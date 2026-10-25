"""Authenticated Kroger product search for a user's nearest store."""

import logging
import math
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
#from dotenv import load_dotenv
from firebase_admin import firestore
from flask import Blueprint, jsonify, request

from flask_app.auth import login_required
from kroger_search import (
    fallback_search_term,
    get_kroger_access_token,
    normalize_search_term,
    search_kroger,
)


kroger_bp = Blueprint("kroger", __name__)
KROGER_LOCATIONS_URL = "https://api.kroger.com/v1/locations"
MAX_LOCATION_RESULTS = 10
MAX_SEARCH_ITEMS = 50
MAX_PRODUCT_RESULTS = 10
PICKUP_MATCHES = 3
ZIP_CODE_PATTERN = re.compile(r"^\d{5}(?:-\d{4})?$")


def _api_headers(access_token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def _find_nearest_location(
    session: requests.Session,
    access_token: str,
    zip_code: str,
) -> dict[str, Any] | None:
    response = session.get(
        KROGER_LOCATIONS_URL,
        headers=_api_headers(access_token),
        params={
            "filter.zipCode.near": zip_code,
            "filter.radiusInMiles": 100,
            "filter.limit": MAX_LOCATION_RESULTS,
        },
        timeout=20,
    )
    response.raise_for_status()
    locations = response.json().get("data", [])
    if not isinstance(locations, list):
        raise RuntimeError("Kroger location response did not include a data list")

    matching_locations = [
        location
        for location in locations
        if isinstance(location, dict) and location.get("locationId")
    ]
    if not matching_locations:
        return None

    if all(
        isinstance(location.get("distance"), (int, float))
        for location in matching_locations
    ):
        return min(matching_locations, key=lambda location: location["distance"])
    return matching_locations[0]


def _pickup_product(product: dict[str, Any]) -> dict[str, Any] | None:
    pickup_options = []
    for item in product.get("items", []):
        if not isinstance(item, dict):
            continue
        fulfillment = item.get("fulfillment")
        inventory = item.get("inventory")
        if not isinstance(fulfillment, dict) or fulfillment.get("curbside") is not True:
            continue
        if not isinstance(inventory, dict) or inventory.get("stockLevel") not in {
            "HIGH",
            "LOW",
        }:
            continue

        price_data = item.get("price")
        if not isinstance(price_data, dict):
            continue
        price = price_data.get("promo")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price <= 0:
            price = price_data.get("regular")
        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not math.isfinite(price)
            or price <= 0
        ):
            continue

        pickup_options.append({
            "price": float(price),
            "size": item.get("size", ""),
        })

    if not pickup_options:
        return None

    selected_option = min(pickup_options, key=lambda option: option["price"])
    upc = product.get("upc")
    if not upc:
        upc = product.get("productId")
    if not upc:
        return None

    return {
        "upc": str(upc),
        "description": product.get("description", ""),
        "brand": product.get("brand", ""),
        "price": selected_option["price"],
        "size": selected_option["size"],
        "product_url": (
            f"https://www.kroger.com/p/a/{quote(str(upc))}?fulfillment=PICKUP"
        ),
        "pickup_available": True,
    }


def _search_pickup_products(
    session: requests.Session,
    access_token: str,
    item_name: str,
    location_id: str,
) -> list[dict[str, Any]]:
    term = normalize_search_term(item_name)
    if not term:
        return []

    matches = search_kroger(
        session,
        access_token,
        term,
        location_id,
        limit=MAX_PRODUCT_RESULTS,
    )
    pickup_matches = [
        result
        for product in matches
        if (result := _pickup_product(product)) is not None
    ]
    if not pickup_matches:
        fallback_term = fallback_search_term(term)
        if fallback_term and fallback_term.casefold() != term.casefold():
            matches = search_kroger(
                session,
                access_token,
                fallback_term,
                location_id,
                limit=MAX_PRODUCT_RESULTS,
            )
            pickup_matches = [
                result
                for product in matches
                if (result := _pickup_product(product)) is not None
            ]
    return pickup_matches[:PICKUP_MATCHES]


@kroger_bp.route("/api/kroger/products", methods=["POST"])
@login_required
def get_kroger_products():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    item_names = payload.get("items")
    if (
        not isinstance(item_names, list)
        or not item_names
        or len(item_names) > MAX_SEARCH_ITEMS
        or not all(
            isinstance(item, str) and item.strip() and len(item) <= 200
            for item in item_names
        )
    ):
        return jsonify({
            "error": f"'items' must contain 1 to {MAX_SEARCH_ITEMS} grocery item names"
        }), 400

    try:
        user_id = request.current_user["sub"]
        user_data = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .get()
            .to_dict()
            or {}
        )
        profile = user_data.get("profile", {})
        zip_code = profile.get("zipCode") if isinstance(profile, dict) else None
        if not isinstance(zip_code, str) or not ZIP_CODE_PATTERN.fullmatch(zip_code):
            return jsonify({
                "error": "Add a valid U.S. ZIP code to your profile to find nearby Kroger pickup products."
            }), 400

        #load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        client_id = os.environ.get("KROGER_CLIENT_ID")
        client_secret = os.environ.get("KROGER_API_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError("Kroger API credentials are not configured")

        session = requests.Session()
        access_token = get_kroger_access_token(
            session,
            client_id,
            client_secret,
        )
        location = _find_nearest_location(session, access_token, zip_code)
        if location is None:
            return jsonify({
                "error": f"No Kroger store was found near ZIP code {zip_code}."
            }), 404

        location_id = str(location["locationId"])
        products_by_item: dict[str, list[dict[str, Any]]] = {}
        for item_name in dict.fromkeys(item.strip() for item in item_names):
            products_by_item[item_name] = _search_pickup_products(
                session,
                access_token,
                item_name,
                location_id,
            )

        address = location.get("address", {})
        if not isinstance(address, dict):
            address = {}
        location_summary = {
            "location_id": location_id,
            "name": location.get("name", "Nearest Kroger"),
            "address": ", ".join(
                part
                for part in (
                    address.get("addressLine1"),
                    address.get("city"),
                    address.get("state"),
                    address.get("zipCode"),
                )
                if isinstance(part, str) and part
            ),
            "distance": location.get("distance"),
        }
        return jsonify({
            "location": location_summary,
            "products": products_by_item,
        }), 200
    except requests.RequestException:
        logging.exception("Kroger API request failed")
        return jsonify({"error": "Kroger product search is temporarily unavailable."}), 502
    except Exception:
        logging.exception("Failed to search Kroger products")
        return jsonify({"error": "Failed to load Kroger pickup products."}), 500
