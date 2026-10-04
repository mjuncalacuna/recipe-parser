"""Read a free-text recipe and return its structured data."""

import json

import anthropic

from .prompts import load

MODEL = "claude-opus-4-1"

client = anthropic.Anthropic()


def extract_recipe(text: str, retries: int = 3) -> dict:
    """Return the recipe as a dict: title, servings, total_minutes, difficulty,
    ingredients, allergens, vegetarian, vegan and summary.

    The model is prefilled with "{" so it starts the JSON object right away. If
    the JSON does not parse, we try again.
    """
    system = load("system_extract")
    last_error = None
    for _ in range(retries):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            temperature=0.2,
            system=system,
            messages=[
                {"role": "user", "content": f"Recipe:\n\"\"\"\n{text}\n\"\"\"\n\nRemember: answer ONLY with the JSON."},
                {"role": "assistant", "content": "{"},
            ],
        )
        raw = "{" + response.content[0].text
        raw = raw[: raw.rfind("}") + 1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            last_error = error
    raise ValueError(f"Could not parse the model's JSON after {retries} tries: {last_error}")
