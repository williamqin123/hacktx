"""Kroger customer authorization and shopping-cart integration."""

import json
import hashlib
import logging
import math
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse

import requests
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from firebase_admin import firestore
from flask import Blueprint, jsonify, redirect, request

from flask_app.auth import login_required


kroger_cart_bp = Blueprint("kroger_cart", __name__)
KROGER_AUTHORIZE_URL = "https://api.kroger.com/v1/connect/oauth2/authorize"
KROGER_TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
KROGER_CART_URL = "https://api.kroger.com/v1/cart/add"
KROGER_CART_SCOPE = "cart.basic:write"
KROGER_CART_PAGE = "https://www.kroger.com/cart"
FRONTEND_CART_PAGE = "http://localhost:5173/logged-in-app/shopping-cart"
UPC_PATTERN = re.compile(r"^\d{8,14}$")
UPC_PATH_PATTERN = re.compile(r"/p/a/([^/?]+)")
OAUTH_STATE_LIFETIME = timedelta(minutes=10)


class KrogerConnectionRequired(Exception):
    """Raised when the customer's Kroger authorization must be renewed."""


def _load_kroger_config():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    client_id = os.environ.get("KROGER_CLIENT_ID")
    client_secret = os.environ.get("KROGER_API_SECRET")
    redirect_uri = os.environ.get("KROGER_REDIRECT_URI")
    encryption_key = os.environ.get("KROGER_TOKEN_ENCRYPTION_KEY")
    if not client_id or not client_secret or not redirect_uri or not encryption_key:
        raise RuntimeError(
            "Kroger cart integration requires KROGER_CLIENT_ID, "
            "KROGER_API_SECRET, KROGER_REDIRECT_URI, and "
            "KROGER_TOKEN_ENCRYPTION_KEY"
        )
    try:
        cipher = Fernet(encryption_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError("KROGER_TOKEN_ENCRYPTION_KEY is invalid") from error
    return client_id, client_secret, redirect_uri, cipher


def _integration_ref(user_id):
    return (
        firestore.client()
        .collection("users")
        .document(user_id)
        .collection("integrations")
        .document("kroger")
    )


def _oauth_state_ref(state):
    state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()
    return firestore.client().collection("kroger_oauth_states").document(state_hash)


def _store_tokens(user_id, token_data, cipher):
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")
    if (
        not isinstance(access_token, str)
        or not access_token
        or isinstance(expires_in, bool)
        or not isinstance(expires_in, (int, float))
        or not math.isfinite(expires_in)
        or expires_in <= 0
    ):
        raise ValueError("Kroger returned an invalid access token response")

    stored_tokens = {
        "access_token": access_token,
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": time.time() + expires_in,
    }
    encrypted_tokens = cipher.encrypt(
        json.dumps(stored_tokens).encode("utf-8")
    ).decode("ascii")
    _integration_ref(user_id).set({
        "credentials_encrypted": encrypted_tokens,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })


def _load_tokens(user_id, cipher):
    snapshot = _integration_ref(user_id).get()
    data = snapshot.to_dict() if snapshot.exists else None
    encrypted = data.get("credentials_encrypted") if data else None
    if not isinstance(encrypted, str):
        raise KrogerConnectionRequired(
            "Connect your Kroger account before checking out."
        )
    try:
        tokens = json.loads(cipher.decrypt(encrypted.encode("ascii")))
    except (InvalidToken, UnicodeEncodeError, json.JSONDecodeError) as error:
        logging.exception("Could not decrypt saved Kroger authorization")
        raise RuntimeError("Saved Kroger authorization could not be read") from error
    if not isinstance(tokens, dict):
        raise RuntimeError("Saved Kroger authorization is invalid")
    return tokens


def _get_access_token(user_id, client_id, client_secret, cipher):
    tokens = _load_tokens(user_id, cipher)
    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at")
    if (
        isinstance(access_token, str)
        and isinstance(expires_at, (int, float))
        and not isinstance(expires_at, bool)
        and expires_at > time.time() + 30
    ):
        return access_token

    refresh_token = tokens.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise KrogerConnectionRequired(
            "Your Kroger authorization expired. Connect your Kroger account again."
        )

    try:
        response = requests.post(
            KROGER_TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            auth=(client_id, client_secret),
            timeout=20,
        )
        if response.status_code in {400, 401}:
            _integration_ref(user_id).delete()
            raise KrogerConnectionRequired(
                "Your Kroger authorization expired. Connect your Kroger account again."
            )
        response.raise_for_status()
        refreshed_tokens = response.json()
        if not isinstance(refreshed_tokens, dict):
            raise ValueError("Kroger returned an invalid token response")
        if not refreshed_tokens.get("refresh_token"):
            refreshed_tokens["refresh_token"] = refresh_token
        _store_tokens(user_id, refreshed_tokens, cipher)
    except KrogerConnectionRequired:
        raise
    except (requests.RequestException, ValueError):
        logging.exception("Failed to refresh Kroger authorization")
        raise

    access_token = refreshed_tokens.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("Kroger did not return a refreshed access token")
    return access_token


def _item_upc(item):
    upc = item.get("upc")
    if not isinstance(upc, str):
        product_url = item.get("product_page_url")
        if _is_kroger_product_url(product_url):
            match = UPC_PATH_PATTERN.search(urlparse(product_url).path)
            if match:
                upc = match.group(1)
    if isinstance(upc, str) and UPC_PATTERN.fullmatch(upc):
        return upc
    return None


def _is_kroger_product_url(value):
    if not isinstance(value, str):
        return False
    parsed_url = urlparse(value)
    hostname = parsed_url.hostname.casefold() if parsed_url.hostname else ""
    return (
        (hostname == "kroger.com" or hostname.endswith(".kroger.com"))
        and UPC_PATH_PATTERN.search(parsed_url.path) is not None
    )


def _build_kroger_cart_items(items):
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        retailer = item.get("retailer")
        product_url = item.get("product_page_url")
        is_kroger_item = retailer == "Kroger"
        if not is_kroger_item:
            is_kroger_item = _is_kroger_product_url(product_url)
        if not is_kroger_item:
            continue

        upc = _item_upc(item)
        quantity = item.get("quantity")
        if upc is None:
            raise ValueError("A Kroger cart item is missing a valid UPC")
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or not 1 <= quantity <= 99
        ):
            raise ValueError("A Kroger cart item has an invalid quantity")
        quantities[upc] = quantities.get(upc, 0) + quantity

    if not quantities:
        raise ValueError("Your app cart does not contain any Kroger products")
    return [
        {"upc": upc, "quantity": quantity, "modality": "PICKUP"}
        for upc, quantity in quantities.items()
    ]


def _add_user_cart_to_kroger(user_id, client_id, client_secret, cipher):
    cart_snapshot = (
        firestore.client()
        .collection("users")
        .document(user_id)
        .collection("cart")
        .document("current")
        .get()
    )
    cart_data = cart_snapshot.to_dict() if cart_snapshot.exists else {}
    items = cart_data.get("items", []) if isinstance(cart_data, dict) else []
    if not isinstance(items, list):
        raise ValueError("Your app cart is invalid")
    kroger_items = _build_kroger_cart_items(items)
    access_token = _get_access_token(
        user_id,
        client_id,
        client_secret,
        cipher,
    )
    response = requests.put(
        KROGER_CART_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"items": kroger_items},
        timeout=20,
    )
    if response.status_code in {401, 403}:
        _integration_ref(user_id).delete()
        raise KrogerConnectionRequired(
            "Kroger could not authorize this cart request. Connect your account again."
        )
    response.raise_for_status()
    return len(kroger_items)


def _frontend_cart_redirect(status):
    return redirect(f"{FRONTEND_CART_PAGE}?kroger={status}")


@kroger_cart_bp.route("/api/kroger/connection", methods=["GET"])
@login_required
def get_kroger_connection():
    try:
        connected = _integration_ref(request.current_user["sub"]).get().exists
        return jsonify({"connected": connected}), 200
    except Exception:
        logging.exception("Failed to load Kroger connection status")
        return jsonify({"error": "Could not check your Kroger connection"}), 500


@kroger_cart_bp.route("/api/kroger/connect", methods=["GET"])
@login_required
def connect_kroger():
    try:
        client_id, _, redirect_uri, _ = _load_kroger_config()
        state = secrets.token_urlsafe(32)
        _oauth_state_ref(state).set({
            "user_id": request.current_user["sub"],
            "checkout": request.args.get("checkout") == "1",
            "expires_at": datetime.now(timezone.utc) + OAUTH_STATE_LIFETIME,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })
        authorization_params = {
            'scope': KROGER_CART_SCOPE,
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        authorization_url = (
            f"{KROGER_AUTHORIZE_URL}?{urlencode(authorization_params)}"
        )
        return redirect(authorization_url)
    except Exception as error:
        logging.exception("Failed to start Kroger authorization")
        return jsonify({"error": str(error)}), 500


@kroger_cart_bp.route("/api/kroger/oauth/callback", methods=["GET"])
def kroger_oauth_callback():
    state = request.args.get("state")
    if not isinstance(state, str) or not state:
        return _frontend_cart_redirect("state_error")

    try:
        state_ref = _oauth_state_ref(state)
        state_snapshot = state_ref.get()
        oauth_data = state_snapshot.to_dict() if state_snapshot.exists else None
        state_ref.delete()
        expires_at = oauth_data.get("expires_at") if oauth_data else None
        if (
            not isinstance(oauth_data, dict)
            or not isinstance(oauth_data.get("user_id"), str)
            or not isinstance(expires_at, datetime)
            or expires_at <= datetime.now(timezone.utc)
        ):
            return _frontend_cart_redirect("state_error")
        if request.args.get("error"):
            return _frontend_cart_redirect("authorization_denied")
        if not request.args.get("code"):
            return _frontend_cart_redirect("authorization_error")

        client_id, client_secret, redirect_uri, cipher = _load_kroger_config()
        response = requests.post(
            KROGER_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": request.args["code"],
                "redirect_uri": redirect_uri,
            },
            auth=(client_id, client_secret),
            timeout=20,
        )
        response.raise_for_status()
        token_data = response.json()
        if not isinstance(token_data, dict):
            raise ValueError("Kroger returned an invalid token response")
        _store_tokens(oauth_data["user_id"], token_data, cipher)

        if oauth_data.get("checkout"):
            _add_user_cart_to_kroger(
                oauth_data["user_id"],
                client_id,
                client_secret,
                cipher,
            )
            return redirect(KROGER_CART_PAGE)
        return _frontend_cart_redirect("connected")
    except Exception:
        logging.exception("Kroger authorization callback failed")
        return _frontend_cart_redirect("checkout_error")


@kroger_cart_bp.route("/api/kroger/cart", methods=["POST"])
@login_required
def add_to_kroger_cart():
    try:
        client_id, client_secret, _, cipher = _load_kroger_config()
        item_count = _add_user_cart_to_kroger(
            request.current_user["sub"],
            client_id,
            client_secret,
            cipher,
        )
        return jsonify({"added_count": item_count}), 200
    except KrogerConnectionRequired as error:
        return jsonify({"error": str(error)}), 409
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        logging.exception("Failed to add products to Kroger cart")
        return jsonify({"error": "Could not add products to your Kroger cart"}), 502
