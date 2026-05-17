"""
Proof of concept: feedback_diagnostics correctly fingerprints the
4-conn vs 8-conn bug class on 13e47133 from a real iter-1 wrong output.

Loads the puzzle, runs Grok_NoTrans iter 1's solver (known to produce
56/900 wrong on test, 4/400 wrong on training pair 1 with the
connectivity-mismatch fingerprint), and asserts that:
  - phase classifier returns "code_debug" (cell correctness >= 85%)
  - conn_mismatch detector fires
"""

import importlib.util
import json
from pathlib import Path

from feedback_diagnostics import diagnose_full, format_targeted_feedback


PUZZLE = Path("evaluation/13e47133.json")
SOLVER = Path("legacy/Model Results/Grok_NoTrans/13e47133/iter_1_response.py")


def load_solver(path):
    spec = importlib.util.spec_from_file_location("_iter_sol", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.solve


def main():
    puzzle = json.loads(PUZZLE.read_text())
    solve = load_solver(SOLVER)

    actual_outputs = [solve(p["input"]) for p in puzzle["train"]]

    diag = diagnose_full(puzzle, actual_outputs)
    print(format_targeted_feedback(diag))
    print()

    assert diag["phase"]["phase"] == "code_debug", (
        f"expected code_debug, got {diag['phase']['phase']} "
        f"(correctness={diag['phase']['correctness']:.3f})"
    )
    matched = [b["bug_class"] for b in diag["bugs"]]
    assert "connectivity_mismatch" in matched, (
        f"expected connectivity_mismatch in matched bugs, got {matched}"
    )

    print("All assertions passed.")


if __name__ == "__main__":
    main()
