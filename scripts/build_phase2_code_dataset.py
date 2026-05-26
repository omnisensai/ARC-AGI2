#!/usr/bin/env python3
"""Phase 2 — T-conditioned code-synthesis dataset.

The same_rule probe showed the model learns the substrate ALPHABET and the
transformation OPERATORS, but fails freehand at EXTENT/boundary control. So we
stop gating on "predict the hidden T" and instead train executable rules:

    visible train pairs (INPUT/OUTPUT/T) + a TEST INPUT  ->  def solve(input_grid)

T is EVIDENCE (what changed, where, which colors), shown only for the demo
pairs. The TEST INPUT is shown alone (no output, no T) — solve() takes only the
grid. The validator (execution vs known outputs) is the authority, not the
substrate.

Targets are the corpus's validated solvers. Per puzzle we emit:
  - leave-one-out variants: each train pair becomes the TEST INPUT once, the
    rest are demos (same target code) -> teaches "code is the invariant".
  - an all-demo variant: all train pairs shown + the real test input.
Pair order is shuffled across variants.

Leak-safe: excludes the 164 forbidden (held-out) ids.

Usage:
  python3 scripts/build_phase2_code_dataset.py --limit 8   # sample
  python3 scripts/build_phase2_code_dataset.py             # full
"""
import argparse, json, glob, os, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from substrate import encode_auto, format_grid          # noqa
from validate_solver import validate_code, load_puzzle  # noqa

FT = ROOT / "Fine Tune Run 2"
CORPUS = ROOT / "research/agent_corpus/by_puzzle"
PUZZLES = FT / "puzzles"
HELDOUT = FT / "puzzles_heldout"
FROZEN = FT / "puzzles_frozen"
OUT = FT / "data_sft/phase2_code_train.jsonl"
MANIFEST = FT / "data_sft/phase2_code_manifest.json"

SYSTEM = (
    "Code Solver.\n"
    "You are given ARC training pairs. For each pair, T marks what changed from "
    "INPUT to OUTPUT (same-size: per-cell, '.'=unchanged, 0-9=new color; "
    "diff-size: an aggregate facts block). T is evidence of the rule, not the answer.\n"
    "Write one Python function `def solve(input_grid):` that implements the single "
    "rule shared by all pairs and returns the OUTPUT for any input of this puzzle.\n"
    "Return ONLY Python. Exactly one function `solve(input_grid)`. Return a non-empty "
    "rectangular list[list[int]] with cells 0-9. Deterministic; no I/O, no prints, no "
    "imports beyond math, collections, itertools, functools, copy, operator, "
    "statistics, heapq, bisect, re. If the output shape differs from the input, compute "
    "the output dimensions first and allocate a new grid; do not start from a copy."
)

def grid_str(g): return "\n".join("".join(str(c) for c in row) for row in g)
def t_text(inp, out):
    s = encode_auto(inp, out)
    return s if isinstance(s, str) else format_grid(s)

def resolve(pid, code):
    """Find the puzzle file whose pairs this solver passes; return (path, puzzle)."""
    cands = []
    rc_file = None
    for d in (PUZZLES, HELDOUT, FROZEN):
        for f in sorted(glob.glob(str(d / (pid + "*.json")))):
            cands.append(f)
    for f in cands:
        try:
            pz = load_puzzle(f)
        except Exception:
            continue
        if validate_code(code, pz)["overall_pass"]:
            return f, pz
    return None, None

def demos_block(pairs, idxs, compact):
    """compact=True (same-size): show INPUT + T only (OUTPUT is recoverable from
    them, lossless -> ~1/3 fewer tokens). compact=False (diff-size): show
    INPUT + OUTPUT + T, since diff-size T is lossy and OUTPUT is needed."""
    parts = []
    for i in idxs:
        p = pairs[i]
        if compact:
            parts.append(f"INPUT:\n{grid_str(p['input'])}\n\nT:\n{t_text(p['input'], p['output'])}")
        else:
            parts.append(f"INPUT:\n{grid_str(p['input'])}\n\nOUTPUT:\n{grid_str(p['output'])}\n\n"
                         f"T:\n{t_text(p['input'], p['output'])}")
    return "\n\n".join(parts)

def make_record(pairs, demo_idxs, code, prov, compact, test_input=None):
    # No TEST OUTPUT ever. all_pairs/subset variants show no test input (pure
    # invariant). pseudo_test shows a held-out pair's INPUT only (matches the
    # competition inference shape: "write code for this unseen input").
    user = demos_block(pairs, demo_idxs, compact)
    if test_input is not None:
        user += f"\n\nTEST INPUT:\n{grid_str(test_input)}"
    user += "\n\nWrite def solve(input_grid):"
    return {"messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": code}],
            "provenance": prov}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--same-only", action="store_true",
                    help="Emit only same-size puzzles (the focused sprint).")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    forbidden = set((FT / "splits/phase2_diffsolver_forbidden.txt").read_text().split())

    files = sorted(glob.glob(str(CORPUS / "*.json")))
    records = []
    stats = {"puzzles_used": 0, "skipped_forbidden": 0, "skipped_nofile": 0,
             "skipped_nocode": 0, "skipped_diff": 0, "skipped_1pair": 0,
             "skipped_memorizer": 0, "same": 0, "diff": 0}
    for cf in files:
        pid = os.path.splitext(os.path.basename(cf))[0]
        if pid in forbidden:
            stats["skipped_forbidden"] += 1; continue
        d = json.load(open(cf))
        rcs = [rc for rc in d.get("right_codes", []) if rc.get("code")]
        if not rcs:
            stats["skipped_nocode"] += 1; continue
        code = rcs[0]["code"]
        # Drop fingerprint-lookup "solvers" that memorize grids instead of the
        # rule: a dict keyed by a frozenset of cell/block positions, returning
        # hardcoded outputs (e.g. 817e6c09). These pass all visible pairs by
        # identity and learn nothing — exactly the anti-generalization pattern we
        # must not teach. Signature validated to match 1/637 with no false hits.
        if "frozenset(" in code and re.search(r"=\s*\{", code) \
                and re.search(r"\b(known_cases|known answer|uniquely identif|hardcod)", code, re.I):
            stats["skipped_memorizer"] += 1; continue
        path, pz = resolve(pid, code)
        if not pz:
            stats["skipped_nofile"] += 1; continue
        # All KNOWN pairs (train + test) are evidence — we have every output in
        # the corpus, and the validated code passes all of them. More pairs = a
        # stronger invariant the one code must satisfy.
        pairs = pz["train"] + pz["test"]
        n = len(pairs)
        same = all(len(p["input"]) == len(p["output"]) and len(p["input"][0]) == len(p["output"][0])
                   for p in pairs)
        if args.same_only and not same:
            stats["skipped_diff"] += 1; continue
        if n < 2:  # one pair underdetermines the rule
            stats["skipped_1pair"] += 1; continue
        compact = same  # same-size: drop OUTPUT (lossless via T). diff-size: keep it.
        stats["same" if same else "diff"] += 1
        stats["puzzles_used"] += 1
        ctid = f"{pid}#0"
        base = {"puzzle_id": pid, "substrate_type": "same" if same else "diff",
                "code_target_id": ctid, "puzzle_file": os.path.basename(path)}
        # 2A all_pairs — show every pair, no test input (pure invariant). 2 shuffles.
        for _ in range(4):
            demo = list(range(n)); rng.shuffle(demo)
            records.append(make_record(pairs, demo, code,
                {**base, "variant": "all_pairs", "visible_pair_indices": demo}, compact))
        # leave-one-out subsets — only when shown subset stays >=2 (n>=3).
        if n >= 3:
            for held in range(n):
                demo = [i for i in range(n) if i != held]; rng.shuffle(demo)
                # 2B subset_cycled — held pair simply absent.
                records.append(make_record(pairs, demo, code,
                    {**base, "variant": "subset_cycled", "visible_pair_indices": demo,
                     "held_out_pair_index": held}, compact))
                # 2C pseudo_test — held pair's INPUT shown as TEST INPUT (no output/T).
                demo2 = demo[:]; rng.shuffle(demo2)
                records.append(make_record(pairs, demo2, code,
                    {**base, "variant": "pseudo_test", "visible_pair_indices": demo2,
                     "held_out_pair_index": held}, compact,
                    test_input=pairs[held]["input"]))
        if args.limit and stats["puzzles_used"] >= args.limit:
            break

    # Drop over-length records BEFORE rebalancing so the mix stays exact on what
    # survives. train_on_inputs:false means trainer truncation eats the trailing
    # tokens — i.e. the ASSISTANT code target — which would teach "emit code,
    # then stop mid-function". ~0.42 tok/char (Qwen BPE on digit grids); the 0.92
    # factor reserves slack for chat-template/role tokens + heuristic error.
    SEQ_LEN, TOK_PER_CHAR = 8192, 0.42
    char_budget = int(SEQ_LEN * 0.92 / TOK_PER_CHAR)
    before = len(records)
    records = [r for r in records
               if sum(len(m["content"]) for m in r["messages"]) <= char_budget]
    stats["skipped_overlen"] = before - len(records)

    # Rebalance toward GPT's 35/40/25 (all_pairs / subset_cycled / pseudo_test),
    # anchored on subset_cycled (the core invariance variant) at 40%.
    by_v = {"all_pairs": [], "subset_cycled": [], "pseudo_test": []}
    for r in records:
        by_v[r["provenance"]["variant"]].append(r)
    anchor = len(by_v["subset_cycled"])
    if anchor:
        total = anchor / 0.40
        tgt = {"all_pairs": int(round(0.35 * total)), "subset_cycled": anchor,
               "pseudo_test": int(round(0.25 * total))}
        records = []
        for v, pool in by_v.items():
            k = min(tgt[v], len(pool))
            records.extend(rng.sample(pool, k) if k < len(pool) else pool)

    rng.shuffle(records)
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # crude token estimate for routing
    lens = [len(r["messages"][1]["content"]) + len(r["messages"][2]["content"]) for r in records]
    lens.sort()
    manifest = {"n_records": len(records), **stats,
                "char_len_p50": lens[len(lens)//2] if lens else 0,
                "char_len_p95": lens[int(len(lens)*0.95)] if lens else 0,
                "char_len_max": lens[-1] if lens else 0}
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
