from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    request,
    url_for,
)
import math
import re

main_bp = Blueprint("main", __name__)

@main_bp.route("/") # user arrives here after logging out -> redirect to frontend homepage
def home():
    return redirect("http://localhost:5173")

def validate_user_info_json(data):
    required_fields = {
        #"people",
        # "budget",
        #"diet",
        #"days",
        "dislikes",
        # "name",
        "age",
        "sex",
        "height",
        "weight",
        "goal",
        "activityLevel",
        "dietaryRestrictions",
    }

    missing_fields = sorted(required_fields - data.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    #people = data["people"]
    #diet = data["diet"]
    #days = data["days"]
    dislikes = data["dislikes"]
    age = data["age"]
    sex = data["sex"]
    height = data["height"]
    weight = data["weight"]
    goal = data["goal"]
    activity_level = data["activityLevel"]
    dietary_restrictions = data["dietaryRestrictions"]
    zip_code = data.get("zipCode", "")

    if not isinstance(dislikes, str):
        raise ValueError("'dislikes' must be a string")

    if isinstance(age, bool) or not isinstance(age, int) or not 1 <= age <= 120:
        raise ValueError("'age' must be an integer from 1 to 120")

    allowed_sexes = {
        "female",
        "male",
        "intersex",
        "other",
        "prefer_not_to_say",
    }
    if not isinstance(sex, str) or sex not in allowed_sexes:
        raise ValueError("'sex' must be a supported selection")

    if (
        isinstance(height, bool)
        or not isinstance(height, (int, float))
        or not math.isfinite(height)
        or not 1 <= height <= 300
    ):
        raise ValueError("'height' must be between 1 and 300 cm")

    if (
        isinstance(weight, bool)
        or not isinstance(weight, (int, float))
        or not math.isfinite(weight)
        or not 1 <= weight <= 700
    ):
        raise ValueError("'weight' must be between 1 and 700 kg")

    if not isinstance(goal, str) or goal not in {"lose", "maintain", "gain"}:
        raise ValueError("'goal' must be lose, maintain, or gain")

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
        raise ValueError("'activityLevel' must be a supported selection")

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
        raise ValueError(
            "'dietaryRestrictions' must be a list of supported restrictions"
        )

    if (
        not isinstance(zip_code, str)
        or (zip_code and not re.fullmatch(r"\d{5}(?:-\d{4})?", zip_code))
    ):
        raise ValueError("'zipCode' must be a valid U.S. ZIP code")