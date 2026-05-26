def infer_T(input_grid):
    """Latent mask: cells to clear (set to background 0).

    Rule: colored cells (non-zero) form 8-connected components. A cell that is
    completely isolated (its 8-connected component has size 1, i.e. it has no
    orthogonal or diagonal neighbor of any color) is noise and gets removed.
    Cells belonging to a component of size >= 2 are kept.
    """
    H, W = len(input_grid), len(input_grid[0])

    cells = set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                cells.add((r, c))

    def neighbors8(r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                yield r + dr, c + dc

    # Compute 8-connected component sizes.
    seen = set()
    comp_size = {}
    for cell in cells:
        if cell in seen:
            continue
        stack = [cell]
        comp = []
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            for n in neighbors8(*x):
                stack.append(n)
        for x in comp:
            comp_size[x] = len(comp)

    # Mask: set isolated cells to 0.
    T = [[None] * W for _ in range(H)]
    for (r, c) in cells:
        if comp_size[(r, c)] == 1:
            T[r][c] = 0
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
