"""Canonical solver for ARC puzzle f3b10344.

Rule: the grid contains solid rectangular blocks of various colors on a
background of 0. Same-color blocks that face each other (overlap along one axis
and are separated only by background along the other) can be connected by a
bridge of color 8 drawn in the connecting gap. The bridge spans the full width
of the gap in the connecting direction, and the overlapping extent shrunk by
one cell on each side in the perpendicular direction.

When several same-color blocks face one another in a loop, only enough bridges
are drawn to connect them all without redundancy: per color the bridges form a
spanning forest (minimum spanning tree by gap distance), so the longest edge
that would merely close a cycle is omitted.

infer_T computes the set of cells to overwrite (the latent transformation mask)
purely from the block structure of the input. apply_T copies the input and
paints those masked cells with 8.
"""

BRIDGE = 8


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _blocks(grid, bg):
    """Return connected single-color components as (color, r0, r1, c0, c1)."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if a < 0 or b < 0 or a >= H or b >= W:
                    continue
                if seen[a][b] or grid[a][b] != color:
                    continue
                seen[a][b] = True
                cells.append((a, b))
                stack.extend([(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)])
            rs = [x for x, _ in cells]
            cs = [y for _, y in cells]
            out.append((color, min(rs), max(rs), min(cs), max(cs)))
    return out


def _gap_clear(grid, bg, r0, r1, c0, c1):
    """The rectangular gap between two facing blocks must be all background,
    so the two blocks are nearest neighbors with nothing in between."""
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != bg:
                return False
    return True


def _candidates(grid, bg, blocks):
    """All feasible same-color facing-pair bridges as
    (gap_distance, color, i, j, frozenset_of_cells)."""
    cands = []
    n = len(blocks)
    for i in range(n):
        ci, ri0, ri1, ci0, ci1 = blocks[i]
        for j in range(i + 1, n):
            cj, rj0, rj1, cj0, cj1 = blocks[j]
            if ci != cj:
                continue

            # Horizontal bridge: blocks overlap in rows, gap in columns.
            ro0, ro1 = max(ri0, rj0), min(ri1, rj1)
            if ro0 <= ro1 and ro1 - ro0 >= 2:
                if ci1 < cj0:
                    g0, g1 = ci1 + 1, cj0 - 1
                elif cj1 < ci0:
                    g0, g1 = cj1 + 1, ci0 - 1
                else:
                    g0 = None
                if g0 is not None and g0 <= g1 and _gap_clear(grid, bg, ro0, ro1, g0, g1):
                    cells = frozenset((r, c) for r in range(ro0 + 1, ro1)
                                      for c in range(g0, g1 + 1))
                    cands.append((g1 - g0 + 1, ci, i, j, cells))

            # Vertical bridge: blocks overlap in columns, gap in rows.
            co0, co1 = max(ci0, cj0), min(ci1, cj1)
            if co0 <= co1 and co1 - co0 >= 2:
                if ri1 < rj0:
                    g0, g1 = ri1 + 1, rj0 - 1
                elif rj1 < ri0:
                    g0, g1 = rj1 + 1, ri0 - 1
                else:
                    g0 = None
                if g0 is not None and g0 <= g1 and _gap_clear(grid, bg, g0, g1, co0, co1):
                    cells = frozenset((r, c) for r in range(g0, g1 + 1)
                                      for c in range(co0 + 1, co1))
                    cands.append((g1 - g0 + 1, ci, i, j, cells))
    return cands


def infer_T(grid):
    """Infer the latent transformation: the set of cells to turn into 8.

    Builds a minimum spanning forest over the candidate bridges (Kruskal by gap
    distance), so each connected group of same-color facing blocks is linked
    without redundant cycle-closing bridges.
    """
    bg = _background(grid)
    blocks = _blocks(grid, bg)
    cands = _candidates(grid, bg, blocks)

    parent = list(range(len(blocks)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    mask = set()
    for _w, _col, i, j, cells in sorted(cands, key=lambda t: t[0]):
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
            mask |= cells
    return mask


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c) in T:
        out[r][c] = BRIDGE
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
