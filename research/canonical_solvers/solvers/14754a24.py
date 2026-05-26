"""Canonical solver for ARC puzzle 14754a24.

Rule: the grid contains color-4 fragments. Each 8-connected 4-component is part
of a plus/cross shape (a center cell plus its 4 orthogonal arms). The shape is
incomplete: some of its cells are still background-fill color 5. The transformation
completes every such plus by recoloring its missing (currently-5) cells to 2.

The plus center is the cell whose orthogonal cross (clipped to the grid) (a)
contains the entire 4-component as a subset and (b) has all of its non-4 cells
currently equal to 5. Exactly one center satisfies this for each component.
"""


def _components(grid, val):
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == val and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    x, y = stack.pop()
                    if (x, y) in seen or not (0 <= x < H and 0 <= y < W):
                        continue
                    if grid[x][y] != val:
                        continue
                    seen.add((x, y))
                    comp.append((x, y))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((x + dr, y + dc))
                out.append(comp)
    return out


def _plus(cr, cc):
    return {(cr, cc), (cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)}


def infer_T(input_grid):
    """Compute the latent mask: {(r, c): 2} for every cell that completes a plus."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    for comp in _components(input_grid, 4):
        cs = set(comp)
        rs = [r for r, _ in comp]
        csl = [c for _, c in comp]
        # The plus center lies within the bounding box of the component (inclusive
        # of one extra ring), so scan a small neighborhood for valid centers.
        for cr in range(min(rs) - 1, max(rs) + 2):
            for cc in range(min(csl) - 1, max(csl) + 2):
                if not (0 <= cr < H and 0 <= cc < W):
                    continue
                plus = _plus(cr, cc)
                if not cs <= plus:
                    continue
                inb = {(r, c) for (r, c) in plus if 0 <= r < H and 0 <= c < W}
                fill = inb - cs
                if fill and all(input_grid[r][c] == 5 for r, c in fill):
                    for r, c in fill:
                        T[(r, c)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
