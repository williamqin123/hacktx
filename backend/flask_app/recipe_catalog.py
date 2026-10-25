import logging

from firebase_admin import firestore
from flask import Blueprint, jsonify, request


recipe_bp = Blueprint("recipes", __name__)
MEAL_TYPES = {"breakfast", "lunch", "dinner"}


def _extract_recipes(data):
    meal_plan = data.get("meal_plan", data)
    if not isinstance(meal_plan, dict):
        raise ValueError("'meal_plan' must be a JSON object")

    daily_meals = meal_plan.get("daily_meals")
    if not isinstance(daily_meals, list):
        raise ValueError("'daily_meals' must be a list")

    recipes = []
    for day_entry in daily_meals:
        if not isinstance(day_entry, dict):
            raise ValueError("Each daily meal entry must be an object")

        meals = day_entry.get("meals")
        if not isinstance(meals, dict):
            raise ValueError("Each daily meal entry must contain a 'meals' object")

        day = day_entry.get("day")
        for meal_type, meal in meals.items():
            if meal_type not in MEAL_TYPES:
                continue
            if not isinstance(meal, dict):
                raise ValueError(f"'{meal_type}' must be a recipe object")

            name = meal.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"'{meal_type}.name' must be a non-empty string")

            calories = meal.get("estimated_calories_kcal_per_person")
            if isinstance(calories, bool) or not isinstance(calories, int):
                raise ValueError(
                    f"'{meal_type}.estimated_calories_kcal_per_person' "
                    "must be an integer"
                )

            ingredients = meal.get("ingredients")
            if not isinstance(ingredients, list) or not ingredients or not all(
                isinstance(ingredient, str) and ingredient.strip()
                for ingredient in ingredients
            ):
                raise ValueError(f"'{meal_type}.ingredients' must be a list of strings")

            prep_time = meal.get("prep_time")
            if isinstance(prep_time, bool) or not isinstance(prep_time, int):
                raise ValueError(f"'{meal_type}.prep_time' must be an integer")

            instructions = meal.get("Recipe")
            if not isinstance(instructions, list) or not instructions or not all(
                isinstance(step, str) and step.strip() for step in instructions
            ):
                raise ValueError(f"'{meal_type}.Recipe' must be a list of strings")

            recipe = {
                "meal_type": meal_type,
                "name": name.strip(),
                "estimated_calories_kcal_per_person": calories,
                "ingredients": ingredients,
                "prep_time": prep_time,
                "Recipe": instructions,
            }
            if isinstance(day, int) and not isinstance(day, bool):
                recipe["day"] = day
            recipes.append(recipe)

    if not recipes:
        raise ValueError("No breakfast, lunch, or dinner recipes were found")

    return recipes


def store_recipes(data):
    recipes = _extract_recipes(data)
    db = firestore.client()
    collection = db.collection("recipes")
    stored_recipes = []

    for start in range(0, len(recipes), 500):
        batch = db.batch()
        batch_recipes = recipes[start:start + 500]
        batch_documents = []
        for recipe in batch_recipes:
            document = collection.document()
            batch.set(document, {
                **recipe,
                "createdAt": firestore.SERVER_TIMESTAMP,
            })
            batch_documents.append({"id": document.id, **recipe})
        batch.commit()
        stored_recipes.extend(batch_documents)

    return stored_recipes


@recipe_bp.route("/api/recipes", methods=["GET"])
def get_recipes():
    try:
        db = firestore.client()
        snapshots = db.collection("recipes").stream()
        recipes = [
            {"id": snapshot.id, **snapshot.to_dict()}
            for snapshot in snapshots
        ]
        return jsonify({"recipes": recipes}), 200
    except Exception:
        logging.exception("Failed to load recipes")
        return jsonify({"error": "Failed to load recipes"}), 500


@recipe_bp.route("/api/recipes", methods=["POST"])
def save_recipes():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    try:
        stored_recipes = store_recipes(data)
        return jsonify({"recipes": stored_recipes}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        logging.exception("Failed to save recipes")
        return jsonify({"error": "Failed to save recipes"}), 500