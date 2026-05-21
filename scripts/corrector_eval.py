"""Corrector-loop eval — invokes the model's full trained pipeline at inference.

For each puzzle:
1. Round 1: Task D prompt (puzzle -> code), system='D'.
2. Run the code on training pairs.
3. If all pass: mark solved at round 1, also try test pair, record outcome.
4. Otherwise: build Task E prompt with the wrong code + per-pair feedback.
5. Round 2..N: Task E prompt with the latest wrong code + feedback, system='E'.
6. Stop when either all train pairs pass or max-rounds reached.

This invokes Phase E behavior (24% of training, never tested in single-shot eval).
Output structure mirrors bulk_collect.py for downstream analysis.

Usage:
    python3 scripts/corrector_eval.py \\
        --model arc \\
        --api-base http://localhost:8000/v1 \\
        --api-key EMPTY \\
        --splits splits/holdout_augmented_706.json \\
        --puzzle-dir data/augmented_eval_706 \\
        --runs 1 \\
        --max-rounds 5 \\
        --workers 8
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from substrate import format_grid, strip_python_comments  # noqa: E402


# --- Prompt builders (byte-identical to build_sft_jsonl.py) ---

PHASE_D_SYSTEM = "D"
PHASE_E_SYSTEM = "E"


def render_puzzle_pairs(puzzle, include_test_answer=False):
    parts = []
    for i, p in enumerate(puzzle["train"]):
        parts.append(
            f"Training pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
            f"Output:\n{format_grid(p['output'])}"
        )
    for i, p in enumerate(puzzle["test"]):
        if include_test_answer:
            parts.append(
                f"Test pair {i+1}:\nInput:\n{format_grid(p['input'])}\n\n"
                f"Output:\n{format_grid(p['output'])}"
            )
        else:
            parts.append(f"Test input:\n{format_grid(p['input'])}")
    return "\n\n".join(parts)


def build_d_prompt(puzzle):
    return (
        "Write a Python `def solve(input_grid):` function that produces the "
        "correct output for the test input. The function must generalize from "
        "the training pairs below.\n\n"
        + render_puzzle_pairs(puzzle, include_test_answer=False)
    )


def render_feedback(pairs):
    """Render per-train-pair feedback in the same format the corrector saw during training."""
    lines = []
    for p in pairs:
        if p.get("type") != "train":
            continue
        if p.get("passed"):
            status = "PASS"
        elif p.get("error"):
            status = f"FAIL ({p['error']})"
        elif p.get("cell_diff") is not None:
            status = f"FAIL (cell_diff={p['cell_diff']})"
        else:
            status = "FAIL (shape mismatch)"
        lines.append(f"  Training pair {p['idx']+1}: {status}")
    if not lines:
        lines.append("  (no pair-level results: wrong code failed at import/exec)")
    return "\n".join(lines)


def build_e_prompt(puzzle, wrong_code, pair_results):
    feedback = render_feedback(pair_results)
    stripped_wrong = strip_python_comments(wrong_code)
    return (
        "The following Python `solve(input_grid)` function is incorrect on "
        "this ARC puzzle. Rewrite it so all training pairs pass.\n\n"
        + render_puzzle_pairs(puzzle, include_test_answer=False)
        + "\n\nWrong code:\n```python\n" + stripped_wrong + "\n```\n\n"
        "Validation against the wrong code:\n" + feedback
    )


# --- Code extraction + validation (lifted from bulk_collect.py) ---

CODE_FENCE_PY = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
CODE_FENCE_ANY = re.compile(r"```\s*\n(.*?)\n```", re.DOTALL)


def extract_code(text):
    if not text:
        return None
    m = CODE_FENCE_PY.search(text)
    if m:
        return m.group(1)
    m = CODE_FENCE_ANY.search(text)
    if m:
        return m.group(1)
    if "def solve" in text:
        return text[text.index("def solve"):]
    return None


def compare(got, expected):
    if not isinstance(got, list) or not got or not isinstance(got[0], list):
        return None
    if len(got) != len(expected):
        return None
    if any(len(a) != len(b) for a, b in zip(got, expected)):
        return None
    return sum(1 for ra, rb in zip(got, expected) for a, b in zip(ra, rb) if a != b)


def validate(code, puzzle, timeout=20):
    """Run code on every train and test pair, return per-pair results.

    Note: no signal-based timeout because ThreadPoolExecutor workers can't
    install signal handlers (signal only works in main thread). ARC codes
    usually finish in milliseconds; the rare infinite-loop just hangs one
    worker, which we accept.
    """
    pairs = []
    if code is None:
        return pairs, "no code"

    ns = {}
    try:
        exec(code, ns)
    except Exception as e:
        return pairs, f"exec error: {type(e).__name__}: {e}"

    solve = ns.get("solve")
    if not callable(solve):
        return pairs, "no solve() function"

    def run_one(grid, expected, is_train, idx):
        try:
            out = solve([row[:] for row in grid])
        except Exception as e:
            return {"type": "train" if is_train else "test", "idx": idx,
                    "passed": False, "cell_diff": None,
                    "error": f"{type(e).__name__}: {e}"}
        d = compare(out, expected)
        return {"type": "train" if is_train else "test", "idx": idx,
                "passed": d == 0, "cell_diff": d, "error": None}

    for i, p in enumerate(puzzle["train"]):
        pairs.append(run_one(p["input"], p["output"], True, i))
    for i, p in enumerate(puzzle["test"]):
        pairs.append(run_one(p["input"], p["output"], False, i + len(puzzle["train"])))

    return pairs, None


# --- API call ---

def call_model(api_key, base_url, model, messages, temperature, max_retries=3):
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "EMPTY":
        headers["Authorization"] = f"Bearer {api_key}"
    last = None
    for attempt in range(max_retries):
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages, "temperature": temperature},
                timeout=180,
            )
            if r.status_code == 429 or r.status_code >= 500:
                last = f"http {r.status_code}: {r.text[:200]}"
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            d = r.json()
            return {"text": d["choices"][0]["message"]["content"],
                    "usage": d.get("usage")}
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    raise RuntimeError(f"API failed after {max_retries} retries: {last}")


# --- Per-puzzle corrector loop ---

def run_puzzle(api_key, base_url, model, pid, puzzle, run_idx, out_dir,
               temperature, max_rounds):
    """Run the corrector loop for one puzzle (one run-attempt with up to max_rounds)."""
    rec = {
        "puzzle_id": pid, "run_idx": run_idx, "model": model,
        "temperature": temperature, "ts": datetime.now().isoformat(),
        "rounds": [],
    }

    wrong_code = None
    wrong_pairs = None

    for round_idx in range(max_rounds):
        if round_idx == 0:
            prompt = build_d_prompt(puzzle)
            sys_tag = PHASE_D_SYSTEM
        else:
            prompt = build_e_prompt(puzzle, wrong_code, wrong_pairs)
            sys_tag = PHASE_E_SYSTEM

        messages = [
            {"role": "system", "content": sys_tag},
            {"role": "user", "content": prompt},
        ]

        round_rec = {"round": round_idx + 1, "system": sys_tag,
                     "prompt_len": len(prompt)}
        try:
            resp = call_model(api_key, base_url, model, messages, temperature)
            round_rec["response"] = resp["text"]
            round_rec["usage"] = resp["usage"]
        except Exception as e:
            round_rec["error"] = f"api_error: {e}"
            rec["rounds"].append(round_rec)
            rec["bucket"] = "api_error"
            break

        code = extract_code(resp["text"])
        round_rec["code"] = code

        pairs, exec_err = validate(code, puzzle)
        round_rec["pairs"] = pairs
        round_rec["exec_error"] = exec_err

        train_pairs = [p for p in pairs if p["type"] == "train"]
        test_pairs = [p for p in pairs if p["type"] == "test"]
        all_train_pass = train_pairs and all(p["passed"] for p in train_pairs)
        all_test_pass = test_pairs and all(p["passed"] for p in test_pairs)

        round_rec["all_train_pass"] = all_train_pass
        round_rec["all_test_pass"] = all_test_pass
        rec["rounds"].append(round_rec)

        if all_train_pass:
            rec["bucket"] = "correct" if all_test_pass else "wrong_test"
            rec["solved_round"] = round_idx + 1
            break
        else:
            wrong_code = code if code else "# no code produced"
            wrong_pairs = pairs

    else:
        # exhausted all rounds without train-pair pass
        rec["bucket"] = (
            "exec_error" if (rec["rounds"] and rec["rounds"][-1].get("exec_error"))
            else "no_code" if (not rec["rounds"][-1].get("code"))
            else "wrong_training"
        )

    if "bucket" not in rec:
        rec["bucket"] = "wrong_training"

    pid_dir = Path(out_dir) / pid
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / f"run_{run_idx:02d}.json").write_text(json.dumps(rec, indent=2))
    return rec


# --- Main ---

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-base", required=True)
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--splits", required=True)
    ap.add_argument("--puzzle-dir", default=None,
                    help="Single puzzle dir. If omitted, search arc1_train, arc1_eval, arc2_train.")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--max-rounds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    # Load puzzle ids
    splits = json.loads(Path(args.splits).read_text())
    puzzle_ids = splits["puzzle_ids"] if isinstance(splits, dict) else splits

    # Resolve puzzle dirs
    if args.puzzle_dir:
        search_dirs = [args.puzzle_dir]
    else:
        search_dirs = ["data/arc1_train", "data/arc1_eval", "data/arc2_train"]

    puzzle_map = {}
    for d in search_dirs:
        for p in Path(d).glob("*.json"):
            puzzle_map.setdefault(p.stem, json.loads(p.read_text()))

    missing = [pid for pid in puzzle_ids if pid not in puzzle_map]
    if missing:
        print(f"WARNING: {len(missing)} pids not found, skipping. First few: {missing[:5]}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"bulk_collect_runs/corrector_{timestamp}_raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "run_meta.json").write_text(json.dumps({
        "timestamp": timestamp,
        "model": args.model,
        "runs_per_puzzle": args.runs,
        "max_rounds": args.max_rounds,
        "temperature": args.temperature,
        "workers": args.workers,
        "splits": args.splits,
        "puzzle_dir": args.puzzle_dir,
        "puzzle_ids": puzzle_ids,
    }, indent=2))

    tasks = [(pid, run_idx) for pid in puzzle_ids if pid in puzzle_map
             for run_idx in range(args.runs)]
    print(f"[{timestamp}] {len(puzzle_ids)} puzzles x {args.runs} runs (up to {args.max_rounds} rounds each)")
    print(f"out: {out_dir}\n")

    start = time.time()
    counters = {"correct": 0, "wrong_training": 0, "wrong_test": 0,
                "exec_error": 0, "no_code": 0, "api_error": 0}
    solved_by_round = {i + 1: 0 for i in range(args.max_rounds)}

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(run_puzzle, args.api_key, args.api_base, args.model,
                      pid, puzzle_map[pid], run_idx, out_dir,
                      args.temperature, args.max_rounds): (pid, run_idx)
            for pid, run_idx in tasks
        }
        for fut in concurrent.futures.as_completed(futures):
            pid, run_idx = futures[fut]
            completed += 1
            try:
                rec = fut.result()
                b = rec["bucket"]
                counters[b] = counters.get(b, 0) + 1
                if b == "correct":
                    solved_by_round[rec.get("solved_round", 1)] += 1
                solved_at = rec.get("solved_round")
                rounds_used = len(rec.get("rounds", []))
                tag = f"r{solved_at}" if solved_at else f"x{rounds_used}"
                print(f"  [{completed:>4}/{len(tasks)}] {pid} run_{run_idx:02d} -> {b} ({tag})")
            except Exception as e:
                print(f"  [{completed:>4}/{len(tasks)}] {pid} run_{run_idx:02d} -> EXCEPTION: {e}")

    elapsed = time.time() - start

    # Per-puzzle aggregation
    per_puzzle = {}
    for pid in puzzle_ids:
        if pid not in puzzle_map:
            continue
        pid_dir = out_dir / pid
        runs = []
        for f in sorted(pid_dir.glob("run_*.json")):
            runs.append(json.loads(f.read_text()))
        stats = {b: sum(1 for r in runs if r["bucket"] == b) for b in counters}
        stats["total"] = len(runs)
        per_puzzle[pid] = stats

    summary = {
        "meta": {
            "timestamp": timestamp,
            "model": args.model,
            "runs_per_puzzle": args.runs,
            "max_rounds": args.max_rounds,
            "elapsed_sec": round(elapsed, 1),
        },
        "per_puzzle": per_puzzle,
        "overall": {
            "total_runs": completed,
            "buckets": counters,
            "solved_by_round": solved_by_round,
            "pass_at_1_avg": round(counters["correct"] / max(1, completed), 4),
            "puzzles_with_any_correct": sum(1 for s in per_puzzle.values() if s["correct"] > 0),
            "puzzles_total": len(per_puzzle),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print()
    print(f"=== SUMMARY ===")
    print(f"  elapsed: {elapsed:.1f}s")
    print(f"  total runs: {completed}")
    print(f"  correct: {counters['correct']} ({100*counters['correct']/max(1,completed):.1f}% pass@1)")
    print(f"  puzzles solved >=1x: {summary['overall']['puzzles_with_any_correct']} / {len(per_puzzle)}")
    print(f"  buckets: {counters}")
    print(f"  solved-by-round: {solved_by_round}")
    print(f"  -> {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
