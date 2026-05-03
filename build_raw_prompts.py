"""Build raw prompts from ARC-AGI puzzle JSON files.

Reads every *.json puzzle from ./evaluation, strips the test output(s),
and writes a copy-pasteable prompt for each puzzle into ./Raw Prompts.
"""

import json
from pathlib import Path

PUZZLES_DIR = Path("evaluation")
OUTPUT_DIR = Path("Raw Prompts")
INSTRUCTION = (
    "Solve this ARC-AGI puzzle and output the test output grid "
    "and a short description of your transformation rule."
)


def build_prompt(puzzle: dict) -> str:
    stripped = {
        "train": puzzle["train"],
        "test": [{"input": t["input"]} for t in puzzle["test"]],
    }
    return json.dumps(stripped, indent=2) + "\n\n" + INSTRUCTION + "\n"


def main() -> None:
    if not PUZZLES_DIR.is_dir():
        raise SystemExit(f"Puzzle folder not found: {PUZZLES_DIR.resolve()}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    puzzle_paths = sorted(PUZZLES_DIR.glob("*.json"))
    if not puzzle_paths:
        print(f"No .json puzzles found in {PUZZLES_DIR}/")
        return

    for path in puzzle_paths:
        puzzle = json.loads(path.read_text())
        prompt = build_prompt(puzzle)
        out_path = OUTPUT_DIR / f"{path.stem}.txt"
        out_path.write_text(prompt)
        print(f"Wrote {out_path}")

    print(f"\nDone. {len(puzzle_paths)} prompt(s) written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
