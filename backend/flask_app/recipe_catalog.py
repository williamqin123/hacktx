import copy
import logging
import math

from firebase_admin import firestore
from flask import Blueprint, jsonify, request

from .auth import login_required


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


def _normalize_ingredient(value):
    return "".join(character for character in value.casefold() if character.isalnum())


def _shopping_items_for_recipe(recipe, grocery_list, walmart_results):
    shopping_items = []
    for ingredient in recipe["ingredients"]:
        normalized_ingredient = _normalize_ingredient(ingredient)
        grocery_item = next(
            (
                item
                for item in grocery_list
                if isinstance(item, dict)
                and isinstance(item.get("item"), str)
                and (
                    _normalize_ingredient(item["item"]) in normalized_ingredient
                    or normalized_ingredient in _normalize_ingredient(item["item"])
                )
            ),
            None,
        )

        if grocery_item is None:
            shopping_items.append({
                "ingredient": ingredient,
                "quantity": "",
                "products": [],
            })
            continue

        item_name = grocery_item["item"].strip()
        quantity = grocery_item.get("quantity", "")
        if not isinstance(quantity, str):
            quantity = str(quantity) if quantity is not None else ""
        display_name = (
            f"{quantity.strip()} {item_name}"
            if quantity.strip()
            and item_name.casefold() not in quantity.casefold()
            else quantity.strip() or item_name
        )
        search_result = walmart_results.get(display_name, {})
        products = search_result.get("organic_results", [])
        shopping_items.append({
            "ingredient": ingredient,
            "quantity": quantity,
            "products": products if isinstance(products, list) else [],
        })

    return shopping_items


def store_recipes(data, user_id, walmart_results=None):
    meal_plan = data.get("meal_plan", data)
    if not isinstance(meal_plan, dict):
        raise ValueError("'meal_plan' must be a JSON object")

    recipes = _extract_recipes(data)
    grocery_list = data.get("grocery_list", [])
    if not isinstance(grocery_list, list):
        raise ValueError("'grocery_list' must be a list")
    walmart_results = walmart_results or {}

    grouped_plan = copy.deepcopy(meal_plan)
    recipes_by_day_and_type = {
        (recipe.get("day"), recipe["meal_type"]): recipe
        for recipe in recipes
    }
    for day_entry in grouped_plan["daily_meals"]:
        day = day_entry.get("day")
        for meal_type, meal in day_entry["meals"].items():
            recipe = recipes_by_day_and_type.get((day, meal_type))
            if recipe:
                meal["shopping_list"] = _shopping_items_for_recipe(
                    recipe,
                    grocery_list,
                    walmart_results,
                )

    saved_plan = {
        "meal_plan": grouped_plan,
        "grocery_list": grocery_list,
        "walmart_results": walmart_results,
    }
    db = firestore.client()
    user_ref = db.collection("users").document(user_id)
    document = user_ref.collection("meal_plans").document()
    batch = db.batch()
    batch.set(document, {
        **saved_plan,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    saved_recipe_refs = []
    for recipe in recipes:
        recipe_ref = user_ref.collection("recipes").document()
        batch.set(recipe_ref, {
            **recipe,
            "shopping_list": _shopping_items_for_recipe(
                recipe,
                grocery_list,
                walmart_results,
            ),
            "meal_plan_id": document.id,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })
        saved_recipe_refs.append(recipe_ref.id)
    batch.commit()
    return {"id": document.id, **saved_plan, "recipe_ids": saved_recipe_refs}


@recipe_bp.route("/api/meal-plans", methods=["GET"])
@login_required
def get_meal_plans():
    try:
        user_id = request.current_user["sub"]
        snapshots = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .collection("meal_plans")
            .stream()
        )
        meal_plans = [
            {"id": snapshot.id, **snapshot.to_dict()}
            for snapshot in snapshots
        ]
        return jsonify({"meal_plans": meal_plans}), 200
    except Exception:
        logging.exception("Failed to load meal plans")
        return jsonify({"error": "Failed to load meal plans"}), 500


@recipe_bp.route("/api/meal-plans/<meal_plan_id>", methods=["DELETE"])
@login_required
def delete_meal_plan(meal_plan_id):
    try:
        user_id = request.current_user["sub"]
        db = firestore.client()
        user_ref = db.collection("users").document(user_id)
        meal_plan_ref = user_ref.collection("meal_plans").document(meal_plan_id)
        if not meal_plan_ref.get().exists:
            return jsonify({"error": "Meal plan not found"}), 404

        recipes = list(
            user_ref.collection("recipes")
            .where("meal_plan_id", "==", meal_plan_id)
            .stream()
        )
        batch = db.batch()
        batch.delete(meal_plan_ref)
        writes = 1
        for recipe in recipes:
            if writes == 500:
                batch.commit()
                batch = db.batch()
                writes = 0
            batch.delete(recipe.reference)
            writes += 1
        batch.commit()
        return jsonify({"message": "Meal plan deleted"}), 200
    except Exception:
        logging.exception("Failed to delete meal plan")
        return jsonify({"error": "Failed to delete meal plan"}), 500


@recipe_bp.route("/api/recipes", methods=["GET"])
@login_required
def get_recipes():
    try:
        user_id = request.current_user["sub"]
        db = firestore.client()
        snapshots = (
            db.collection("users")
            .document(user_id)
            .collection("recipes")
            .stream()
        )
        recipes = [
            {"id": snapshot.id, **snapshot.to_dict()}
            for snapshot in snapshots
        ]
        return jsonify({"recipes": recipes}), 200
    except Exception:
        logging.exception("Failed to load recipes")
        return jsonify({"error": "Failed to load recipes"}), 500


@recipe_bp.route("/api/recipes", methods=["POST"])
@login_required
def save_recipes():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    try:
        stored_recipes = store_recipes(
            data,
            user_id=request.current_user["sub"],
        )
        return jsonify({"recipes": stored_recipes}), 201
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        logging.exception("Failed to save recipes")
        return jsonify({"error": "Failed to save recipes"}), 500


@recipe_bp.route("/api/saved-meals", methods=["GET"])
@login_required
def get_saved_meals():
    try:
        user_id = request.current_user["sub"]
        snapshots = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .collection("saved_meals")
            .stream()
        )
        saved_meals = [
            {"id": snapshot.id, **snapshot.to_dict()}
            for snapshot in snapshots
        ]
        return jsonify({"saved_meals": saved_meals}), 200
    except Exception:
        logging.exception("Failed to load saved meals")
        return jsonify({"error": "Failed to load saved meals"}), 500


@recipe_bp.route("/api/saved-meals", methods=["POST"])
@login_required
def save_meal():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    meal = data.get("meal")
    source_plan_id = data.get("source_meal_plan_id")
    meal_type = data.get("meal_type")
    day = data.get("day")
    if (
        not isinstance(meal, dict)
        or not isinstance(meal.get("name"), str)
        or not meal["name"].strip()
    ):
        return jsonify({"error": "A meal with a name is required"}), 400
    if not isinstance(source_plan_id, str) or not source_plan_id:
        return jsonify({"error": "source_meal_plan_id is required"}), 400
    if not isinstance(meal_type, str) or meal_type not in MEAL_TYPES:
        return jsonify({"error": "meal_type must be breakfast, lunch, or dinner"}), 400
    if isinstance(day, bool) or not isinstance(day, int) or day < 1:
        return jsonify({"error": "day must be a positive integer"}), 400
    ingredients = meal.get("ingredients")
    shopping_list = meal.get("shopping_list", [])
    instructions = meal.get("Recipe", [])
    if not isinstance(ingredients, list) or not all(
        isinstance(ingredient, str) for ingredient in ingredients
    ):
        return jsonify({"error": "meal.ingredients must be a list of strings"}), 400
    if not isinstance(shopping_list, list) or not all(
        isinstance(line, dict)
        and isinstance(line.get("ingredient"), str)
        and isinstance(line.get("products", []), list)
        for line in shopping_list
    ):
        return jsonify({"error": "meal.shopping_list must contain valid ingredients"}), 400
    if not (
        isinstance(instructions, str)
        or isinstance(instructions, list)
        and all(isinstance(step, str) for step in instructions)
    ):
        return jsonify({"error": "meal.Recipe must be a string or list of strings"}), 400

    try:
        user_id = request.current_user["sub"]
        user_ref = firestore.client().collection("users").document(user_id)
        saved_meals_ref = user_ref.collection("saved_meals")
        duplicate = (
            saved_meals_ref
            .where("source_meal_plan_id", "==", source_plan_id)
            .where("day", "==", day)
            .where("meal_type", "==", meal_type)
            .limit(1)
            .stream()
        )
        duplicate = next(iter(duplicate), None)
        if duplicate:
            return jsonify({
                "error": "This meal is already saved",
                "saved_meal": {"id": duplicate.id, **duplicate.to_dict()},
            }), 409

        saved_meal = {
            "name": meal["name"].strip(),
            "estimated_calories_kcal_per_person": meal.get(
                "estimated_calories_kcal_per_person"
            ),
            "ingredients": ingredients,
            "prep_time": meal.get("prep_time"),
            "Recipe": instructions,
            "shopping_list": shopping_list,
            "meal_type": meal_type,
            "day": day,
            "source_meal_plan_id": source_plan_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
        document = saved_meals_ref.document()
        document.set(saved_meal)
        response_meal = {key: value for key, value in saved_meal.items() if key != "createdAt"}
        return jsonify({"saved_meal": {"id": document.id, **response_meal}}), 201
    except Exception:
        logging.exception("Failed to save meal")
        return jsonify({"error": "Failed to save meal"}), 500


@recipe_bp.route("/api/saved-meals/<saved_meal_id>", methods=["DELETE"])
@login_required
def delete_saved_meal(saved_meal_id):
    try:
        user_id = request.current_user["sub"]
        document = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .collection("saved_meals")
            .document(saved_meal_id)
        )
        if not document.get().exists:
            return jsonify({"error": "Saved meal not found"}), 404
        document.delete()
        return jsonify({"message": "Saved meal deleted"}), 200
    except Exception:
        logging.exception("Failed to delete saved meal")
        return jsonify({"error": "Failed to delete saved meal"}), 500


@recipe_bp.route("/api/cart", methods=["GET"])
@login_required
def get_cart():
    try:
        user_id = request.current_user["sub"]
        cart_ref = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .collection("cart")
            .document("current")
        )
        snapshot = cart_ref.get()
        items = snapshot.to_dict().get("items", []) if snapshot.exists else []
        return jsonify({"items": items}), 200
    except Exception:
        logging.exception("Failed to load shopping cart")
        return jsonify({"error": "Failed to load shopping cart"}), 500


@recipe_bp.route("/api/cart", methods=["PUT"])
@login_required
def update_cart():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return jsonify({"error": "'items' must be a list"}), 400

    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("title"), str)
            or not isinstance(item.get("meal_name"), str)
            or not isinstance(item.get("ingredient"), str)
            or isinstance(item.get("quantity"), bool)
            or not isinstance(item.get("quantity"), int)
            or not 1 <= item["quantity"] <= 99
        ):
            return jsonify({"error": "Cart items must include valid product and quantity data"}), 400
        price = item.get("price")
        if price is not None and (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or not math.isfinite(price)
            or price < 0
        ):
            return jsonify({"error": "Cart item prices must be non-negative numbers"}), 400

    try:
        user_id = request.current_user["sub"]
        cart_ref = (
            firestore.client()
            .collection("users")
            .document(user_id)
            .collection("cart")
            .document("current")
        )
        cart_ref.set({"items": items, "updatedAt": firestore.SERVER_TIMESTAMP})
        return jsonify({"items": items}), 200
    except Exception:
        logging.exception("Failed to update shopping cart")
        return jsonify({"error": "Failed to update shopping cart"}), 500