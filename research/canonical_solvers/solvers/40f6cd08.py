"""Canonical solver for ARC puzzle 40f6cd08.

Rule: the grid contains several solid-color rectangular regions on a 0 background.
Exactly one rectangle is "decorated" with concentric nested frames (more than one
color); the others are blank (a single color). Each blank rectangle is repainted
with the SAME concentric-frame decoration as the decorated source. Every colored
frame keeps its fixed thickness/inset from each of the four sides, and the
innermost color stretches to fill whatever space remains in the target rectangle.

We model each color of the source by the inset of its bounding box from each of
the four edges (top, bottom, left, right). A cell of a target rectangle is given
the color of the deepest (most nested) frame whose four per-side insets it
satisfies.

infer_T builds a latent mask {(r,c): color} of the cells to overwrite; apply_T
copies the input and writes only the masked cells.
"""


def _rectangles(grid):
    """Return list of (r0, r1, c0, c1) bounding boxes of non-zero 4-connected blobs."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if grid[sr][sc] != 0 and not seen[sr][sc]:
                stack = [(sr, sc)]
                cells = []
                while stack:
                    r, c = stack.pop()
                    if r < 0 or r >= H or c < 0 or c >= W:
                        continue
                    if seen[r][c] or grid[r][c] == 0:
                        continue
                    seen[r][c] = True
                    cells.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                rs = [a for a, _ in cells]
                cs = [b for _, b in cells]
                comps.append((min(rs), max(rs), min(cs), max(cs)))
    return comps


def _color_insets(grid, r0, r1, c0, c1):
    """For each color in the rectangle, the (top, bottom, left, right) inset of its
    bounding box from the rectangle edges, plus the cell count (for tie-breaking)."""
    H, W = r1 - r0 + 1, c1 - c0 + 1
    cells = {}
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            cells.setdefault(grid[r][c], []).append((r - r0, c - c0))
    insets = {}
    for col, cs in cells.items():
        rs = [a for a, _ in cs]
        ccs = [b for _, b in cs]
        insets[col] = (min(rs), H - 1 - max(rs), min(ccs), W - 1 - max(ccs), len(cs))
    return insets


def _render(H, W, insets):
    """Color each cell by the deepest frame whose per-side insets it satisfies.
    Outer-to-inner order = increasing total inset (tie-break by larger cell count
    = more outer)."""
    order = sorted(insets.keys(), key=lambda col: (sum(insets[col][:4]), -insets[col][4]))
    grid = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            dt, db, dl, dr = r, H - 1 - r, c, W - 1 - c
            chosen = None
            for col in order:
                t, b, l, ri, _ = insets[col]
                if dt >= t and db >= b and dl >= l and dr >= ri:
                    chosen = col
            grid[r][c] = chosen
    return grid


def infer_T(input_grid):
    """Build the latent mask {(r,c): new_color} of cells to repaint."""
    rects = _rectangles(input_grid)

    # The decorated source is the rectangle containing more than one color.
    source = None
    targets = []
    for (r0, r1, c0, c1) in rects:
        colors = set(
            input_grid[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
        )
        if len(colors) > 1:
            source = (r0, r1, c0, c1)
        else:
            targets.append((r0, r1, c0, c1))

    T = {}
    if source is None:
        return T

    insets = _color_insets(input_grid, *source)
    for (r0, r1, c0, c1) in targets:
        H, W = r1 - r0 + 1, c1 - c0 + 1
        rendered = _render(H, W, insets)
        for r in range(H):
            for c in range(W):
                val = rendered[r][c]
                if val is not None and val != input_grid[r0 + r][c0 + c]:
                    T[(r0 + r, c0 + c)] = val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
