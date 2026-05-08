"""
Paste helper: process a manual chat-mode response and save artifacts.

When the user pastes a model response (from claude.ai / chatgpt.com / gemini /
grok web browser), this script:
  1. Extracts def solve() and TEST_OUTPUT (hand grid)
  2. Runs run_feedback.py against the puzzle
  3. Saves all artifacts under Model Results/<Model>/<puzzle>/iter_N_*
  4. Prints a JSON manifest of paths so the caller can push to GitHub

Usage:
  python paste_helper.py <puzzle_id> <model> <paste_file> [--iter N]

Example:
  python paste_helper.py 13e47133 gpt /tmp/paste.txt

Looks for the puzzle file at:
  ./evaluation/<id>.json   (preferred / canonical)
  ./puzzle_<id>.json       (legacy)
"""

import argparse
import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path


MODEL_DIR = {
    "claude":     "Claude",
    "gpt":        "GPT",
    "gemini":     "Gemini",
    "grok":       "Grok",
    "openrouter": "OpenRouter",
}


def extract_solve(text):
    fence_matches = re.findall(
        r"```(?:python)?\s*\n([\s\S]*?def solve\b[\s\S]*?)\n```",
        text,
    )
    if fence_matches:
        return fence_matches[-1].rstrip()
    raw_matches = re.findall(
        r"^(def solve\b[\s\S]*?)(?=\n```|\n# end|\Z)",
        text, re.MULTILINE,
    )
    if raw_matches:
        return raw_matches[-1].rstrip()
    return None


def extract_hand_grid(text):
    """Find TEST_OUTPUT = [...] and walk the brackets to find the matching close.
    Robust against multi-line nested lists; the prior regex would only catch
    a single inner list before the outer ]."""
    m = re.search(r"TEST_OUTPUT\s*=\s*\[", text)
    if not m:
        return None
    start = m.end() - 1
    depth = 0
    end = None
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None
    try:
        grid = ast.literal_eval(text[start:end])
        if (isinstance(grid, list)
                and all(isinstance(row, list) for row in grid)
                and all(isinstance(v, int) for row in grid for v in row)):
            return grid
    except (ValueError, SyntaxError):
        pass
    return None


def validate_hand_grid(hand_grid, puzzle_file):
    if hand_grid is None:
        return None
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    if not puzzle.get("test") or "output" not in puzzle["test"][0]:
        return None
    truth = puzzle["test"][0]["output"]
    if len(hand_grid) != len(truth) or any(
        len(hand_grid[r]) != len(truth[r]) for r in range(len(truth))
    ):
        return {"dimension_mismatch": True}
    diffs = sum(
        1 for r in range(len(truth)) for c in range(len(truth[0]))
        if hand_grid[r][c] != truth[r][c]
    )
    total = len(truth) * len(truth[0])
    return {"matches": diffs == 0, "diffs": diffs, "total": total}


def validate_code_on_test(puzzle_file, solution_path):
    with open(puzzle_file) as f:
        puzzle = json.load(f)
    if not puzzle.get("test") or "output" not in puzzle["test"][0]:
        return None
    test_input = puzzle["test"][0]["input"]
    truth = puzzle["test"][0]["output"]
    spec = importlib.util.spec_from_file_location("_iter_sol", solution_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        out = mod.solve(test_input)
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    if not isinstance(out, list) or not out or not isinstance(out[0], list):
        return {"status": "error", "msg": "solve() did not return 2D list"}
    if len(out) != len(truth) or any(
        len(out[r]) != len(truth[r]) for r in range(len(truth))
    ):
        return {"status": "dim_mismatch", "got": f"{len(out)}x{len(out[0])}"}
    diffs = sum(
        1 for r in range(len(truth)) for c in range(len(truth[0]))
        if out[r][c] != truth[r][c]
    )
    total = len(truth) * len(truth[0])
    return {"matches": diffs == 0, "diffs": diffs, "total": total}


def next_iter_n(model_dir):
    if not model_dir.exists():
        return 1
    existing = [
        int(p.stem.split("_")[1])
        for p in model_dir.glob("iter_*_response.txt")
        if p.stem.split("_")[1].isdigit()
    ]
    return max(existing, default=0) + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("puzzle_id")
    parser.add_argument("model", help=f"One of: {', '.join(MODEL_DIR)}")
    parser.add_argument("paste_file")
    parser.add_argument("--iter", type=int, default=None)
    args = parser.parse_args()

    model_key = args.model.lower()
    if model_key not in MODEL_DIR:
        print(json.dumps({"error": f"unknown model {args.model}"}))
        sys.exit(1)

    puzzle_file = str(Path("evaluation") / f"{args.puzzle_id}.json")
    if not Path(puzzle_file).exists():
        legacy = f"puzzle_{args.puzzle_id}.json"
        if Path(legacy).exists():
            puzzle_file = legacy
        else:
            print(json.dumps({"error": f"puzzle file not found: {puzzle_file} or {legacy}"}))
            sys.exit(1)

    out_dir = Path("Model Results") / MODEL_DIR[model_key] / args.puzzle_id
    out_dir.mkdir(parents=True, exist_ok=True)

    n = args.iter if args.iter is not None else next_iter_n(out_dir)

    history_file = f"{args.puzzle_id}_history.json"
    if n == 1 and os.path.exists(history_file):
        os.remove(history_file)
        for ckpt in Path(".").glob(f"{args.puzzle_id}_checkpoint_pair_*.py"):
            ckpt.unlink()

    response = Path(args.paste_file).read_text()
    response_path = out_dir / f"iter_{n}_response.txt"
    response_path.write_text(response)

    code = extract_solve(response)
    if code is None:
        manifest = {
            "iter": n,
            "model": args.model,
            "puzzle_id": args.puzzle_id,
            "error": "no def solve() in response",
            "files": {"response": str(response_path)},
        }
        print(json.dumps(manifest, indent=2))
        sys.exit(1)

    code_path = out_dir / f"iter_{n}_response.py"
    code_path.write_text(code)
    Path("solution.py").write_text(code)

    hand_grid = extract_hand_grid(response)
    hand_grid_path = None
    hand_validation = None
    if hand_grid is not None:
        hand_grid_path = out_dir / f"iter_{n}_hand_grid.json"
        hand_grid_path.write_text(json.dumps(hand_grid))
        hand_validation = validate_hand_grid(hand_grid, puzzle_file)

    result = subprocess.run(
        [sys.executable, "run_feedback.py", puzzle_file, "solution"],
        capture_output=True, text=True,
    )
    feedback_file = Path(f"feedback_{args.puzzle_id}.txt")
    if feedback_file.exists():
        feedback = feedback_file.read_text()
    else:
        feedback = (f"VALIDATOR ERROR (exit {result.returncode}):\n\n"
                    f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")

    feedback_path = out_dir / f"iter_{n}_feedback.txt"
    feedback_path.write_text(feedback)

    verdict = "UNKNOWN"
    if "Verdict: SUBMIT" in feedback or "VERDICT: SUBMIT" in feedback:
        verdict = "SUBMIT"
    elif "DO NOT SUBMIT" in feedback:
        verdict = "DO NOT SUBMIT"

    code_test_result = validate_code_on_test(puzzle_file, "solution.py")

    summary = {
        "iter": n,
        "model": args.model,
        "puzzle_id": args.puzzle_id,
        "verdict": verdict,
        "hand_grid_validation": hand_validation,
        "code_test_result": code_test_result,
    }
    summary_path = out_dir / f"iter_{n}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    manifest = {
        "iter": n,
        "model": args.model,
        "puzzle_id": args.puzzle_id,
        "verdict": verdict,
        "hand_grid_validation": hand_validation,
        "code_test_result": code_test_result,
        "files": {
            "response": str(response_path),
            "code": str(code_path),
            "feedback": str(feedback_path),
            "summary": str(summary_path),
            **({"hand_grid": str(hand_grid_path)} if hand_grid_path else {}),
        },
    }
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
