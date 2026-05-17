"""Merge bulk_collect API run outputs into the per-puzzle agent corpus.

Reads bulk_collect_runs/<ts>_*/<puzzle>/run_NN.json files (or
'research/Bulk Collect/<puzzle>/run_NN.json' once uploaded). For each
puzzle, appends the wrong codes (and any correct ones) into
research/agent_corpus/by_puzzle/<puzzle>.json under wrong_codes/right_codes.

Deduplicates by code-hash so re-running is idempotent. Source attribution
defaults to '<model_basename>_<bucket>' (e.g. 'qwen_baseline').

Usage:
    python3 merge_bulk_collect.py "research/Bulk Collect"
    python3 merge_bulk_collect.py bulk_collect_runs/20260516_172851_raw
    python3 merge_bulk_collect.py <dir> --source-tag qwen_baseline_v2
    python3 merge_bulk_collect.py <dir> --dry-run        # show counts, don't write

Filters:
    --include-buckets wrong_training,wrong_test,exec_error    (default)
    --skip-locked     skip puzzles in splits/baseline_10.json (DO NOT do this:
                      baseline_10 IS where we want Qwen wrong codes for
                      Phase 3 corrector pairs.)
    --skip-correct-as-right   by default we also pull `correct` records into
                              right_codes; pass to skip that.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


DEFAULT_BUCKETS_AS_WRONG = ("wrong_training", "wrong_test", "exec_error")


def code_hash(code: str) -> str:
    """Stable short hash for de-duping codes that are byte-identical."""
    return hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]


def derive_source_tag(model: str, default_tag: str | None) -> str:
    if default_tag:
        return default_tag
    if not model:
        return "bulk_collect"
    # model is like 'qwen/qwen-2.5-7b-instruct' -> 'qwen-2.5-7b-instruct'
    base = model.split("/")[-1] if "/" in model else model
    return base.split(":")[0]


def derive_failure_mode(run: dict) -> str:
    """Plain-English failure-mode description derived from validation result."""
    bucket = run.get("bucket")
    if bucket == "exec_error":
        return f"runtime: code crashed during validation ({run.get('exec_error', 'unknown')})"
    pairs = run.get("pairs", [])
    train = [p for p in pairs if p.get("type") == "train"]
    test = [p for p in pairs if p.get("type") == "test"]
    train_fails = sum(1 for p in train if not p.get("passed"))
    test_fails = sum(1 for p in test if not p.get("passed"))
    train_diff = sum(p.get("cell_diff") or 0 for p in train if not p.get("passed"))
    if bucket == "wrong_training":
        return f"fails {train_fails}/{len(train)} training pairs (total cell-diff {train_diff})"
    if bucket == "wrong_test":
        test_diff = sum(p.get("cell_diff") or 0 for p in test if not p.get("passed"))
        return (f"overfit: passes {len(train)}/{len(train)} training pairs but "
                f"fails {test_fails}/{len(test)} test pairs (total cell-diff {test_diff})")
    return f"bucket={bucket}"


def merge_run_dir(run_dir: Path, corpus_dir: Path,
                  data_dirs: list[Path],
                  source_tag: str | None,
                  buckets_as_wrong: tuple,
                  also_right: bool,
                  dry_run: bool):
    """Walk a bulk_collect run directory, merge into per-puzzle corpus files."""
    # Find puzzle subdirectories (each contains run_NN.json files)
    puzzle_dirs = [p for p in run_dir.iterdir() if p.is_dir() and any(p.glob("run_*.json"))]
    print(f"Found {len(puzzle_dirs)} puzzle dirs under {run_dir}")

    # Build puzzle_id -> path lookup so we can warn if a puzzle isn't in data/
    known_puzzles = set()
    for d in data_dirs:
        for p in Path(d).glob("*.json"):
            known_puzzles.add(p.stem)

    summary = Counter()
    per_puzzle_changes = []

    for pdir in sorted(puzzle_dirs):
        pid = pdir.name

        # Load corpus file (create if missing)
        cf = corpus_dir / f"{pid}.json"
        if cf.exists():
            corpus_rec = json.loads(cf.read_text())
        else:
            if pid not in known_puzzles:
                print(f"  skip {pid}: no puzzle JSON in {data_dirs} and no corpus record")
                summary["skipped_unknown"] += 1
                continue
            corpus_rec = {
                "puzzle_id": pid,
                "source": "arc2_train",  # best guess; can be overridden
                "consensus": None,
                "right_codes": [],
                "wrong_codes": [],
                "judging": None,
            }
        corpus_rec.setdefault("right_codes", [])
        corpus_rec.setdefault("wrong_codes", [])

        existing_right = {code_hash(r["code"]) for r in corpus_rec["right_codes"] if r.get("code")}
        existing_wrong = {code_hash(w["code"]) for w in corpus_rec["wrong_codes"] if w.get("code")}

        added_right = 0
        added_wrong = 0
        skipped_dup = 0
        skipped_other = 0

        for runf in sorted(pdir.glob("run_*.json")):
            run = json.loads(runf.read_text())
            code = run.get("code")
            if not code:
                skipped_other += 1
                continue
            if run.get("puzzle_id") and run["puzzle_id"] != pid:
                # Cross-folder contamination guard (we hit this once when files got mis-uploaded)
                skipped_other += 1
                continue
            h = code_hash(code)
            bucket = run.get("bucket")
            src = derive_source_tag(run.get("model"), source_tag)

            entry = {
                "bucket": bucket,
                "exec_error": run.get("exec_error"),
                "pairs": run.get("pairs", []),
                "code": code,
                "source": src,
            }

            if bucket == "correct":
                if also_right and h not in existing_right:
                    corpus_rec["right_codes"].append(entry)
                    existing_right.add(h)
                    added_right += 1
                else:
                    skipped_dup += 1
            elif bucket in buckets_as_wrong:
                if h not in existing_wrong:
                    entry["failure_mode"] = derive_failure_mode(run)
                    corpus_rec["wrong_codes"].append(entry)
                    existing_wrong.add(h)
                    added_wrong += 1
                else:
                    skipped_dup += 1
            else:
                skipped_other += 1

        per_puzzle_changes.append((pid, added_right, added_wrong, skipped_dup, skipped_other))
        summary["puzzles_touched"] += 1
        summary["right_added"] += added_right
        summary["wrong_added"] += added_wrong
        summary["duplicates_skipped"] += skipped_dup

        if not dry_run and (added_right or added_wrong):
            cf.write_text(json.dumps(corpus_rec, indent=2))

    # Report
    print(f"\n{'puzzle':<12} {'+right':>7} {'+wrong':>7} {'dup':>5} {'other':>6}")
    print("-" * 44)
    for pid, ar, aw, sd, so in per_puzzle_changes:
        print(f"{pid:<12} {ar:>7} {aw:>7} {sd:>5} {so:>6}")

    print(f"\nSummary: {dict(summary)}")
    if dry_run:
        print("\n(--dry-run: no files written)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="bulk_collect run directory (containing <puzzle>/run_NN.json files)")
    ap.add_argument("--corpus-dir", default="research/agent_corpus/by_puzzle")
    ap.add_argument("--data-dirs", nargs="+",
                    default=["data/arc1_train", "data/arc1_eval", "data/arc2_train", "data/arc2_eval"])
    ap.add_argument("--source-tag", default=None,
                    help="Override source field on every appended entry (default: derive from run's 'model' field)")
    ap.add_argument("--include-buckets",
                    default="wrong_training,wrong_test,exec_error",
                    help="Which buckets count as wrong_codes (comma-separated)")
    ap.add_argument("--skip-correct-as-right", action="store_true",
                    help="Don't pull bucket=correct records into right_codes (default: include them)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    merge_run_dir(
        run_dir=Path(args.run_dir),
        corpus_dir=Path(args.corpus_dir),
        data_dirs=[Path(d) for d in args.data_dirs],
        source_tag=args.source_tag,
        buckets_as_wrong=tuple(args.include_buckets.split(",")),
        also_right=not args.skip_correct_as_right,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
