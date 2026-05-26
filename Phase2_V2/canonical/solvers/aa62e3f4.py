from collections import deque


def _background(input_grid):
    cnt = {}
    for row in input_grid:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    return max(cnt, key=cnt.get)


def _exterior(input_grid, bg):
    """Background cells reachable from the grid border (the outside region)."""
    H, W = len(input_grid), len(input_grid[0])
    ext = set()
    dq = deque()
    for r in range(H):
        for c in (0, W - 1):
            if input_grid[r][c] == bg:
                dq.append((r, c))
    for c in range(W):
        for r in (0, H - 1):
            if input_grid[r][c] == bg:
                dq.append((r, c))
    while dq:
        r, c = dq.popleft()
        if (r, c) in ext or not (0 <= r < H and 0 <= c < W):
            continue
        if input_grid[r][c] != bg:
            continue
        ext.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dq.append((r + dr, c + dc))
    return ext


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    The input holds a single closed shape: an outline color (touching the
    outside) wrapping an inner 'core' color.  The transformation erases the
    whole shape and re-draws, in the core color, the one-pixel-wide outer
    parallel contour of the outline (every exterior background cell that is
    orthogonally adjacent to the shape).
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    shape = set((r, c) for r in range(H) for c in range(W) if input_grid[r][c] != bg)
    ext = _exterior(input_grid, bg)

    # Outline colors touch the exterior (even diagonally); the core color does not.
    outline_colors = set()
    for (r, c) in shape:
        if any(0 <= r + dr < H and 0 <= c + dc < W and (r + dr, c + dc) in ext
               for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            outline_colors.add(input_grid[r][c])
    core = None
    for (r, c) in shape:
        v = input_grid[r][c]
        if v not in outline_colors:
            core = v
    if core is None:  # degenerate fallback: least frequent non-bg color
        cnt = {}
        for (r, c) in shape:
            v = input_grid[r][c]
            cnt[v] = cnt.get(v, 0) + 1
        if cnt:
            core = min(cnt, key=cnt.get)

    T = {}
    # Erase the shape.
    for (r, c) in shape:
        T[(r, c)] = bg
    # Draw the offset contour in the core color (overrides erasures where they meet).
    if core is not None:
        for (r, c) in ext:
            if any(0 <= r + dr < H and 0 <= c + dc < W and (r + dr, c + dc) in shape
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                T[(r, c)] = core
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
