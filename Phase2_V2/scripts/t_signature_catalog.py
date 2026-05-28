"""Empirical catalog v2 — cluster by T-GRID PATTERN, not by code style.

For each canonical puzzle (using its ground-truth train pairs), compute the T
per pair, extract a topological signature of the *change pattern*, and cluster.

Same operation -> same T-signature, regardless of solver implementation.
Invariants (.) are ignored by construction — T only contains the operation.

This is the MECE classification: T captures the operation; everything else is
surface variation.

Signature: (size_change, density_band, polarity_bias, topology, n_components_band)
"""
import json, sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GT_DIR = ROOT / "canonical" / "ground_truth_puzzles"
OUTPUT_FILE = ROOT / "canonical" / "t_signature_catalog.md"


def compute_T(inp, out):
    """Per-cell diff: dict (r,c) -> new_value where inp != out."""
    H, W = len(inp), len(inp[0])
    return {(r, c): out[r][c] for r in range(H) for c in range(W) if inp[r][c] != out[r][c]}


def bg_of(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def t_signature(inp, out):
    """Extract a discrete signature from the (input, output) pair's T."""
    H_in, W_in = len(inp), len(inp[0])
    H_out, W_out = len(out), len(out[0])
    if (H_in, W_in) != (H_out, W_out):
        return ("DIFF_SIZE", f"{H_in}x{W_in}->{H_out}x{W_out}", None, None, None)

    T = compute_T(inp, out)
    n_cells = H_in * W_in
    if n_cells == 0:
        return ("SAME", "NO_CHANGE", "NONE", "EMPTY", "0")

    n_changed = len(T)
    pct = n_changed / n_cells

    # density band
    if   n_changed == 0: density = "NO_CHANGE"
    elif pct < 0.02:     density = "TINY"          # <2%   (1-2 cells in a small grid)
    elif pct < 0.10:     density = "SPARSE"        # 2-10%
    elif pct < 0.30:     density = "MEDIUM"        # 10-30%
    elif pct < 0.70:     density = "DENSE"         # 30-70%
    else:                density = "TOTAL"         # 70%+

    # polarity
    bg = bg_of(inp)
    n_add = n_remove = n_recolor = 0
    for (r, c), v in T.items():
        old = inp[r][c]
        if old == bg and v != bg:    n_add += 1
        elif old != bg and v == bg:  n_remove += 1
        else:                         n_recolor += 1
    total = max(n_add + n_remove + n_recolor, 1)
    if   n_add     / total > 0.7: polarity = "ADD"        # paint cells (frame, fill, draw)
    elif n_remove  / total > 0.7: polarity = "REMOVE"     # erase cells (hollow, delete)
    elif n_recolor / total > 0.7: polarity = "RECOLOR"    # change colors
    elif n_add > 0 and n_remove > 0 and n_recolor < n_add + n_remove:
        polarity = "MOVE"                                  # erase + paint (translation, drop)
    else:                          polarity = "MIXED"

    # topology of changed cells (4-conn components)
    changed = set(T.keys())
    seen = set()
    comp_sizes = []
    for cell in changed:
        if cell in seen: continue
        q = deque([cell]); seen.add(cell); size = 0
        while q:
            r, c = q.popleft(); size += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) in changed and (nr, nc) not in seen:
                    seen.add((nr, nc)); q.append((nr, nc))
        comp_sizes.append(size)

    n_comps = len(comp_sizes)
    if   n_comps == 0:                              topology = "EMPTY"
    elif n_comps == 1:                              topology = "ONE_BLOB"
    elif all(s == 1 for s in comp_sizes):           topology = "ISOLATED_CELLS"
    elif n_comps <= 3:                              topology = "FEW_BLOBS"
    elif n_comps <= 8:                              topology = "MULTI_BLOBS"
    else:                                            topology = "MANY_SCATTERED"

    # n_components band (separate for clustering granularity)
    if   n_comps == 0:  comps_band = "0"
    elif n_comps == 1:  comps_band = "1"
    elif n_comps <= 3:  comps_band = "2-3"
    elif n_comps <= 8:  comps_band = "4-8"
    else:                comps_band = "9+"

    return ("SAME", density, polarity, topology, comps_band)


def puzzle_signature(puzzle):
    """Aggregate over train pairs. If pairs disagree, take the modal signature."""
    pairs = puzzle.get('train', [])
    if not pairs:
        return ("EMPTY",)
    sigs = [t_signature(p['input'], p['output']) for p in pairs]
    return Counter(sigs).most_common(1)[0][0]


def main():
    if not GT_DIR.exists():
        print(f"Error: {GT_DIR} not found"); sys.exit(1)

    files = sorted(GT_DIR.glob("*.json"))
    print(f"Analyzing T-signatures of {len(files)} canonical puzzles ...")

    buckets = defaultdict(list)
    for f in files:
        puzzle = json.loads(f.read_text())
        buckets[puzzle_signature(puzzle)].append(f.stem)

    sorted_buckets = sorted(buckets.items(), key=lambda kv: -len(kv[1]))

    with OUTPUT_FILE.open("w") as f:
        f.write("# T-Signature Catalog\n\n")
        f.write(f"Clustering of **{len(files)} canonical puzzles** by their T-GRID PATTERN ")
        f.write("(input → output diff), not by solver code style.\n\n")
        f.write("**Same operation = same T-signature**, regardless of code, colors, grid size, ")
        f.write("or positions. Invariants (`.`) are ignored by construction.\n\n")
        f.write("Signature schema: `(size_change, density, polarity, topology, n_components)`\n\n")
        f.write("- **size_change**: SAME / DIFF_SIZE  (output dims same as input or different)\n")
        f.write("- **density**: % of cells changed — NO_CHANGE / TINY / SPARSE / MEDIUM / DENSE / TOTAL\n")
        f.write("- **polarity**: ADD (bg→colour) / REMOVE (colour→bg) / RECOLOR / MOVE (add+remove) / MIXED\n")
        f.write("- **topology**: connected-component shape of changed cells — ONE_BLOB / FEW_BLOBS / MULTI_BLOBS / ISOLATED_CELLS / MANY_SCATTERED / EMPTY\n")
        f.write("- **n_components**: 0 / 1 / 2-3 / 4-8 / 9+\n\n")
        f.write("---\n\n## Stats\n\n")
        f.write(f"- Puzzles analyzed: **{len(files)}**\n")
        f.write(f"- Distinct T-signatures: **{len(buckets)}**\n")
        head = [(s, p) for s, p in sorted_buckets if len(p) > 1]
        head_pids = sum(len(p) for _, p in head)
        tail = [(s, p) for s, p in sorted_buckets if len(p) == 1]
        f.write(f"- Head (clusters ≥ 2):  **{len(head)}** clusters covering **{head_pids}** puzzles ({100*head_pids/len(files):.1f}%)\n")
        f.write(f"- Tail (1 puzzle):      **{len(tail)}** puzzles ({100*len(tail)/len(files):.1f}%)\n\n")
        f.write("---\n\n## Clusters (largest first)\n\n")
        for sig, pids in sorted_buckets:
            sig_str = " | ".join(str(s) for s in sig)
            f.write(f"### `({sig_str})` — {len(pids)} puzzles\n\n")
            shown = pids[:25]
            extra = len(pids) - len(shown)
            f.write(", ".join(f"[`{p}`](https://arcprize.org/tasks/{p})" for p in shown))
            if extra > 0:
                f.write(f" … (+{extra} more)")
            f.write("\n\n")

    print(f"\nWrote {OUTPUT_FILE}")
    print(f"  distinct T-signatures: {len(buckets)}")
    print(f"  head ≥2: {len(head)} clusters covering {head_pids}/{len(files)} = {100*head_pids/len(files):.1f}%")
    print(f"  tail =1: {len(tail)}\n")
    print(f"Top 20 clusters by size:")
    for sig, pids in sorted_buckets[:20]:
        sig_str = " | ".join(str(s) for s in sig)
        print(f"  {len(pids):4d}  ({sig_str})")


if __name__ == "__main__":
    main()
