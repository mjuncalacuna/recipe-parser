# recipe-parser

A small app that reads a recipe written in free text (a blog post, a message, a cookbook page, in any language) and turns it into structured data with Claude: ingredients, servings, total time, difficulty, the 14 EU allergens, and whether it is vegetarian or vegan. A second feature adapts a recipe for a food allergy, looking ingredients up with a tool.

## Why this repo exists

It is a test bench for Anthropic's `claude-api` skill in Claude Code, run on code that is not mine to share. **The app is deliberately written the way many Claude apps were written in 2024-2025**: shouting prompts, "think step by step", hard word limits, a JSON prefill with a retry loop, `temperature`, forced `tool_choice`, older model IDs, a long system prompt sent uncached on every call, and a large model for a simple extraction.

That gives each subcommand something real to find:

| Command | What it looks at here |
|---|---|
| `/claude-api prompt-audit` | the prompts in `prompts/`, the tool descriptions in `recipes/tools.py`, `CLAUDE.md` |
| `/claude-api migrate` | moving `recipes/extract.py` and `recipes/adapt.py` to a current model |
| `/claude-api build-eval` | an eval for the extraction, with `data/recipes.jsonl` as labelled cases |
| `/claude-api hillclimb` | improving the extraction against that eval |
| `/claude-api cost-optimize` | what the extraction costs per recipe and how to lower it |

## Data

`data/recipes.jsonl` has 48 synthetic recipes in English, Spanish, French, German and Italian, each labelled with its allergens, vegetarian, vegan, total minutes and servings. Some are traps on purpose: dashi (fish), a red curry paste with shrimp paste, hoisin sauce with wheat, oat milk (gluten), Worcestershire sauce (fish).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python run.py --sample        # 5 recipes, compares with the labels
python run.py --all           # all 48
python run.py --adapt "milk" some_recipe.txt
```

Every run calls the Claude API and costs money. `--all` makes 48 calls.
