"""Canonical solver for ARC puzzle 228f6490.

Rule
----
The grid contains several rectangular "frames" drawn in color 5. Each frame has
an interior pattern of background (0) holes. Scattered elsewhere are colored
shapes. Exactly one color is "noise" (it appears as many small disconnected
components); it is ignored. Every remaining colored shape is a single connected
component whose cell pattern matches the hole pattern of exactly one frame.

For each frame we find the shape whose normalized cell pattern equals the
frame's normalized hole pattern, fill the holes with that shape's color, and
erase the shape from its original location.

The latent transformation T is a dict {(r, c): new_color} marking exactly the
cells that change: hole cells get filled, shape cells get cleared to 0.
"""

from collections import Counter


def _components(grid, predicate):
    """8-connected, single-color components for cells satisfying predicate."""
    H, W = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if (r, c) in seen or not predicate(grid[r][c]):
                continue
            col = grid[r][c]
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                    continue
                if grid[a][b] != col:
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((a + dr, b + dc))
            out.append((col, cells))
    return out


def _norm(cells):
    """Translation-normalized cell set."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _find_frames(grid):
    """Return each frame's list of interior hole cells (0s within its bbox)."""
    H, W = len(grid), len(grid[0])
    seen = set()
    frames = []
    for r in range(H):
        for c in range(W):
            if (r, c) in seen or grid[r][c] != 5:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                a, b = stack.pop()
                if (a, b) in seen or not (0 <= a < H and 0 <= b < W):
                    continue
                if grid[a][b] != 5:
                    continue
                seen.add((a, b))
                cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((a + dr, b + dc))
            rs = [x for x, _ in cells]
            cs = [y for _, y in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            holes = [(i, j) for i in range(r0, r1 + 1)
                     for j in range(c0, c1 + 1) if grid[i][j] == 0]
            if holes:
                frames.append(holes)
    return frames


def infer_T(input_grid):
    """Compute the latent change mask: {(r, c): new_color}."""
    shapes = _components(input_grid, lambda v: v not in (0, 5))

    # Identify the noise color: the one forming the most components (>1).
    counts = Counter(col for col, _ in shapes)
    noise = None
    if counts:
        cand_noise = max(counts, key=lambda k: counts[k])
        if counts[cand_noise] > 1:
            noise = cand_noise

    candidates = [(col, cells) for col, cells in shapes if col != noise]
    frames = _find_frames(input_grid)

    T = {}
    used = set()
    for holes in frames:
        nh = _norm(holes)
        for idx, (col, cells) in enumerate(candidates):
            if idx in used:
                continue
            if len(cells) == len(holes) and _norm(cells) == nh:
                used.add(idx)
                for (i, j) in holes:      # fill the frame's holes
                    T[(i, j)] = col
                for (i, j) in cells:      # erase the original shape
                    T[(i, j)] = 0
                break
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
