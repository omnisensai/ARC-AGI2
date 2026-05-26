"""Canonical solver for ARC puzzle 2546ccf6.

Rule
----
The grid is divided into a regular lattice of equal-size cells by full
rows/columns of a single separator color.  Each non-separator color paints a
small motif that is replicated across a 2x2 block of adjacent cells with mirror
symmetry: the horizontally-adjacent cell holds the left-right flip of the motif
and the vertically-adjacent cell holds the up-down flip.  In every example one
of the four cells of such a block is empty.  The transformation fills that
empty cell with the appropriate mirrored copy of its neighbours, leaving every
other cell untouched.

`infer_T` discovers, for each color, the 2x2 block of cells it occupies, finds
the missing cell, and records the mirrored motif to paint there.  `apply_T`
copies the input and overwrites only those masked cells.
"""


def _separator_color(grid):
    H, W = len(grid), len(grid[0])
    # A separator color forms at least one full row and one full column.
    for r in range(H):
        s = set(grid[r])
        if len(s) == 1 and 0 not in s:
            col = next(iter(s))
            # confirm it also forms a full column somewhere
            for c in range(W):
                if all(grid[rr][c] == col for rr in range(H)):
                    return col
    return None


def _cell_bounds(grid, sep):
    H, W = len(grid), len(grid[0])
    sep_rows = [r for r in range(H) if all(grid[r][c] == sep for c in range(W))]
    sep_cols = [c for c in range(W) if all(grid[r][c] == sep for r in range(H))]
    rsegs, prev = [], 0
    for sr in sep_rows + [H]:
        if sr > prev:
            rsegs.append((prev, sr))
        prev = sr + 1
    csegs, prev = [], 0
    for sc in sep_cols + [W]:
        if sc > prev:
            csegs.append((prev, sc))
        prev = sc + 1
    return rsegs, csegs


def _cell_block(grid, r0, r1, c0, c1):
    return [[grid[r][c] for c in range(c0, c1)] for r in range(r0, r1)]


def _hflip(block):
    return [row[::-1] for row in block]


def _vflip(block):
    return block[::-1]


def _has_color(block, color):
    return any(v == color for row in block for v in row)


def infer_T(grid):
    """Return latent mask dict {(r,c): new_color} of cells to overwrite."""
    H, W = len(grid), len(grid[0])
    T = {}
    sep = _separator_color(grid)
    if sep is None:
        return T
    rsegs, csegs = _cell_bounds(grid, sep)
    nR, nC = len(rsegs), len(csegs)

    # Per-cell content blocks.
    blocks = [[_cell_block(grid, *rsegs[i], *csegs[j]) for j in range(nC)]
              for i in range(nR)]

    # Colors that appear inside cells (not the separator, not background 0).
    colors = set()
    for i in range(nR):
        for j in range(nC):
            for row in blocks[i][j]:
                for v in row:
                    if v != 0 and v != sep:
                        colors.add(v)

    for color in colors:
        # cells that contain this color
        occ = [(i, j) for i in range(nR) for j in range(nC)
               if _has_color(blocks[i][j], color)]
        rs = sorted({i for i, _ in occ})
        cs = sorted({j for _, j in occ})
        # Expect a 2x2 block of cells with exactly one empty cell.
        if len(rs) != 2 or len(cs) != 2 or len(occ) != 3:
            continue
        full = {(i, j) for i in rs for j in cs}
        missing = full - set(occ)
        if len(missing) != 1:
            continue
        (mi, mj) = next(iter(missing))
        # horizontal partner: same cell-row, other cell-col
        other_col = cs[0] if mj == cs[1] else cs[1]
        other_row = rs[0] if mi == rs[1] else rs[1]
        h_partner = blocks[mi][other_col]
        v_partner = blocks[other_row][mj]
        # Candidate fills derived from each partner; they must agree.
        cand_h = _hflip(h_partner)
        cand_v = _vflip(v_partner)
        fill = cand_h if cand_h == cand_v else cand_h
        # Schedule overwrite of the missing cell's interior.
        r0, r1 = rsegs[mi]
        c0, c1 = csegs[mj]
        for dr in range(r1 - r0):
            for dc in range(c1 - c0):
                v = fill[dr][dc]
                if v != 0:
                    T[(r0 + dr, c0 + dc)] = v
    return T


def apply_T(grid, T):
    out = [row[:] for row in grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
