"""Adapt a recipe for a food allergy, looking ingredients up first."""

import anthropic

from .prompts import load
from .tools import TOOLS, run_tool

MODEL = "claude-sonnet-4-5"

client = anthropic.Anthropic()


def adapt_recipe(recipe: str, allergy: str) -> str:
    system = load("system_adapt")
    messages = [{"role": "user", "content": f"Allergy: {allergy}\n\nRecipe:\n{recipe}"}]
    first = True
    for _ in range(8):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=0.7,
            system=system,
            tools=TOOLS,
            # Force a tool call on the first turn so the model always looks the ingredients up.
            tool_choice={"type": "tool", "name": "lookup_ingredient"} if first else {"type": "auto"},
            messages=messages,
        )
        first = False
        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")
        messages.append({"role": "assistant", "content": response.content})
        results = [
            {"type": "tool_result", "tool_use_id": block.id, "content": str(run_tool(block.name, block.input))}
            for block in response.content
            if block.type == "tool_use"
        ]
        messages.append({"role": "user", "content": results})
    raise RuntimeError("The assistant did not finish in 8 turns")
