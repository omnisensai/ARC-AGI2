"""Canonical solver for ARC puzzle 79369cc6.

Rule
----
The grid contains exactly one 3x3 "key": a block made only of colors 4 and 6
(4 appears nowhere else in the input). The key encodes a stamp: the cells that
are 6 form a fixed connected shape, and the cells that are 4 mark how that shape
should be "completed" with color 4.

Elsewhere in the grid the same 6-shape occurs (possibly rotated/reflected, and
possibly running off the grid edge). At every such occurrence we stamp the key:
the cells aligned with the key's 4-cells are overwritten with 4 (the 6-cells are
left untouched). The original key block is left as-is.

T is the latent dict-mask {(r,c): 4} of cells to recolor.
"""


def _find_key(grid):
    """Bounding box of the 4-cells = the 3x3 key block."""
    H, W = len(grid), len(grid[0])
    fours = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 4]
    if not fours:
        return None, None
    rs = [r for r, _ in fours]
    cs = [c for _, c in fours]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    key = [grid[r][c0:c1 + 1] for r in range(r0, r1 + 1)]
    return key, (r0, c0)


def _orientations(grid):
    """All 8 dihedral transforms (deduplicated)."""
    def rot(g):
        return [list(row) for row in zip(*g[::-1])]

    def refl(g):
        return [row[::-1] for row in g]

    outs = []
    g = [row[:] for row in grid]
    for _ in range(4):
        outs.append([row[:] for row in g])
        outs.append(refl(g))
        g = rot(g)
    uniq, seen = [], set()
    for o in outs:
        t = tuple(tuple(r) for r in o)
        if t not in seen:
            seen.add(t)
            uniq.append(o)
    return uniq


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    key, key_origin = _find_key(input_grid)
    T = {}
    if key is None:
        return T
    kr0, kc0 = key_origin
    kh, kw = len(key), len(key[0])

    for ori in _orientations(key):
        oh, ow = len(ori), len(ori[0])
        six = [(r, c) for r in range(oh) for c in range(ow) if ori[r][c] == 6]
        four = [(r, c) for r in range(oh) for c in range(ow) if ori[r][c] == 4]
        if not six:
            continue
        # Try every placement, allowing the stamp to hang off the grid edges.
        for tr in range(-oh + 1, H):
            for tc in range(-ow + 1, W):
                # Every 6-cell of the shape must be in-bounds and equal 6.
                six_abs = [(tr + r, tc + c) for r, c in six]
                if any(not (0 <= r < H and 0 <= c < W) for r, c in six_abs):
                    continue
                if not all(input_grid[r][c] == 6 for r, c in six_abs):
                    continue
                # Skip the original key block itself.
                if (tr, tc) == (kr0, kc0) and oh == kh and ow == kw and \
                        all(input_grid[tr + r][tc + c] == key[r][c]
                            for r in range(oh) for c in range(ow)):
                    continue
                four_in = [(tr + r, tc + c) for r, c in four
                           if 0 <= tr + r < H and 0 <= tc + c < W]
                # The 4-cells must not currently be part of a 6-shape.
                if any(input_grid[r][c] == 6 for r, c in four_in):
                    continue
                for r, c in four_in:
                    T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
