from collections import deque


def _marker_cells(input_grid):
    """Non-background, non-wall cells form the seed marker."""
    H, W = len(input_grid), len(input_grid[0])
    return [(r, c) for r in range(H) for c in range(W)
            if input_grid[r][c] not in (0, 8)]


def infer_T(input_grid):
    """Latent mask: {(r,c): color} for every 0-corridor cell reachable from the
    marker via 4-connected non-wall (non-8) cells. The color is a checkerboard
    keyed on (r+c) parity; the parity->color map is read off the marker cells,
    which already lie on that checkerboard.
    """
    H, W = len(input_grid), len(input_grid[0])
    marker = _marker_cells(input_grid)

    # parity -> color, derived from the marker cells themselves
    parity_color = {}
    for (r, c) in marker:
        parity_color[(r + c) % 2] = input_grid[r][c]

    T = {}
    if not marker or len(parity_color) < 2:
        return T

    # flood fill through all passable (non-wall) cells starting at the marker
    passable = lambda r, c: 0 <= r < H and 0 <= c < W and input_grid[r][c] != 8
    seen = set(marker)
    q = deque(marker)
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if passable(nr, nc) and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))

    for (r, c) in seen:
        if input_grid[r][c] == 0:
            T[(r, c)] = parity_color[(r + c) % 2]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
