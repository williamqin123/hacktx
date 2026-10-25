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

    required_fields = {
        "people",
        "budget",
        "diet",
        "days",
        "dislikes",
        "name",
        "age",
        "sex",
        "height",
        "weight",
        "goal",
        "activity_level",
        "dietary_restrictions",
    }
    missing_fields = sorted(required_fields - data.keys())
    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields,
        }), 400

    people = data["people"]
    budget = data["budget"]
    diet = data["diet"]
    days = data["days"]
    dislikes = data["dislikes"]
    name = data["name"]
    age = data["age"]
    sex = data["sex"]
    height = data["height"]
    weight = data["weight"]
    goal = data["goal"]
    activity_level = data["activity_level"]
    dietary_restrictions = data["dietary_restrictions"]

    if isinstance(people, bool) or not isinstance(people, int) or people < 1:
        return jsonify({"error": "'people' must be a positive integer"}), 400
    if (
        isinstance(budget, bool)
        or not isinstance(budget, (int, float))
        or not math.isfinite(budget)
        or budget < 0
    ):
        return jsonify({"error": "'budget' must be a non-negative number"}), 400
    if not isinstance(diet, str) or not diet.strip():
        return jsonify({"error": "'diet' must be a non-empty string"}), 400
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        return jsonify({"error": "'days' must be a positive integer"}), 400
    if not isinstance(dislikes, str):
        return jsonify({"error": "'dislikes' must be a string"}), 400
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "'name' must be a non-empty string"}), 400
    if isinstance(age, bool) or not isinstance(age, int) or not 1 <= age <= 120:
        return jsonify({"error": "'age' must be an integer from 1 to 120"}), 400
    allowed_sexes = {
        "female",
        "male",
        "intersex",
        "other",
        "prefer_not_to_say",
    }
    if not isinstance(sex, str) or sex not in allowed_sexes:
        return jsonify({"error": "'sex' must be a supported selection"}), 400
    if (
        isinstance(height, bool)
        or not isinstance(height, (int, float))
        or not math.isfinite(height)
        or not 1 <= height <= 300
    ):
        return jsonify({"error": "'height' must be between 1 and 300 cm"}), 400
    if (
        isinstance(weight, bool)
        or not isinstance(weight, (int, float))
        or not math.isfinite(weight)
        or not 1 <= weight <= 700
    ):
        return jsonify({"error": "'weight' must be between 1 and 700 kg"}), 400
    if not isinstance(goal, str) or goal not in {"lose", "maintain", "gain"}:
        return jsonify({"error": "'goal' must be lose, maintain, or gain"}), 400
    allowed_activity_levels = {
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "extra_active",
    }
    if (
        not isinstance(activity_level, str)
        or activity_level not in allowed_activity_levels
    ):
        return jsonify({"error": "'activity_level' must be a supported selection"}), 400
    allowed_restrictions = {
        "Vegetarian",
        "Vegan",
        "Gluten-free",
        "Dairy-free",
        "Nut-free",
        "Pescatarian",
        "Halal",
        "Kosher",
    }
    if (
        not isinstance(dietary_restrictions, list)
        or not all(
            isinstance(restriction, str)
            and restriction in allowed_restrictions
            for restriction in dietary_restrictions
        )
    ):
        return jsonify({
            "error": "'dietary_restrictions' must be a list of supported restrictions"
        }), 400

    from SerpAPI import generate_meal_plan

    try:
        meal_plan = generate_meal_plan(
            people=people,
            budget=budget,
            diet=diet,
            days=days,
            dislikes=dislikes,
            name=name.strip(),
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

    from WalmartAPI import RESULTS_FILE, search_walmart_items

    try:
        walmart_results = search_walmart_items(meal_plan)
    except ValueError as error:
        return jsonify({
            "error": "Could not extract grocery items from the Gemini response",
            "details": str(error),
        }), 502

    return jsonify({
        **meal_plan,
        "walmart_results": walmart_results["walmart_results"],
        "results_file": RESULTS_FILE.name,
    }), 200
