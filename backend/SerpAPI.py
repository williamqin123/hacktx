import os
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

OUTPUT:
Always return valid JSON.
Do not include markdown.
Do not include explanations outside the JSON.
"""


def generate_meal_plan(people, budget, diet, days, dislikes):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY is not set")

    client = serpapi.Client(api_key=api_key)
    prompt = f"""
{AGENT_INSTRUCTIONS}

USER REQUEST:
People: {people}
Budget: ${budget}
Diet: {diet}
Days: {days}
Dislikes: {dislikes}

Create the meal plan.
"""

    results = client.search({
        "engine": "google_gemini",
        "q": prompt,
    })
    if hasattr(results, "as_dict"):
        return results.as_dict()
    return results