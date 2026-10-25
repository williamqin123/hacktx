"""Search Kroger for grocery items saved in Firestore."""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app


KROGER_TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
KROGER_PRODUCTS_URL = "https://api.kroger.com/v1/products"
KROGER_SCOPE = "product.compact"
REQUEST_TIMEOUT_SECONDS = 20
MAX_MATCHES = 3
MEASUREMENT_UNITS = re.compile(
    r"\b(?:"
    r"cups?|c|"
    r"fluid\s+ounces?|fl\.?\s*oz\.?|"
    r"ounces?|oz\.?|"
    r"pounds?|lbs?\.?|"
    r"kilograms?|kgs?\.?|"
    r"grams?|g|"
    r"milligrams?|mgs?\.?|"
    r"liters?|litres?|l|"
    r"milliliters?|millilitres?|ml|"
    r"gallons?|quarts?|pints?|"
    r"tablespoons?|tbsp\.?|tbs\.?|"
    r"teaspoons?|tsp\.?|"
    r"pinches?|dashes?|"
    r"bunch(?:es)?|cloves?|scoops?|heads?|stalks?|sprigs?|"
    r"cans?|packages?|packets?|"
    r"sticks?|slices?|pieces?"
    r")\b",
    re.IGNORECASE,
)
ATTACHED_MEASUREMENT_UNITS = re.compile(
    r"(?<=\d)(?:"
    r"fluidounces?|floz|"
    r"ounces?|oz|"
    r"pounds?|lbs?|"
    r"kilograms?|kgs?|"
    r"grams?|g|"
    r"milligrams?|mgs?|"
    r"milliliters?|millilitres?|ml|"
    r")\b",
    re.IGNORECASE,
)
QUANTITY_NUMBERS = re.compile(
    r"(?<!\w)(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)(?!\w)"
)
QUANTITY_WORDS = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"half|quarter|third)\b",
    re.IGNORECASE,
)
SEARCH_QUALIFIERS = {"cooked", "dry", "roasted", "large", "small", "medium", "cubed", "cubes"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def initialize_firestore() -> Any:
    """Initialize Firebase Admin from the configured service-account JSON."""
    load_dotenv(Path(__file__).with_name(".env"))
    try:
        from firebase_admin import get_app

        return get_app()
    except ValueError:
        credentials_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if not credentials_json:
            raise RuntimeError("FIREBASE_CREDENTIALS_JSON is not set")
        try:
            credentials_data = json.loads(credentials_json)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "FIREBASE_CREDENTIALS_JSON is not valid JSON"
            ) from error
        return initialize_app(credentials.Certificate(credentials_data))


def get_kroger_access_token(
    session: requests.Session,
    client_id: str,
    client_secret: str,
    scope: str = KROGER_SCOPE,
) -> str:
    """Request an OAuth client-credentials token for product search."""
    response = session.post(
        KROGER_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "scope": scope,
        },
        auth=(client_id, client_secret),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Kroger token response did not include access_token")
    return token


def search_kroger(
    session: requests.Session,
    access_token: str,
    term: str,
    location_id: str | None = None,
    limit: int = MAX_MATCHES,
) -> list[dict[str, Any]]:
    """Return Kroger API-ranked products, including UPC strings."""
    params: dict[str, str | int] = {
        "filter.term": term,
        "filter.limit": limit,
    }
    if location_id:
        params["filter.locationId"] = location_id

    response = session.get(
        KROGER_PRODUCTS_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    products = response.json().get("data", [])
    if not isinstance(products, list):
        raise RuntimeError("Kroger product response did not include a data list")

    matches = []
    for product in products[:limit]:
        if not isinstance(product, dict):
            continue
        upc = product.get("productId")
        if upc is None:
            continue
        matches.append({
            "upc": str(upc),
            "description": product.get("description", ""),
            "brand": product.get("brand", ""),
            "items": product.get("items", []),
        })
    return matches


def normalize_search_term(value: str) -> str:
    """Remove numeric quantities and common units from a grocery item name."""
    fractions = {
        "½": " 1/2 ",
        "⅓": " 1/3 ",
        "⅔": " 2/3 ",
        "¼": " 1/4 ",
        "¾": " 3/4 ",
        "⅛": " 1/8 ",
        "⅜": " 3/8 ",
        "⅝": " 5/8 ",
        "⅞": " 7/8 ",
    }
    for fraction, replacement in fractions.items():
        value = value.replace(fraction, replacement)

    value = ATTACHED_MEASUREMENT_UNITS.sub(" ", value)
    value = MEASUREMENT_UNITS.sub(" ", value)
    value = QUANTITY_NUMBERS.sub(" ", value)
    value = QUANTITY_WORDS.sub(" ", value)
    value = re.sub(r"[\[\]{}(),/]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -,:;.")
    value = re.sub(r"^(?:of|the)\s+", "", value, flags=re.IGNORECASE)
    return value.strip()


def fallback_search_term(value: str) -> str:
    """Remove common preparation and size descriptors for a no-results retry."""
    words = [
        word
        for word in value.split()
        if word.casefold() not in SEARCH_QUALIFIERS
    ]
    return " ".join(words)


def _item_name(item: Any) -> str | None:
    if isinstance(item, str) and item.strip():
        return item.strip()
    if isinstance(item, dict):
        for key in ("item", "ingredient", "name", "product", "title"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _items_in_document(collection_name: str, data: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if collection_name == "meal_plans":
        grocery_list = data.get("grocery_list", [])
        if isinstance(grocery_list, list):
            items.extend(
                name
                for name in (_item_name(item) for item in grocery_list)
                if name
            )
    else:
        ingredients = data.get("ingredients", [])
        if isinstance(ingredients, list):
            items.extend(
                name
                for name in (_item_name(item) for item in ingredients)
                if name
            )

    shopping_list = data.get("shopping_list", [])
    if isinstance(shopping_list, list):
        items.extend(
            name
            for name in (_item_name(item) for item in shopping_list)
            if name
        )

    return list(dict.fromkeys(items))


def _update_user_documents(
    db: Any,
    user_ref: Any,
    collection_name: str,
    token: str,
    location_id: str | None,
    dry_run: bool,
    cache: dict[str, list[dict[str, Any]]],
    session: requests.Session,
) -> tuple[int, int]:
    updated = 0
    searched = 0
    for snapshot in user_ref.collection(collection_name).stream():
        document_data = snapshot.to_dict() or {}
        item_names = _items_in_document(collection_name, document_data)
        if not item_names:
            continue

        results: dict[str, list[dict[str, Any]]] = {}
        for item_name in item_names:
            search_term = normalize_search_term(item_name)
            if not search_term:
                logging.warning("Skipping item that is empty after normalization: %s", item_name)
                continue
            cache_key = search_term.casefold()
            if cache_key not in cache:
                cache[cache_key] = search_kroger(
                    session,
                    token,
                    search_term,
                    location_id,
                )
                searched += 1
                if not cache[cache_key]:
                    fallback_term = fallback_search_term(search_term)
                    fallback_key = fallback_term.casefold()
                    if fallback_term and fallback_key != cache_key:
                        if fallback_key not in cache:
                            cache[fallback_key] = search_kroger(
                                session,
                                token,
                                fallback_term,
                                location_id,
                            )
                            searched += 1
                        cache[cache_key] = cache[fallback_key]
                        if cache[cache_key]:
                            logging.info(
                                "Using fallback search %s for %s",
                                fallback_term,
                                item_name,
                            )
                logging.info(
                    "Found %d Kroger matches for %s (searched as %s)",
                    len(cache[cache_key]),
                    item_name,
                    search_term,
                )
            results[item_name] = cache[cache_key]

        if results and not dry_run:
            db.collection("users").document(user_ref.id).collection(
                collection_name
            ).document(snapshot.id).update({"kroger_results": results})
            updated += 1

    return updated, searched


def run_search(
    user_id: str | None = None,
    dry_run: bool = False,
    output_path: Path | None = None,
) -> None:
    """Search item lists in user meal plans, recipes, and saved meals."""
    load_dotenv(Path(__file__).with_name(".env"))
    client_id = os.environ.get("KROGER_CLIENT_ID")
    client_secret = os.environ.get("KROGER_API_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set KROGER_CLIENT_ID and KROGER_API_SECRET in backend/.env"
        )

    initialize_firestore()
    db = firestore.client()
    session = requests.Session()
    token = get_kroger_access_token(session, client_id, client_secret)
    location_id = os.environ.get("KROGER_LOCATION_ID")

    users = (
        [db.collection("users").document(user_id)]
        if user_id
        else list(db.collection("users").stream())
    )
    cache: dict[str, list[dict[str, Any]]] = {}
    export_items: dict[str, dict[str, Any]] = {}
    total_updated = 0
    total_searched = 0
    for user_snapshot in users:
        user_ref = db.collection("users").document(user_snapshot.id)
        for collection_name in ("meal_plans", "recipes", "saved_meals"):
            for snapshot in user_ref.collection(collection_name).stream():
                document_data = snapshot.to_dict() or {}
                for item_name in _items_in_document(collection_name, document_data):
                    search_term = normalize_search_term(item_name)
                    if not search_term:
                        logging.warning(
                            "Skipping item that is empty after normalization: %s",
                            item_name,
                        )
                        continue
                    export_items.setdefault(
                        search_term.casefold(),
                        {"item": search_term, "upcs": []},
                    )

            updated, searched = _update_user_documents(
                db,
                user_ref,
                collection_name,
                token,
                location_id,
                dry_run,
                cache,
                session,
            )
            total_updated += updated
            total_searched += searched

    for exported in export_items.values():
        matches = cache.get(exported["item"].casefold(), [])
        exported["upcs"] = [match["upc"] for match in matches]

    destination = output_path or Path(__file__).with_name("kroger_upcs.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps({"items": list(export_items.values())}, indent=2) + "\n",
        encoding="utf-8",
    )

    logging.info(
        "%s: searched %d unique item(s); updated %d document(s); wrote %s",
        "Dry run complete" if dry_run else "Kroger search complete",
        total_searched,
        total_updated,
        destination,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Search Kroger for grocery items in Firestore and save up to "
            "three UPC matches per item."
        )
    )
    parser.add_argument(
        "--user-id",
        help="Only process this Firestore users/{user-id} document",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and report matches without writing to Firestore",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("kroger_upcs.json"),
        help="Path for the JSON export (default: backend/kroger_upcs.json)",
    )
    args = parser.parse_args()
    run_search(
        user_id=args.user_id,
        dry_run=args.dry_run,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
