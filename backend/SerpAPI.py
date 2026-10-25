import os
import json

import serpapi
from dotenv import load_dotenv

load_dotenv()


AGENT_INSTRUCTIONS = """
You are MealMind, an intelligent meal-planning and grocery-shopping agent.

YOUR ROLE:
You help users create personalized meal plans and grocery lists.

YOUR GOALS:
1. Understand the user's dietary preferences.
2. Respect allergies and foods they dislike.
3. Stay within the user's budget.
4. Minimize food waste.
5. Reuse ingredients across multiple meals when practical.
6. Prefer simple recipes unless the user asks for something complicated.
7. Generate realistic ingredient quantities.
8. Never invent product prices.
9. Never claim a product is available at a store unless product data confirms it.

IMPORTANT:
You are not just a recipe generator.
You are planning meals with the user's actual grocery-shopping constraints in mind.

You are a meal planning agent.

Your response MUST be valid JSON.

Do NOT use markdown.
Do NOT use ```json.
Do NOT include explanations before or after the JSON.

Return one JSON object with exactly these top-level keys: "meal_plan" and
"grocery_list". Do not add sample values or placeholder text.

"meal_plan" must be an object with:
- "days": integer equal to requested days
- "people": integer equal to requested people
- "diet": the requested diet
- "budget": the requested budget as a number
- "calorie_goal_kcal_per_person": estimated integer daily calories, or null
- "calorie_guidance": a brief string describing that the estimate is approximate
- "daily_meals": array with exactly one entry per requested day

Each "daily_meals" entry must be an object with "day" (1-based integer),
"estimated_calories_kcal_per_person" (integer), and "meals" (object).
"meals" must contain "breakfast", "lunch", and "dinner". Each meal must be an
object with "name" (string), "estimated_calories_kcal_per_person" (integer),
"ingredients" (array of actual ingredient strings), "prep_time" (integer
minutes), and "Recipe" (array of detailed instruction strings).

"grocery_list" must be an array of objects. Every object must have "item"
(actual ingredient name, string) and "quantity" (realistic quantity string).
Use ingredients required by the recipes. Never output the words "example",
"placeholder", or template values in the meal plan or grocery list.

RULES:

1. "days" must equal the number of days requested by the user.

2. "people" must equal the number of people requested by the user.

3. "diet" must follow the user's requested diet.

4. "budget" must equal the user's requested grocery budget.

5. "daily_meals" must contain exactly one object for every day.

6. Each day must contain exactly three meals:
   - breakfast
   - lunch
   - dinner

7. Every meal must have:
   - "name": the name of the meal
   - "ingredients": an array of ingredient names

8. "grocery_list" must contain every ingredient needed for the complete meal plan.

9. Combine duplicate ingredients in the grocery list into a single item.

10. Each grocery list item must have:
    - "item": ingredient name
    - "quantity": realistic quantity needed for the requested number of people and days.

11. Respect all dietary restrictions and dislikes provided by the user.

12. Reuse ingredients across meals when practical to reduce food waste.

13. Do not invent grocery store products or prices.

14. Do not include ingredients that violate the user's dietary restrictions or explicitly stated dislikes.

15. The JSON must be valid and parseable by Python's json.loads().

16. Estimate a daily calorie target per person using age, sex, height, weight, activity level, and weight goal. This is an approximation, not medical advice.

17. If the person is under 18, do not recommend a calorie deficit or surplus; return null for the calorie target and put advice to consult a qualified health professional in "calorie_guidance".

18. For adults, choose meal portions and calorie estimates so the three meals' daily total is close to the estimated target. Return calories per person, not for the entire household.

19. Include the estimated daily calorie target and daily estimated calorie total in the output. Keep the menu, grocery quantities, and budget appropriate for all requested people.

20. Every breakfast, lunch, and dinner must include "prep_time" as a realistic integer number of minutes.

21. Every meal must include "Recipe" as an ordered array of clear, detailed cooking instructions. Include ingredient preparation, cooking temperatures or timing where relevant, and how to finish and serve the meal. The instructions and quantities must make sense for the requested number of people.
"""


def _decode_json_result(value):
    if hasattr(value, "as_dict"):
        value = value.as_dict()

    if isinstance(value, dict):
        if "meal_plan" in value and "grocery_list" in value:
            return value

        for key in (
            "text",
            "answer",
            "response",
            "content",
            "output",
            "result",
        ):
            if key in value:
                try:
                    return _decode_json_result(value[key])
                except ValueError:
                    continue

        for nested_value in value.values():
            try:
                return _decode_json_result(nested_value)
            except ValueError:
                continue

    if isinstance(value, list):
        for nested_value in value:
            try:
                return _decode_json_result(nested_value)
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
            decoder = json.JSONDecoder()
            for index, character in enumerate(text):
                if character != "{":
                    continue
                try:
                    parsed, _ = decoder.raw_decode(text[index:])
                except json.JSONDecodeError:
                    continue
                if not isinstance(parsed, (dict, list)):
                    break
                return _decode_json_result(parsed)
            raise ValueError("Gemini response did not contain the required JSON object")
        if not isinstance(parsed, (dict, list)):
            raise ValueError("Gemini response JSON must contain an object")
        return _decode_json_result(parsed)

    raise ValueError("Gemini response did not contain the required JSON object")


def _validate_meal_plan(result, requested_days):
    if not isinstance(result, dict):
        raise ValueError("Gemini JSON response must be an object")
    if not isinstance(result.get("meal_plan"), dict):
        raise ValueError('Gemini JSON must contain a "meal_plan" object')
    if not isinstance(result.get("grocery_list"), list):
        raise ValueError('Gemini JSON must contain a "grocery_list" array')

    plan = result["meal_plan"]
    if plan.get("days") != requested_days:
        raise ValueError(
            f'Gemini "meal_plan.days" must equal the requested {requested_days} day(s)'
        )
    daily_meals = plan.get("daily_meals")
    if not isinstance(daily_meals, list) or len(daily_meals) != requested_days:
        raise ValueError(
            f'Gemini "meal_plan.daily_meals" must contain exactly '
            f"{requested_days} day(s)"
        )

    def reject_placeholder(value, path):
        if isinstance(value, str) and any(
            marker in value.casefold() for marker in ("example", "placeholder")
        ):
            raise ValueError(f'{path} contains placeholder text')

    for day in daily_meals:
        meals = day.get("meals") if isinstance(day, dict) else None
        if not isinstance(meals, dict):
            raise ValueError('Each day must contain a "meals" object')
        for meal_name in ("breakfast", "lunch", "dinner"):
            meal = meals.get(meal_name)
            if not isinstance(meal, dict):
                raise ValueError(f'Each day must contain a "{meal_name}" object')
            if not isinstance(meal.get("name"), str):
                raise ValueError(f'"{meal_name}.name" must be a string')
            reject_placeholder(meal["name"], f"{meal_name}.name")
            if not isinstance(meal.get("ingredients"), list):
                raise ValueError(f'"{meal_name}.ingredients" must be an array')
            if not all(isinstance(ingredient, str) for ingredient in meal["ingredients"]):
                raise ValueError(f'"{meal_name}.ingredients" must contain strings')
            if not meal["ingredients"]:
                raise ValueError(f'"{meal_name}.ingredients" must not be empty')
            for ingredient in meal["ingredients"]:
                reject_placeholder(ingredient, f"{meal_name}.ingredients")
            calories = meal.get("estimated_calories_kcal_per_person")
            if isinstance(calories, bool) or not isinstance(calories, int):
                raise ValueError(
                    f'"{meal_name}.estimated_calories_kcal_per_person" must be an integer'
                )
            if (
                isinstance(meal.get("prep_time"), bool)
                or not isinstance(meal.get("prep_time"), int)
            ):
                raise ValueError(f'"{meal_name}.prep_time" must be an integer')
            if not isinstance(meal.get("Recipe"), list) or not meal["Recipe"] or not all(
                isinstance(step, str) and step.strip() for step in meal["Recipe"]
            ):
                raise ValueError(f'"{meal_name}.Recipe" must be an array of steps')
            for step in meal["Recipe"]:
                reject_placeholder(step, f"{meal_name}.Recipe")

        daily_calories = day.get("estimated_calories_kcal_per_person")
        if isinstance(daily_calories, bool) or not isinstance(daily_calories, int):
            raise ValueError(
                '"daily_meals[].estimated_calories_kcal_per_person" must be an integer'
            )

    calorie_goal = plan.get("calorie_goal_kcal_per_person")
    if calorie_goal is not None and (
        isinstance(calorie_goal, bool) or not isinstance(calorie_goal, int)
    ):
        raise ValueError(
            '"meal_plan.calorie_goal_kcal_per_person" must be an integer or null'
        )
    if not isinstance(plan.get("calorie_guidance"), str):
        raise ValueError('"meal_plan.calorie_guidance" must be a string')
    if not result["grocery_list"]:
        raise ValueError('"grocery_list" must not be empty')

    for item in result["grocery_list"]:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("item"), str)
            or not isinstance(item.get("quantity"), str)
        ):
            raise ValueError(
                'Each "grocery_list" entry must have string "item" and "quantity" fields'
            )
        reject_placeholder(item["item"], "grocery_list.item")
        reject_placeholder(item["quantity"], "grocery_list.quantity")


def generate_meal_plan(
    people,
    #budget,
    diet,
    days,
    dislikes,
    #name,
    age,
    sex,
    height,
    weight,
    goal,
    activity_level,
    dietary_restrictions,
):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY is not set")

    client = serpapi.Client(api_key=api_key)
    prompt = f"""
{AGENT_INSTRUCTIONS}

USER REQUEST:
Number of People to Feed: {people}
Meal Plan Diet Description: {diet}
Number of Days: {days}
Dislikes: {dislikes}

CUSTOMER PROFILE:
Age: {age}
Sex: {sex}
Height: {height} cm
Weight: {weight} kg
Weight goal: {goal}
Activity level: {activity_level}
Dietary restrictions: {", ".join(dietary_restrictions) or "None"}

Create the meal plan.
"""

    results = client.search({
        "engine": "google_gemini",
        "q": prompt,
    })
    meal_plan = _decode_json_result(results)
    _validate_meal_plan(meal_plan, days)
    return meal_plan