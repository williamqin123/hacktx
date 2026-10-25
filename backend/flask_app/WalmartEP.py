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

    required_fields = {"people", "budget", "diet", "days", "dislikes"}
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

    from SerpAPI import generate_meal_plan

    meal_plan = generate_meal_plan(
        people=people,
        budget=budget,
        diet=diet,
        days=days,
        dislikes=dislikes,
    )
    return jsonify({"meal_plan": meal_plan}), 200
