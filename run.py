"""Command line entry point.

    python run.py path/to/recipe.txt          extract one recipe from a file
    python run.py --sample                    extract the first 5 recipes of data/recipes.jsonl
    python run.py --all                       extract every recipe and print how many match the labels
    python run.py --adapt "milk" path/to/recipe.txt

    RECIPES_BACKEND=claude-code python run.py --all    same, through `claude -p` on a subscription
"""

import json
import sys
from pathlib import Path

from recipes.extract import BACKEND, USAGE, extract_recipe

DATA = Path(__file__).resolve().parent / "data" / "recipes.jsonl"


def recipes() -> list[dict]:
    return [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]


def matches(result: dict, label: dict) -> bool:
    return (
        set(result.get("allergens", [])) == set(label["allergens"])
        and result.get("vegetarian") == label["vegetarian"]
        and result.get("vegan") == label["vegan"]
    )


def print_cost() -> None:
    if not USAGE:
        return
    tokens_in = sum(u["input_tokens"] for u in USAGE)
    tokens_out = sum(u["output_tokens"] for u in USAGE)
    cost = sum(u["cost_usd"] for u in USAGE)
    kind = "estimated API cost" if any(u["estimated"] for u in USAGE) else "API cost"
    print(f"{len(USAGE)} calls ({BACKEND}) · {tokens_in} input + {tokens_out} output tokens · {kind}: {cost:.4f} USD")


def main(args: list[str]) -> None:
    if not args:
        print(__doc__)
        return
    if args[0] == "--adapt":
        from recipes.adapt import adapt_recipe  # API only

        print(adapt_recipe(Path(args[2]).read_text(), args[1]))
        return
    if args[0] in ("--sample", "--all"):
        rows = recipes() if args[0] == "--all" else recipes()[:5]
        correct = 0
        for row in rows:
            result = extract_recipe(row["text"])
            ok = matches(result, row["label"])
            correct += ok
            print(("OK  " if ok else "MISS"), row["id"], sorted(result.get("allergens", [])), "expected", sorted(row["label"]["allergens"]))
        print(f"\n{correct}/{len(rows)} match the labels (allergens, vegetarian, vegan)")
        print_cost()
        return
    print(json.dumps(extract_recipe(Path(args[0]).read_text()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
