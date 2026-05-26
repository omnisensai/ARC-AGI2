from collections import deque


def infer_T(input_grid):
    """Latent mask: flood-fill outward from every cell already colored 1,
    spreading through background (0) cells via 4-connectivity. Every reached
    0-cell is marked to become a 1. Non-zero, non-1 cells block the spread."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    seen = set()
    dq = deque()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                dq.append((r, c))
                seen.add((r, c))
    while dq:
        r, c = dq.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen \
                    and input_grid[nr][nc] == 0:
                seen.add((nr, nc))
                T[nr][nc] = 1
                dq.append((nr, nc))
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
