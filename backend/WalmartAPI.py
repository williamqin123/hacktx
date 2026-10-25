import json
import os
from pathlib import Path

import serpapi
from dotenv import load_dotenv

load_dotenv()

RESULTS_FILE = Path(__file__).resolve().with_name("walmart_search_results.json")
STORE_ID = 3569


def _normalize_items(items):
    if not isinstance(items, list):
        raise ValueError('Gemini "items" must be a list')

    normalized = []
    for item in items:
        if isinstance(item, str) and item.strip():
            normalized.append({"item": item.strip(), "quantity": ""})
            continue

        if isinstance(item, dict):
            name = next(
                (
                    item[key]
                    for key in ("name", "item", "ingredient", "product", "title")
                    if isinstance(item.get(key), str) and item[key].strip()
                ),
                None,
            )
            if name:
                quantity = item.get("quantity")
                normalized.append({
                    "item": name.strip(),
                    "quantity": (
                        quantity.strip()
                        if isinstance(quantity, str)
                        else str(quantity) if quantity is not None else ""
                    ),
                })
                continue

        raise ValueError(
            'Each Gemini item must be a non-empty string or an object with an item name'
        )

    return normalized


def _parse_items(value):
    if isinstance(value, dict):
        if "grocery_list" in value:
            return _normalize_items(value["grocery_list"])
        if "items" in value:
            return _normalize_items(value["items"])

        preferred_keys = (
            "text",
            "answer",
            "response",
            "content",
            "output",
            "result",
            "results",
            "gemini_results",
            "grocery_list",
            "items",
        )
        ordered_values = [
            value[key] for key in preferred_keys if key in value
        ] + [
            nested_value
            for key, nested_value in value.items()
            if key not in preferred_keys
        ]
        for nested_value in ordered_values:
            try:
                return _parse_items(nested_value)
            except ValueError:
                continue

    if isinstance(value, str):
        text = value.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3].strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
            decoder = json.JSONDecoder()
            for index, character in enumerate(text):
                if character not in "{[":
                    continue
                try:
                    parsed, _ = decoder.raw_decode(text[index:])
                    break
                except json.JSONDecodeError:
                    continue
            if parsed is None:
                raise ValueError(
                    'Gemini response was text and did not contain JSON with an "items" list'
                )
        return _parse_items(parsed)

    if isinstance(value, list):
        for entry in value:
            try:
                return _parse_items(entry)
            except ValueError:
                continue

    raise ValueError('Gemini response did not contain an "items" list')


def search_walmart_items(meal_plan_response):
    items = _parse_items(meal_plan_response)
    unique_items = {}
    for entry in items:
        item_name = entry["item"].strip()
        quantity = entry["quantity"].strip()
        display_name = (
            f"{quantity} {item_name}"
            if quantity and item_name.casefold() not in quantity.casefold()
            else quantity or item_name
        )
        unique_items.setdefault(display_name, item_name)

    if not unique_items:
        raise ValueError("Gemini returned an empty grocery item list")

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY is not set")

    client = serpapi.Client(api_key=api_key)
    results_by_item = {}
    for display_name, item_name in unique_items.items():
        result = client.search({
            "engine": "walmart",
            "query": item_name,
            "store_id": STORE_ID,
            "spelling": "true",
            "json_restrictor": (
                "organic_results[0:3].{product_id, title, "
                "primary_offer.offer_price, product_page_url}"
            ),
        })
        if hasattr(result, "as_dict"):
            result = result.as_dict()
        if isinstance(result, dict) and not result.get("organic_results"):
            result = {
                "query": item_name,
                "status": "no_results",
                "organic_results": [],
            }
        results_by_item[display_name] = result

    if not isinstance(meal_plan_response, dict):
        raise ValueError("Gemini response must be a JSON object")

    combined_results = {
        "meal_plan": meal_plan_response.get("meal_plan"),
        "grocery_list": meal_plan_response.get("grocery_list"),
        "walmart_results": results_by_item,
    }
    with RESULTS_FILE.open("w", encoding="utf-8") as output_file:
        json.dump(combined_results, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    return combined_results
