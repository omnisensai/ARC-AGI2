"""Scan the master corpus + Solvers/ + splits/ and produce a status tracker.

Outputs:
    STATUS.md   - human-readable summary + per-puzzle table (committed)
    STATUS.csv  - machine-readable per-puzzle row, easy to open in Numbers/Excel

Run after any corpus change (after merge_bulk_collect, after a fresh agent
batch, after writing a solver). Idempotent and fast — just a scan, no API.

    python3 update_status.py
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from substrate import is_same_size


def collect_status():
    """Return (per_puzzle_rows, summary_counters).

    The locked-eval set is arc2_eval — the official ARC-AGI-2 held-out benchmark.
    No JSON-file-driven lock; the held-out-ness comes from the directory itself
    being excluded from gen_phase1_data.py and build_sft_jsonl.py default inputs.
    """
    # All puzzles on disk (with source attribution)
    sources = [
        ("arc1_train", "data/arc1_train"),
        ("arc1_eval", "data/arc1_eval"),
        ("arc2_train", "data/arc2_train"),
        ("arc2_eval", "data/arc2_eval"),  # LOCKED — official ARC-AGI-2 benchmark
    ]
    all_puzzles = {}  # pid -> {source, same_size, h, w}
    for src_name, src_dir in sources:
        for p in sorted(Path(src_dir).glob("*.json")):
            pid = p.stem
            if pid in all_puzzles:
                continue  # first source wins (consistent with collect_universe)
            puz = json.loads(p.read_text())
            pair = puz["train"][0]
            all_puzzles[pid] = {
                "source": src_name,
                "same_size": is_same_size(puz),
                "h": len(pair["input"]),
                "w": len(pair["input"][0]),
                "n_pairs": len(puz["train"]) + len(puz["test"]),
            }

    # Corpus state
    corpus_dir = Path("research/agent_corpus/by_puzzle")
    corpus_map = {}
    for f in sorted(corpus_dir.glob("*.json")):
        rec = json.loads(f.read_text())
        corpus_map[rec["puzzle_id"]] = rec

    # Solver files
    solver_dir = Path("Solvers")
    solver_to_puzzle = {}
    for f in solver_dir.glob("*.py"):
        # Parse the puzzle id from the module docstring
        head = f.read_text().split("\n", 6)
        for line in head:
            if line.startswith("Puzzle:"):
                pid = line.split(":", 1)[1].strip()
                solver_to_puzzle[pid] = f.name
                break

    rows = []
    for pid, meta in sorted(all_puzzles.items()):
        rec = corpus_map.get(pid, {})
        right_codes = rec.get("right_codes", [])
        wrong_codes = rec.get("wrong_codes", [])
        rights_by_source = Counter(r.get("source", "?") for r in right_codes)
        wrongs_by_source = Counter(w.get("source", "?") for w in wrong_codes)

        consensus = rec.get("consensus") or {}

        # "Locked" now simply means: this puzzle lives in arc2_eval (the held-out
        # benchmark, never trained on). Directory placement is the lock.
        is_locked = meta["source"] == "arc2_eval"
        rows.append({
            "puzzle_id": pid,
            "source": meta["source"],
            "size": f"{meta['h']}x{meta['w']}",
            "same_size": "y" if meta["same_size"] else "n",
            "locked": "y" if is_locked else "",
            "n_right": len(right_codes),
            "n_wrong": len(wrong_codes),
            "right_sources": ",".join(f"{s}:{n}" for s, n in sorted(rights_by_source.items())),
            "wrong_sources": ",".join(f"{s}:{n}" for s, n in sorted(wrongs_by_source.items())),
            "consensus_name": consensus.get("name", ""),
            "solver_file": solver_to_puzzle.get(pid, ""),
            "phase3_pairs": len(right_codes) * len(wrong_codes) if not is_locked else 0,
        })

    # Summary counters
    summary = Counter()
    summary["total_puzzles_on_disk"] = len(all_puzzles)
    summary["locked_eval"] = sum(1 for r in rows if r["locked"])
    summary["same_size_puzzles"] = sum(1 for r in rows if r["same_size"] == "y")
    summary["puzzles_in_corpus"] = len(corpus_map)
    summary["puzzles_with_right_code"] = sum(1 for r in rows if r["n_right"] > 0)
    summary["puzzles_with_wrong_code"] = sum(1 for r in rows if r["n_wrong"] > 0)
    summary["puzzles_with_both"] = sum(1 for r in rows if r["n_right"] > 0 and r["n_wrong"] > 0)
    summary["puzzles_with_solver"] = sum(1 for r in rows if r["solver_file"])
    summary["puzzles_with_consensus"] = sum(1 for r in rows if r["consensus_name"])
    summary["total_right_codes"] = sum(r["n_right"] for r in rows)
    summary["total_wrong_codes"] = sum(r["n_wrong"] for r in rows)
    summary["total_phase3_pairs_available"] = sum(r["phase3_pairs"] for r in rows)

    return rows, summary


def write_csv(rows, path: Path):
    fieldnames = ["puzzle_id", "source", "size", "same_size", "locked",
                  "n_right", "n_wrong", "right_sources", "wrong_sources",
                  "consensus_name", "solver_file", "phase3_pairs"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_markdown(rows, summary, path: Path):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Per-source bucket counts
    sources = sorted({r["source"] for r in rows})
    source_table = []
    for src in sources:
        src_rows = [r for r in rows if r["source"] == src]
        source_table.append({
            "source": src,
            "total": len(src_rows),
            "same_size": sum(1 for r in src_rows if r["same_size"] == "y"),
            "locked": sum(1 for r in src_rows if r["locked"]),
            "in_corpus": sum(1 for r in src_rows if r["n_right"] + r["n_wrong"] > 0),
            "has_right": sum(1 for r in src_rows if r["n_right"] > 0),
            "has_wrong": sum(1 for r in src_rows if r["n_wrong"] > 0),
            "has_solver": sum(1 for r in src_rows if r["solver_file"]),
        })

    # To-do lists (locked = arc2_eval rows; we never collect right_codes for those)
    needs_wrong = sorted(r["puzzle_id"] for r in rows
                         if r["n_right"] > 0 and r["n_wrong"] == 0 and not r["locked"])
    needs_right = sorted(r["puzzle_id"] for r in rows
                         if r["n_wrong"] > 0 and r["n_right"] == 0 and not r["locked"])
    needs_consensus = sorted(r["puzzle_id"] for r in rows
                             if r["n_right"] > 0 and not r["consensus_name"])
    needs_solver = sorted(r["puzzle_id"] for r in rows
                          if r["consensus_name"] and not r["solver_file"])

    # Active puzzles only (in corpus)
    active = [r for r in rows if r["n_right"] + r["n_wrong"] > 0]

    lines = [
        f"# Pipeline Status",
        f"",
        f"Auto-generated by `update_status.py` — `{ts}`",
        f"",
        f"## Big numbers",
        f"",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Total puzzles on disk | {summary['total_puzzles_on_disk']} |",
        f"| Same-size puzzles | {summary['same_size_puzzles']} |",
        f"| Locked eval (never train on these) | {summary['locked_eval']} |",
        f"| Puzzles in corpus | {summary['puzzles_in_corpus']} |",
        f"| Puzzles with at least 1 right_code | {summary['puzzles_with_right_code']} |",
        f"| Puzzles with at least 1 wrong_code | {summary['puzzles_with_wrong_code']} |",
        f"| **Puzzles with both (Phase 3 ready)** | **{summary['puzzles_with_both']}** |",
        f"| Puzzles with judge consensus name | {summary['puzzles_with_consensus']} |",
        f"| Puzzles with solver file | {summary['puzzles_with_solver']} |",
        f"| Total right_codes collected | {summary['total_right_codes']} |",
        f"| Total wrong_codes collected | {summary['total_wrong_codes']} |",
        f"| **Phase 3 training pairs available** (sum of right×wrong per non-locked puzzle) | **{summary['total_phase3_pairs_available']}** |",
        f"",
        f"## By source",
        f"",
        f"| Source | Total | Same-size | Locked | In corpus | Has right | Has wrong | Has solver |",
        f"|---|---|---|---|---|---|---|---|",
    ]
    for s in source_table:
        lines.append(f"| {s['source']} | {s['total']} | {s['same_size']} | "
                     f"{s['locked']} | {s['in_corpus']} | {s['has_right']} | "
                     f"{s['has_wrong']} | {s['has_solver']} |")

    lines += [
        f"",
        f"## To-do queues",
        f"",
        f"### Needs wrong_codes ({len(needs_wrong)})",
        f"Right code exists but no Qwen wrong codes yet. Run `bulk_collect.py` on these.",
        f"",
    ]
    if needs_wrong:
        lines.append("```\n" + "\n".join(needs_wrong) + "\n```")
    else:
        lines.append("_(none — all non-locked puzzles with right_codes also have wrong_codes)_")

    lines += [
        f"",
        f"### Needs right_codes ({len(needs_right)})",
        f"Wrong codes exist but no correct solution. Run agent batches or manual paste.",
        f"",
    ]
    if needs_right:
        lines.append("```\n" + "\n".join(needs_right) + "\n```")
    else:
        lines.append("_(none)_")

    lines += [
        f"",
        f"### Needs judge consensus ({len(needs_consensus)})",
        f"Has right code(s) but no canonical rule name yet. Run 5-judge round.",
        f"",
    ]
    if needs_consensus:
        lines.append("```\n" + "\n".join(needs_consensus) + "\n```")
    else:
        lines.append("_(none)_")

    lines += [
        f"",
        f"### Needs solver file ({len(needs_solver)})",
        f"Has consensus name but no Solvers/<name>.py yet.",
        f"",
    ]
    if needs_solver:
        lines.append("```\n" + "\n".join(needs_solver) + "\n```")
    else:
        lines.append("_(none)_")

    lines += [
        f"",
        f"## Active puzzles ({len(active)})",
        f"",
        f"All puzzles currently in the corpus. Sort: by puzzle_id.",
        f"",
        f"| Puzzle | Source | Size | Lock | R | W | Phase3 | Consensus | Solver |",
        f"|---|---|---|---|---|---|---|---|---|",
    ]
    for r in active:
        lock = "🔒" if r["locked"] else ""
        consensus = r["consensus_name"] or ""
        solver = "✅" if r["solver_file"] else ""
        lines.append(f"| `{r['puzzle_id']}` | {r['source']} | {r['size']} | "
                     f"{lock} | {r['n_right']} | {r['n_wrong']} | {r['phase3_pairs']} | "
                     f"{consensus} | {solver} |")

    lines += [
        f"",
        f"---",
        f"Full per-puzzle data including source attribution is in `STATUS.csv`.",
        f"",
    ]

    path.write_text("\n".join(lines))


def main():
    rows, summary = collect_status()
    write_csv(rows, Path("STATUS.csv"))
    write_markdown(rows, summary, Path("STATUS.md"))
    print(f"Wrote STATUS.csv ({len(rows)} rows) and STATUS.md")
    print(f"Summary: {dict(summary)}")


if __name__ == "__main__":
    main()
