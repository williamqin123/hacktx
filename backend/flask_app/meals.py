import logging
import math

from flask import Blueprint, jsonify, request


walmart_bp = Blueprint("walmart", __name__)


@walmart_bp.route("/api/meal-plan", methods=["POST"])
def create_meal_plan():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    from .main import validate_user_info_json
    try:
        validate_user_info_json(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    required_fields = {
        "diet",
        "days",
        "people",
    }
    missing_fields = sorted(required_fields - data.keys())
    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields,
        }), 400

    people = data["people"]
    # budget = data["budget"]
    diet = data["diet"]
    days = data["days"]
    dislikes = data["dislikes"]
    # name = data["name"]
    age = data["age"]
    sex = data["sex"]
    height = data["height"]
    weight = data["weight"]
    goal = data["goal"]
    activity_level = data["activityLevel"]
    dietary_restrictions = data["dietaryRestrictions"]

    if isinstance(people, bool) or not isinstance(people, int) or people < 1:
        raise ValueError("'people' must be a positive integer")

    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise ValueError("'days' must be a positive integer")


    from SerpAPI import generate_meal_plan

    try:
        meal_plan = generate_meal_plan(
            people=people,
            #budget=budget,
            diet=diet,
            days=days,
            dislikes=dislikes,
            #name=name.strip(),
            age=age,
            sex=sex,
            height=height,
            weight=weight,
            goal=goal,
            activity_level=activity_level,
            dietary_restrictions=dietary_restrictions,
        )
    except ValueError as error:
        return jsonify({
            "error": "Gemini did not return the required meal-plan JSON",
            "details": str(error),
        }), 502

    from .recipe_catalog import store_recipes

    try:
        saved_recipes = store_recipes(meal_plan)
    except ValueError as error:
        return jsonify({
            "error": "Generated meal plan could not be saved as recipes",
            "details": str(error),
        }), 502
    except Exception:
        logging.exception("Failed to save generated recipes")
        return jsonify({"error": "Failed to save generated recipes"}), 500

    return jsonify({**meal_plan, "recipes": saved_recipes}), 200

from WalmartAPI import search_walmart_items

@walmart_bp.route("/api/walmart-search", methods=["POST"])
def get_walmart_results():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    items = data["items"]

    try:
        walmart_results = search_walmart_items(items)
    except ValueError as error:
        return jsonify({
            "error": "Could not extract grocery items from the Gemini response",
            "details": str(error),
        }), 502

    return jsonify(walmart_results["walmart_results"]), 200