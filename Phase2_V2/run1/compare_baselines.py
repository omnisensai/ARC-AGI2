"""Side-by-side baseline comparison.

Reads two JSONLs (e.g. base Qwen vs Coder) and emits a markdown dump
showing, for each puzzle: the expected output grid, what each model
generated (raw + extracted code + got_output), and their failure modes.

Usage:
    python3 Phase2_V2/run1/compare_baselines.py \\
        --a Phase2_V2/run1/eval/baseline_qwen25_7b.jsonl \\
        --b Phase2_V2/run1/eval/baseline_coder-7b-instruct.jsonl \\
        --out Phase2_V2/run1/eval/compare_base_vs_coder.md \\
        --limit 20
"""
import argparse, json
from pathlib import Path


def grid_str(g):
    if g is None:
        return "(none)"
    if not isinstance(g, list) or not g or not isinstance(g[0], list):
        return f"(not a grid: {type(g).__name__})"
    return "\n".join("".join(str(c) for c in row) for row in g)


def load(path, limit):
    recs = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        recs.append(json.loads(line))
        if limit and len(recs) >= limit:
            break
    return {r["puzzle"]: r for r in recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="JSONL for model A")
    ap.add_argument("--b", required=True, help="JSONL for model B")
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a_label = args.label_a or Path(args.a).stem
    b_label = args.label_b or Path(args.b).stem

    a = load(args.a, args.limit)
    b = load(args.b, args.limit)
    common = [p for p in a if p in b][:args.limit]

    out = []
    out.append(f"# Baseline comparison: {a_label} vs {b_label}")
    out.append("")
    out.append(f"- A = `{args.a}` ({len(a)} records)")
    out.append(f"- B = `{args.b}` ({len(b)} records)")
    out.append(f"- Compared on {len(common)} puzzles\n")

    # Tally
    from collections import Counter
    ta = Counter(a[p]["failure_mode"] for p in common)
    tb = Counter(b[p]["failure_mode"] for p in common)
    out.append("## Failure-mode tally\n")
    out.append(f"| mode | A: {a_label} | B: {b_label} |")
    out.append("|---|---:|---:|")
    for mode in sorted(set(ta) | set(tb)):
        out.append(f"| {mode} | {ta.get(mode,0)} | {tb.get(mode,0)} |")
    out.append("")

    # Per-puzzle
    out.append("## Per-puzzle breakdown\n")
    for pid in common:
        ra, rb = a[pid], b[pid]
        out.append(f"### {pid}\n")
        out.append(f"**A ({a_label}):** {ra['failure_mode']}   "
                   f"**B ({b_label}):** {rb['failure_mode']}\n")
        out.append("**Expected output:**\n```\n" + grid_str(ra["expected_output"]) + "\n```\n")
        out.append(f"**A got:**\n```\n{grid_str(ra.get('got_output'))}\n```\n")
        out.append(f"**B got:**\n```\n{grid_str(rb.get('got_output'))}\n```\n")
        out.append(f"**A extracted code:**\n```python\n{ra.get('extracted_code','')}\n```\n")
        out.append(f"**B extracted code:**\n```python\n{rb.get('extracted_code','')}\n```\n")
        out.append("**A raw output (full):**\n```\n"
                   + ra.get('model_output_raw','') + "\n```\n")
        out.append("**B raw output (full):**\n```\n"
                   + rb.get('model_output_raw','') + "\n```\n")
        out.append("---\n")

    Path(args.out).write_text("\n".join(out))
    print(f"wrote {args.out}  ({len(common)} puzzles)")


if __name__ == "__main__":
    main()
