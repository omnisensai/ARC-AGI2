"""Build SFT/DPO training JSONLs from the per-puzzle agent corpus.

Reads research/agent_corpus/by_puzzle/<pid>.json files and produces:

    phase2_train.jsonl
        One line per (puzzle, right_code) pair.
        Task: see the puzzle's training pairs, produce a correct `solve()`.
        System tag: 'D'  (pairs -> code).

    phase3_train.jsonl
        One line per (puzzle, wrong_code, right_code) triple (Cartesian product
        per puzzle). The user message includes the wrong code + structured
        feedback (pass/fail per training pair + cell-diff counts). The
        assistant target is the right code.
        System tag: 'E'  (wrong code + feedback -> right code).

    phase3_dpo.jsonl
        DPO preference pairs: same prompt as phase3 SFT but split into chosen
        (right_code) and rejected (wrong_code). Same Cartesian-product
        expansion. For use in DPO post-SFT alignment, not SFT itself.

Skips puzzles with zero right_codes (nothing to train toward).
Skips puzzles with zero wrong_codes for phase3 (no corrector signal).

Usage:
    python3 build_sft_jsonl.py                    # default out: repo root
    python3 build_sft_jsonl.py --out-dir sft_out  # custom out dir
"""
import argparse
import json
from pathlib import Path

from substrate import format_grid


PHASE2_SYSTEM = "D"
PHASE3_SYSTEM = "E"


def render_puzzle_pairs(puzzle: dict, include_test_answer: bool = False) -> str:
    """Format a puzzle's training pairs (and optionally test) for the prompt."""
    parts = []
    for i, p in enumerate(puzzle["train"]):
        parts.append(f"Training pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
                     f"Output:\n{format_grid(p['output'])}")
    for i, p in enumerate(puzzle["test"]):
        if include_test_answer:
            parts.append(f"Test pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
                         f"Output:\n{format_grid(p['output'])}")
        else:
            parts.append(f"Test input:\n{format_grid(p['input'])}")
    return "\n\n".join(parts)


def render_feedback(wrong_pairs: list) -> str:
    """Render the structured feedback that R2 sees alongside the wrong code.

    Format: one line per training pair, status + cell_diff (if applicable).
    Skip test pairs — at competition inference time we don't see them, so the
    corrector must work from training-pair signal only.
    """
    lines = []
    for p in wrong_pairs:
        if p["type"] != "train":
            continue
        if p["passed"]:
            status = "PASS"
        elif p["error"]:
            status = f"FAIL ({p['error']})"
        elif p["cell_diff"] is not None:
            status = f"FAIL (cell_diff={p['cell_diff']})"
        else:
            status = "FAIL (shape mismatch)"
        lines.append(f"  Training pair {p['idx']+1}: {status}")
    return "\n".join(lines)


def make_phase2_record(puzzle: dict, puzzle_id: str, right_code: dict) -> dict:
    """Phase 2: puzzle -> correct code. SFT format."""
    return {
        "task": "phase2",
        "puzzle_id": puzzle_id,
        "right_code_source": right_code.get("source"),
        "messages": [
            {"role": "system", "content": PHASE2_SYSTEM},
            {"role": "user", "content": (
                "Write a Python `def solve(input_grid):` function that produces the "
                "correct output for the test input. The function must generalize from "
                "the training pairs below.\n\n"
                + render_puzzle_pairs(puzzle, include_test_answer=False)
            )},
            {"role": "assistant", "content": right_code["code"]},
        ],
    }


def make_phase3_record(puzzle: dict, puzzle_id: str,
                       wrong_code: dict, right_code: dict) -> dict:
    """Phase 3: wrong code + feedback -> right code. SFT format."""
    feedback = render_feedback(wrong_code.get("pairs", []))
    return {
        "task": "phase3",
        "puzzle_id": puzzle_id,
        "wrong_code_source": wrong_code.get("source"),
        "right_code_source": right_code.get("source"),
        "messages": [
            {"role": "system", "content": PHASE3_SYSTEM},
            {"role": "user", "content": (
                "The following Python `solve(input_grid)` function is incorrect on "
                "this ARC puzzle. Rewrite it so all training pairs pass.\n\n"
                + render_puzzle_pairs(puzzle, include_test_answer=False)
                + "\n\nWrong code:\n```python\n" + wrong_code["code"] + "\n```\n\n"
                "Validation against the wrong code:\n" + feedback
            )},
            {"role": "assistant", "content": right_code["code"]},
        ],
    }


def make_phase3_dpo_record(puzzle: dict, puzzle_id: str,
                           wrong_code: dict, right_code: dict) -> dict:
    """Phase 3 DPO: same prompt, chosen=right, rejected=wrong."""
    feedback = render_feedback(wrong_code.get("pairs", []))
    prompt_text = (
        "Write a Python `def solve(input_grid):` function that produces the "
        "correct output for the test input.\n\n"
        + render_puzzle_pairs(puzzle, include_test_answer=False)
    )
    return {
        "task": "phase3_dpo",
        "puzzle_id": puzzle_id,
        "wrong_code_source": wrong_code.get("source"),
        "right_code_source": right_code.get("source"),
        "prompt": [
            {"role": "system", "content": PHASE2_SYSTEM},
            {"role": "user", "content": prompt_text},
        ],
        "chosen": [{"role": "assistant", "content": right_code["code"]}],
        "rejected": [{"role": "assistant", "content": wrong_code["code"]}],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-dir", default="research/agent_corpus/by_puzzle")
    ap.add_argument("--puzzle-dirs", nargs="+",
                    default=["data/arc1_train", "data/arc1_eval", "data/arc2_train"],
                    help="Puzzle dirs to read from. arc2_eval is deliberately NOT in the "
                         "default list — it's the official ARC-AGI-2 held-out benchmark and "
                         "must never enter training data.")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    corpus_dir = Path(args.corpus_dir)
    out_dir = Path(args.out_dir)

    # Build a puzzle_id -> full puzzle JSON map (across all source dirs).
    # arc2_eval is intentionally excluded from --puzzle-dirs default; any corpus
    # record for a puzzle not in the chosen dirs is skipped with a warning. This
    # is how we enforce the comp-clean invariant: training never reads arc2_eval.
    puzzle_map = {}
    for d in args.puzzle_dirs:
        for p in Path(d).glob("*.json"):
            puzzle_map.setdefault(p.stem, json.loads(p.read_text()))

    phase2_lines = []
    phase3_lines = []
    dpo_lines = []
    stats = {"puzzles": 0, "rights": 0, "wrongs": 0,
             "phase2": 0, "phase3": 0, "dpo": 0,
             "skipped_unknown_puzzle": 0, "skipped_no_rights": 0}

    for cf in sorted(corpus_dir.glob("*.json")):
        rec = json.loads(cf.read_text())
        pid = rec["puzzle_id"]
        puzzle = puzzle_map.get(pid)
        if puzzle is None:
            print(f"  skip {pid}: no puzzle JSON in {args.puzzle_dirs} "
                  f"(likely arc2_eval, correctly excluded from training)")
            stats["skipped_unknown_puzzle"] += 1
            continue
        rights = rec.get("right_codes", [])
        wrongs = rec.get("wrong_codes", [])
        if not rights:
            stats["skipped_no_rights"] += 1
            continue
        stats["puzzles"] += 1
        stats["rights"] += len(rights)
        stats["wrongs"] += len(wrongs)

        for right in rights:
            phase2_lines.append(make_phase2_record(puzzle, pid, right))
            stats["phase2"] += 1
            for wrong in wrongs:
                phase3_lines.append(make_phase3_record(puzzle, pid, wrong, right))
                dpo_lines.append(make_phase3_dpo_record(puzzle, pid, wrong, right))
                stats["phase3"] += 1
                stats["dpo"] += 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, recs in [("phase2_train.jsonl", phase2_lines),
                        ("phase3_train.jsonl", phase3_lines),
                        ("phase3_dpo.jsonl", dpo_lines)]:
        path = out_dir / fname
        with path.open("w") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        print(f"  wrote {path}  ({len(recs)} records)")

    print(f"\nFrom {stats['puzzles']} puzzles "
          f"({stats['rights']} right_codes, {stats['wrongs']} wrong_codes):")
    print(f"  phase2 SFT records  (puzzle -> right code):           {stats['phase2']}")
    print(f"  phase3 SFT records  (puzzle + wrong + fb -> right):   {stats['phase3']}")
    print(f"  phase3 DPO pairs    (chosen=right, rejected=wrong):   {stats['dpo']}")


if __name__ == "__main__":
    main()
