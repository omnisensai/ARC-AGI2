"""Canonical solver for ARC puzzle d968ffd4.

Two colored bars sit on a background, separated along one axis (both bars
share the perpendicular extent). Each bar emits a beam toward the other,
filling half of the gap between them (floor(gap/2) cells). The beam is the
bar widened by one cell on each side along the perpendicular axis (clipped
to the grid). The original bars and any leftover middle gap are preserved.
"""


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            cells = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and grid[ny][nx] == color:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            comps.append({
                "color": color,
                "r0": min(rs), "r1": max(rs),
                "c0": min(cs), "c1": max(cs),
            })
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    comps = _components(input_grid, bg)
    T = [[None] * W for _ in range(H)]
    if len(comps) != 2:
        return T

    a, b = comps

    # Determine separation axis. Horizontal if their column ranges are disjoint.
    horizontal = a["c1"] < b["c0"] or b["c1"] < a["c0"]

    def beam(obj, other):
        # along-axis gap and perpendicular widened span
        if horizontal:
            # object on left or right of the other
            if obj["c0"] < other["c0"]:
                gap = other["c0"] - obj["c1"] - 1
                length = gap // 2
                start = obj["c1"] + 1
                cols = range(start, start + length)
            else:
                gap = obj["c0"] - other["c1"] - 1
                length = gap // 2
                end = obj["c0"] - 1
                cols = range(end - length + 1, end + 1)
            r_lo = max(0, obj["r0"] - 1)
            r_hi = min(H - 1, obj["r1"] + 1)
            for c in cols:
                for r in range(r_lo, r_hi + 1):
                    T[r][c] = obj["color"]
        else:
            if obj["r0"] < other["r0"]:
                gap = other["r0"] - obj["r1"] - 1
                length = gap // 2
                start = obj["r1"] + 1
                rows = range(start, start + length)
            else:
                gap = obj["r0"] - other["r1"] - 1
                length = gap // 2
                end = obj["r0"] - 1
                rows = range(end - length + 1, end + 1)
            c_lo = max(0, obj["c0"] - 1)
            c_hi = min(W - 1, obj["c1"] + 1)
            for r in rows:
                for c in range(c_lo, c_hi + 1):
                    T[r][c] = obj["color"]

    beam(a, b)
    beam(b, a)
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
