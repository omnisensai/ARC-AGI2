"""Canonical latent-T solver for ARC puzzle f8c80d96.

Rule (inferred from input structure alone):
  The input contains a set of nested, concentric rectangular "frames" drawn in a
  single foreground color on a background of 0.  Every frame shares the same
  "side signature" (which of top/bottom/left/right edges are actually drawn) and
  the frames' bounding boxes form an arithmetic progression (a rectangular
  spiral).  The transformation continues that spiral: it extrapolates the
  arithmetic progression of bounding boxes outward (and inward) for as long as a
  box still intersects the grid, draws each clipped frame in the foreground
  color, and paints every remaining background (0) cell with color 5.  Existing
  foreground cells are preserved.

Canonical form:
  T = infer_T(input_grid)   -> latent mask dict {(r,c): new_color}
  apply_T(input_grid, T)    -> copy input, overwrite only masked cells
"""


def _foreground_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    nonzero = [k for k in counts if k != 0]
    if not nonzero:
        return None
    # The drawn spiral is the dominant non-background color.
    return max(nonzero, key=lambda k: counts[k])


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    cells = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if grid[r][c] == color
    )
    comps = []
    seen = set()
    for cell in cells:
        if cell in seen:
            continue
        comp = set()
        stack = [cell]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.add(x)
            r, c = x
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    stack.append(nb)
        comps.append(comp)
    return comps


def _describe(comp):
    rs = [x[0] for x in comp]
    cs = [x[1] for x in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    s = comp
    top = all((r0, c) in s for c in range(c0, c1 + 1))
    bot = all((r1, c) in s for c in range(c0, c1 + 1))
    left = all((r, c0) in s for r in range(r0, r1 + 1))
    right = all((r, c1) in s for r in range(r0, r1 + 1))
    return [r0, r1, c0, c1], (top, bot, left, right)


def _draw_frame(box, sig, H, W, out_cells):
    r0, r1, c0, c1 = box
    top, bot, left, right = sig

    def put(r, c):
        if 0 <= r < H and 0 <= c < W:
            out_cells.add((r, c))

    if top:
        for c in range(c0, c1 + 1):
            put(r0, c)
    if bot:
        for c in range(c0, c1 + 1):
            put(r1, c)
    if left:
        for r in range(r0, r1 + 1):
            put(r, c0)
    if right:
        for r in range(r0, r1 + 1):
            put(r, c1)


def _box_intersects_grid(box, H, W):
    r0, r1, c0, c1 = box
    return not (r1 < 0 or r0 >= H or c1 < 0 or c0 >= W)


def infer_T(input_grid):
    """Return a latent mask dict {(r, c): new_color}.

    Foreground cells of the extrapolated spiral map to the spiral color; all
    remaining background (0) cells map to 5.
    """
    H, W = len(input_grid), len(input_grid[0])
    color = _foreground_color(input_grid)
    T = {}
    if color is None:
        return T

    comps = _components(input_grid, color)
    described = [_describe(comp) for comp in comps]
    # Smallest frame first (by bounding-box area).
    described.sort(key=lambda b: (b[0][1] - b[0][0]) * (b[0][3] - b[0][2]))

    boxes = [b[0] for b in described]
    sig = described[0][1]

    spiral_cells = set()

    if len(boxes) >= 2:
        # Arithmetic-progression step between consecutive concentric frames.
        step = tuple(boxes[1][j] - boxes[0][j] for j in range(4))

        # Draw the frames already present.
        for b in boxes:
            _draw_frame(b, sig, H, W, spiral_cells)

        # Extrapolate outward (toward larger / further along the progression).
        box = list(boxes[-1])
        for _ in range(1000):
            box = [box[j] + step[j] for j in range(4)]
            if not _box_intersects_grid(box, H, W):
                break
            _draw_frame(box, sig, H, W, spiral_cells)

        # Extrapolate inward (toward smaller) for completeness.
        box = list(boxes[0])
        for _ in range(1000):
            nb = [box[j] - step[j] for j in range(4)]
            if not _box_intersects_grid(nb, H, W):
                break
            box = nb
            _draw_frame(box, sig, H, W, spiral_cells)
    else:
        for b in boxes:
            _draw_frame(b, sig, H, W, spiral_cells)

    for r in range(H):
        for c in range(W):
            if (r, c) in spiral_cells or input_grid[r][c] == color:
                # Spiral foreground (preserve / extend the color).
                if input_grid[r][c] != color:
                    T[(r, c)] = color
            else:
                # Background becomes 5.
                if input_grid[r][c] != 5:
                    T[(r, c)] = 5
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
