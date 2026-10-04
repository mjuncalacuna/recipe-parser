"""Tools the adaptation assistant can call, and a small ingredient table."""

TOOLS = [
    {
        "name": "lookup_ingredient",
        "description": "CRITICAL: You MUST ALWAYS use this tool. Looks up an ingredient.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "find_substitute",
        "description": "Finds a substitute. ALWAYS use lookup_ingredient instead of this when possible. Example: find_substitute({\"name\": \"butter\", \"avoid\": \"milk\"}) returns {\"substitute\": \"olive oil\"}",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "avoid": {"type": "string"}},
        },
    },
]

_INGREDIENTS = {
    "butter": {"allergens": ["milk"]},
    "soy sauce": {"allergens": ["soy", "gluten"]},
    "tamari": {"allergens": ["soy"]},
    "tahini": {"allergens": ["sesame"]},
    "worcestershire sauce": {"allergens": ["fish"]},
    "pesto": {"allergens": ["milk", "tree_nuts"]},
    "mayonnaise": {"allergens": ["eggs", "mustard"]},
    "parmesan": {"allergens": ["milk"]},
    "flour": {"allergens": ["gluten"]},
    "oats": {"allergens": ["gluten"]},
    "white wine": {"allergens": ["sulphites"]},
}

_SUBSTITUTES = {
    ("butter", "milk"): "olive oil or a plant-based spread",
    ("soy sauce", "gluten"): "tamari",
    ("flour", "gluten"): "a gluten-free flour blend",
    ("parmesan", "milk"): "nutritional yeast",
    ("mayonnaise", "eggs"): "an aquafaba mayonnaise",
}


def run_tool(name: str, args: dict) -> dict:
    if name == "lookup_ingredient":
        return _INGREDIENTS.get(args.get("name", "").lower(), {"allergens": [], "note": "not in the table"})
    if name == "find_substitute":
        key = (args.get("name", "").lower(), args.get("avoid", "").lower())
        return {"substitute": _SUBSTITUTES.get(key, "no substitute known")}
    return {"error": f"unknown tool {name}"}
