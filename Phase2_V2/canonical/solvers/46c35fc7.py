# Solver for ARC puzzle 46c35fc7
#
# Rule: The grid contains one or more isolated 3x3 blocks drawn on a uniform
# background (the most common color). Each block is rearranged by a fixed cell
# permutation of its 3x3 positions (the center stays fixed). The permutation,
# in (src_row,src_col) -> (dst_row,dst_col) form, is:
#   (0,0)->(2,0) (0,1)->(1,2) (0,2)->(0,0)
#   (1,0)->(0,1) (1,1)->(1,1) (1,2)->(2,1)
#   (2,0)->(2,2) (2,1)->(1,0) (2,2)->(0,2)
# Corners cycle counter-clockwise, edge-midpoints cycle clockwise.
#
# Canonical latent-T form: infer_T builds a dict mask {(r,c): new_color} of the
# cells whose color changes; apply_T overwrites only those cells.

# Fixed 3x3 position permutation: source cell -> destination cell.
_PERM = {
    (0, 0): (2, 0), (0, 1): (1, 2), (0, 2): (0, 0),
    (1, 0): (0, 1), (1, 1): (1, 1), (1, 2): (2, 1),
    (2, 0): (2, 2), (2, 1): (1, 0), (2, 2): (0, 2),
}


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(grid, bg):
    """4-connected components of non-background cells."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    a, b = stack.pop()
                    cells.append((a, b))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + dr, b + dc
                        if 0 <= na < H and 0 <= nb < W and not seen[na][nb] \
                                and grid[na][nb] != bg:
                            seen[na][nb] = True
                            stack.append((na, nb))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Build a latent mask {(r,c): new_color} describing every changed cell.

    Detect each isolated 3x3 block (a connected non-background cluster whose
    bounding box is 3x3), then permute its cells by the fixed _PERM rule.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    T = {}
    for cells in _components(input_grid, bg):
        rs = [a for a, _ in cells]
        cs = [b for _, b in cells]
        r0, c0 = min(rs), min(cs)
        # Only treat clusters that fit in a 3x3 bounding box as blocks.
        if max(rs) - r0 != 2 or max(cs) - c0 != 2:
            continue
        # Read the 3x3 block (cells not part of the cluster are background).
        block = [[input_grid[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
        for (sr, sc), (dr, dc) in _PERM.items():
            T[(r0 + dr, c0 + dc)] = block[sr][sc]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
