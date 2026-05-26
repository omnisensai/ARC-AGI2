"""Canonical latent-T solver for ARC puzzle 36fdfd69.

Rule: Color 2 appears in localized clusters that mark rectangular "tiles".
Group the 2-cells by proximity (Chebyshev distance <= 2 links them into one
tile). For each tile, take the bounding box of its 2-cells; every cell inside
that bounding box that is NOT a 2 (i.e. a noise/foreground cell embedded in the
tile) is recolored to 4. The 2s and the rest of the grid are left untouched.
"""


def infer_T(input_grid):
    """Compute the latent transformation mask {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    twos = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 2]

    # Union-find: link 2-cells within Chebyshev distance 2 into the same tile.
    n = len(twos)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        r1, c1 = twos[i]
        for j in range(i + 1, n):
            r2, c2 = twos[j]
            if max(abs(r1 - r2), abs(c1 - c2)) <= 2:
                parent[find(i)] = find(j)

    groups = {}
    for i, t in enumerate(twos):
        groups.setdefault(find(i), []).append(t)

    T = {}
    for grp in groups.values():
        rs = [r for r, c in grp]
        cs = [c for r, c in grp]
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                if input_grid[r][c] != 2:
                    T[(r, c)] = 4
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
