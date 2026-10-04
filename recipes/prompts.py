from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def load(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()
