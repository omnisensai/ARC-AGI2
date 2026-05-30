"""Empirical primitive catalog — derived from canonical solvers, not guessed.

Static-analyses each canonical solver in Phase2_V2/canonical/solvers/*.py to
extract structural feature signatures (patterns/idioms the solver uses), then
clusters solvers by signature. Each cluster ≈ one empirical primitive.

Output: canonical/empirical_catalog.md with:
  - HEAD: clusters of size > 1 (shared primitives across puzzles)
  - TAIL: clusters of size 1 (one-offs — human review queue)
  - Stats: # primitives, head coverage, etc.

Feature detection is by substring/regex — approximate but stable. Clusters
group solvers with identical feature signatures.

No assumption about WHAT primitives should exist — derived from the code.
"""
import re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLVERS_DIR = ROOT / "canonical" / "solvers"
OUTPUT_FILE = ROOT / "canonical" / "empirical_catalog.md"


# ---------- feature detectors ------------------------------------------
# Each returns True if the pattern is present in the code text.

# Code-only patterns: features detect ACTUAL CODE STRUCTURE, not docstring keywords.
# All comments and string literals are stripped before matching.

FEATURES = {
    # ---- background / colour analysis ----
    "BG_COUNTER":      lambda c: "most_common" in c or "key=counts.get" in c or re.search(r'max\(counts,\s*key=counts\.get\)', c) is not None,
    "COUNTER_LIB":     lambda c: "Counter(" in c,

    # ---- traversal / connectivity ----
    "QUEUE_BFS":       lambda c: "deque" in c and "popleft" in c,
    "STACK_DFS":       lambda c: re.search(r'stack\.pop\(\)', c) is not None or re.search(r'stack = \[\]', c) is not None,
    "CONN4_TUPLE":     lambda c: re.search(r'\(1,\s*0\)\s*,\s*\(-1,\s*0\)\s*,\s*\(0,\s*1\)\s*,\s*\(0,\s*-1\)', c) is not None,
    "CONN8_TUPLE":     lambda c: ("(1, 1)" in c or "(1,1)" in c) and ("(-1, -1)" in c or "(-1,-1)" in c) and ("(1, -1)" in c or "(1,-1)" in c),

    # ---- geometry over cell sets ----
    "BBOX":            lambda c: ("min(r " in c or "min(r," in c) and ("max(r " in c or "max(r," in c) and ("min(c " in c or "min(c," in c),
    "FRAME_PERIMETER": lambda c: re.search(r'\[\s*r0\s*\]\s*\[\s*c\s*\]', c) is not None and re.search(r'\[\s*r1\s*\]\s*\[\s*c\s*\]', c) is not None,

    # ---- whole-grid geometry ----
    "HFLIP_IDX":       lambda c: re.search(r'\[\s*W\s*-\s*1\s*-\s*c\s*\]', c) is not None,
    "VFLIP_IDX":       lambda c: re.search(r'\[\s*H\s*-\s*1\s*-\s*r\s*\]', c) is not None,
    "ROT90_IDX":       lambda c: re.search(r'\[\s*H\s*-\s*1\s*-\s*\w+\s*\]\s*\[\s*\w+\s*\]', c) is not None,
    "SCALE_DIV":       lambda c: re.search(r'\[\s*[rc]\s*//\s*\d+\s*\]', c) is not None,

    # ---- periodicity ----
    "GCD":             lambda c: "gcd" in c,
    "MOD_PERIOD":      lambda c: re.search(r'%\s*p[rc]\b', c) is not None or re.search(r'\(r\s*%\s*\w+\s*,\s*c\s*%\s*\w+\)', c) is not None,
    "DIAG_RESIDUE":    lambda c: re.search(r'\(r\s*[+-]\s*c\)\s*%', c) is not None,

    # ---- ray / step traversal ----
    "RAY_STEP":        lambda c: re.search(r'\+=\s*dr\b', c) is not None and re.search(r'\+=\s*dc\b', c) is not None,

    # ---- selection / ordering ----
    "MAX_BY_LEN":      lambda c: re.search(r'max\(\s*\w+\s*,\s*key\s*=\s*len\s*\)', c) is not None,

    # ---- border iteration (flood-from-border pattern) ----
    "BORDER_LOOP":     lambda c: (re.search(r'for\s+\w+\s+in\s+\(\s*0\s*,\s*[HW]\s*-\s*1\s*\)', c) is not None
                                  or re.search(r'r\s+in\s+\(\s*0\s*,\s*H\s*-\s*1\s*\)', c) is not None
                                  or "for c in (0, W - 1)" in c
                                  or "for r in (0, H - 1)" in c),

    # ---- block / fractal indexing ----
    "BLOCK_INDEX":     lambda c: re.search(r'\[\s*[Rr]\s*\*\s*H\s*\+', c) is not None or re.search(r'R\s*\*\s*H', c) is not None,

    # ---- shape lookup / fingerprint table ----
    "FROZENSET_KEY":   lambda c: "frozenset(" in c,
    "TUPLE_NORMALIZE": lambda c: re.search(r'tuple\(\s*sorted\(', c) is not None,

    # ---- mirror via paired indexing ----
    "PAIRED_MIRROR":   lambda c: re.search(r'g\[\s*r\s*\]\[\s*mc\s*\]', c) is not None or re.search(r'g\[\s*mr\s*\]\[\s*c\s*\]', c) is not None,

    # ---- sandwich / between collinear pair ----
    "BETWEEN_PAIR":    lambda c: re.search(r'\(r1\s*[-+]\s*r0|r2\s*-\s*r1\)', c) is not None and ("dr" in c and "dc" in c) and "in_between" in c.lower() if False else (
                                  re.search(r'between', c) is not None and "collinear" in c.lower() if False else False),
    "STEPS_DIRECTION": lambda c: re.search(r'sr\s*,\s*sc\s*=', c) is not None and re.search(r'\+\s*sr\s*\*', c) is not None,

    # ---- column / row settling (gravity-like) ----
    "COL_SETTLE":      lambda c: re.search(r'for\s+c\s+in\s+range\(W\):', c) is not None and re.search(r'g\[r\]\[c\]', c) is not None and "stack" in c.lower() and "col" in c.lower(),
}


_TRIPLE_DOC = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'')
_LINE_COMMENT = re.compile(r'#.*')
_STRING_LIT = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')


def strip_docs_and_strings(code):
    """Remove docstrings, line comments, and string literals so feature
    detection only sees real code structure."""
    s = _TRIPLE_DOC.sub('', code)
    s = _LINE_COMMENT.sub('', s)
    s = _STRING_LIT.sub('""', s)
    return s


def feature_signature(code):
    stripped = strip_docs_and_strings(code)
    return frozenset(name for name, test in FEATURES.items() if test(stripped))


# ---------- heuristic names for common signatures ----------------------

NAME_MAP = {
    frozenset({"BG_COUNTER", "QUEUE_BFS", "CONN4_TUPLE", "MAX_BY_LEN"}):           "keep_largest_4conn_component",
    frozenset({"BG_COUNTER", "QUEUE_BFS", "CONN8_TUPLE", "MAX_BY_LEN"}):           "keep_largest_8conn_component",
    frozenset({"BG_COUNTER", "QUEUE_BFS", "CONN4_TUPLE"}):                          "components_4conn",
    frozenset({"BG_COUNTER", "QUEUE_BFS", "CONN8_TUPLE"}):                          "components_8conn",
    frozenset({"BG_COUNTER", "STACK_DFS", "BORDER_LOOP"}):                                    "flood_from_border_dfs",
    frozenset({"BG_COUNTER", "QUEUE_BFS", "BORDER_LOOP", "CONN4_TUPLE"}):                     "fill_enclosed_4conn",
    frozenset({"BG_COUNTER", "RAY_STEP"}):                                                    "ray_tracing",
    frozenset({"BG_COUNTER", "GCD", "MOD_PERIOD"}):                                           "periodic_repair_2d",
    frozenset({"BG_COUNTER", "GCD"}):                                                         "periodic_extension_1d",
    frozenset({"BG_COUNTER", "DIAG_RESIDUE"}):                                                "diagonal_residue_class",
    frozenset({"BG_COUNTER", "HFLIP_IDX"}):                                                   "horizontal_flip",
    frozenset({"BG_COUNTER", "VFLIP_IDX"}):                                                   "vertical_flip",
    frozenset({"BG_COUNTER", "PAIRED_MIRROR"}):                                               "symmetry_complete",
    frozenset({"BG_COUNTER", "BBOX", "FRAME_PERIMETER"}):                                     "draw_bbox_perimeter",
    frozenset({"BG_COUNTER", "BLOCK_INDEX"}):                                                 "fractal_or_block_tiling",
    frozenset({"FROZENSET_KEY", "TUPLE_NORMALIZE"}):                                          "shape_lookup_fingerprint",
    frozenset({"BG_COUNTER", "FROZENSET_KEY", "TUPLE_NORMALIZE"}):                            "shape_lookup_fingerprint",
    frozenset({"BG_COUNTER", "STEPS_DIRECTION"}):                                             "sandwich_fill_pairs",
    frozenset({"BG_COUNTER", "SCALE_DIV"}):                                                   "scale_by_div_index",
    frozenset({"BG_COUNTER", "ROT90_IDX"}):                                                   "rotate_90",
}


def name_for(sig):
    return NAME_MAP.get(sig, "+".join(sorted(sig)) if sig else "trivial_no_features")


# ---------- main -------------------------------------------------------

def main():
    if not SOLVERS_DIR.exists():
        print(f"Error: {SOLVERS_DIR} not found"); sys.exit(1)

    solvers = sorted(SOLVERS_DIR.glob("*.py"))
    print(f"Analyzing {len(solvers)} canonical solvers …")

    buckets = defaultdict(list)
    for path in solvers:
        pid = path.stem
        code = path.read_text(errors="replace")
        sig = feature_signature(code)
        buckets[sig].append(pid)

    items = sorted(buckets.items(), key=lambda kv: -len(kv[1]))
    # head = primitive clusters with >1 puzzles AND at least 1 detected feature
    # unclustered = the empty-signature bucket (no structural features matched)
    # tail = unique signatures (1 puzzle, ≥1 feature)
    head = [(s, p) for s, p in items if len(p) > 1 and len(s) > 0]
    unclustered = [(s, p) for s, p in items if len(s) == 0]
    tail = [(s, p) for s, p in items if len(p) == 1 and len(s) > 0]
    head_pids = sum(len(p) for _, p in head)
    unclustered_pids = sum(len(p) for _, p in unclustered)
    tail_pids = sum(len(p) for _, p in tail)

    with OUTPUT_FILE.open("w") as f:
        f.write("# Empirical Primitive Catalog\n\n")
        f.write(f"Derived from static analysis of **{len(solvers)} canonical solvers** in `canonical/solvers/`.\n\n")
        f.write("Each cluster groups solvers that share a structural feature signature ")
        f.write("(BFS, 4- vs 8-connectivity, flood-from-border, ray tracing, bbox, period, "
                "flip, fractal, etc.). Clusters approximate the **empirical primitives real ARC uses** — "
                "no assumption about what should exist, derived from the code.\n\n")
        f.write("Detection is by substring/regex match. Approximate but stable; mis-matches "
                "should be rare and self-flagging (puzzles in the tail).\n\n")
        f.write("---\n\n")
        f.write(f"## Stats\n\n")
        f.write(f"- Total solvers analyzed:           **{len(solvers)}**\n")
        f.write(f"- Distinct feature signatures:      **{len(buckets)}**\n")
        f.write(f"- HEAD primitive clusters (≥2):     **{len(head)}** covering **{head_pids}** puzzles ({100*head_pids/len(solvers):.1f}%)\n")
        f.write(f"- UNCLUSTERED (no detected struct): **{unclustered_pids}** puzzles ({100*unclustered_pids/len(solvers):.1f}%) — hand-crafted or analyzer-missed\n")
        f.write(f"- TAIL (unique signature, 1 puzzle):**{len(tail)}** puzzles ({100*tail_pids/len(solvers):.1f}%) — candidate new primitives or rare patterns\n\n")
        f.write("---\n\n")

        f.write(f"## HEAD — shared primitives\n\n")
        f.write(f"_{len(head)} clusters covering {head_pids} puzzles._\n\n")
        for sig, pids in head:
            n = len(pids)
            label = name_for(sig)
            f.write(f"### `{label}`  —  **{n}** puzzles\n")
            f.write(f"**Features**: `{', '.join(sorted(sig)) if sig else '(none)'}`\n\n")
            shown = pids[:25]
            extra = n - len(shown)
            f.write(f"**Puzzles**: {', '.join(shown)}")
            f.write(f" … (+{extra} more)" if extra > 0 else "")
            f.write("\n\n")

        f.write("---\n\n")
        f.write(f"## UNCLUSTERED — no structural features detected\n\n")
        f.write(f"_{unclustered_pids} puzzles. These solvers don't use the patterns the analyzer recognizes ")
        f.write(f"(BFS, ray, bbox, mirror, period, fractal, etc.). Could be:_\n")
        f.write(f"_- bespoke per-puzzle rules (real tail of the substrate)_\n")
        f.write(f"_- patterns the analyzer missed (refine features and re-run)_\n\n")
        for sig, pids in unclustered:
            f.write(f"<details><summary>{len(pids)} puzzles</summary>\n\n")
            for p in pids:
                f.write(f"- `{p}`\n")
            f.write("\n</details>\n")

        f.write("\n---\n\n")
        f.write(f"## TAIL — unique signatures (your review queue)\n\n")
        f.write(f"_{len(tail)} puzzles with a structural signature unique to them. ")
        f.write(f"Each is a candidate new primitive, or a rare composition. Review each, decide._\n\n")
        for sig, pids in tail:
            pid = pids[0]
            f.write(f"- `{pid}` — features: `{', '.join(sorted(sig))}`\n")

    # console summary
    print(f"\nWrote {OUTPUT_FILE}")
    print(f"  signatures: {len(buckets)}")
    print(f"  HEAD primitive clusters: {len(head)}  covering {head_pids}/{len(solvers)} = {100*head_pids/len(solvers):.1f}%")
    print(f"  UNCLUSTERED (no features): {unclustered_pids} ({100*unclustered_pids/len(solvers):.1f}%)")
    print(f"  TAIL (unique sigs):        {len(tail)} ({100*tail_pids/len(solvers):.1f}%)")
    print(f"\nTop 15 HEAD clusters by size:")
    for sig, pids in head[:15]:
        print(f"  {len(pids):4d}  {name_for(sig):42s}  features={sorted(sig)}")


if __name__ == "__main__":
    main()
