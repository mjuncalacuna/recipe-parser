"""Read a free-text recipe and return its structured data.

Two backends, chosen with the RECIPES_BACKEND environment variable:

- "api" (default): the Claude API through the anthropic SDK. Real calls, real cost.
- "claude-code": `claude -p` with the same system prompt, no tools, no project
  settings, from an empty directory. It runs on a Claude subscription instead of
  the API, so evals cost nothing. It measures the prompt and the model, not this
  exact code path: the prefill, temperature and retries below do not apply.
  RECIPES_CLI_MODEL picks the model (default "sonnet").
"""

import json
import os
import subprocess
import tempfile

from .prompts import PROMPTS, load

MODEL = "claude-opus-4-1"
BACKEND = os.environ.get("RECIPES_BACKEND", "api")
CLI_MODEL = os.environ.get("RECIPES_CLI_MODEL", "sonnet")

# USD per million tokens (input, output), for the API backend's cost.
PRICES = {"claude-opus-4-1": (15.0, 75.0), "claude-sonnet-4-5": (3.0, 15.0), "claude-haiku-4-5": (1.0, 5.0)}

# One entry per model call: backend, model, tokens and cost (estimated for claude-code).
USAGE: list[dict] = []

_client = None


def _api():
    global _client
    if _client is None:
        import anthropic  # only the API backend needs the SDK

        _client = anthropic.Anthropic()
    return _client


def _user_message(text: str) -> str:
    return f"Recipe:\n\"\"\"\n{text}\n\"\"\"\n\nRemember: answer ONLY with the JSON."


def _call_api(system: str, text: str) -> str:
    response = _api().messages.create(
        model=MODEL,
        max_tokens=1500,
        temperature=0.2,
        system=system,
        messages=[
            {"role": "user", "content": _user_message(text)},
            {"role": "assistant", "content": "{"},
        ],
    )
    price_in, price_out = PRICES.get(MODEL, (0.0, 0.0))
    u = response.usage
    USAGE.append({
        "backend": "api", "model": MODEL, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
        "cost_usd": (u.input_tokens * price_in + u.output_tokens * price_out) / 1e6, "estimated": False,
    })
    return "{" + response.content[0].text


def _call_claude_code(text: str) -> str:
    # Never let `claude -p` fall back to the API key: with it in the environment it bills the API.
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")}
    with tempfile.TemporaryDirectory() as empty:
        proc = subprocess.run(
            [
                "claude", "-p",
                "--system-prompt-file", str(PROMPTS / "system_extract.md"),
                "--tools", "",
                "--model", CLI_MODEL,
                "--output-format", "json",
                "--no-session-persistence",
                "--strict-mcp-config",
                "--setting-sources", "project",
                _user_message(text),
            ],
            cwd=empty, env=env, capture_output=True, text=True, timeout=300,
        )
    data = json.loads(proc.stdout)
    if data.get("is_error"):
        raise RuntimeError(f"claude -p failed: {data.get('result')}")
    u = data.get("usage", {})
    USAGE.append({
        "backend": "claude-code", "model": ",".join(data.get("modelUsage", {})) or CLI_MODEL,
        "input_tokens": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        # Claude Code's own estimate of what the call would cost on the API. It includes the
        # ~550 tokens of context the CLI adds (environment, model, date), so it runs a bit high.
        "cost_usd": data.get("total_cost_usd", 0.0), "estimated": True,
    })
    return data["result"]


def extract_recipe(text: str, retries: int = 3) -> dict:
    """Return the recipe as a dict: title, servings, total_minutes, difficulty,
    ingredients, allergens, vegetarian, vegan and summary.

    With the API backend the model is prefilled with "{" so it starts the JSON
    object right away. If the JSON does not parse, we try again.
    """
    system = load("system_extract")
    last_error = None
    for _ in range(retries):
        raw = _call_claude_code(text) if BACKEND == "claude-code" else _call_api(system, text)
        raw = raw[raw.find("{") : raw.rfind("}") + 1]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            last_error = error
    raise ValueError(f"Could not parse the model's JSON after {retries} tries: {last_error}")
