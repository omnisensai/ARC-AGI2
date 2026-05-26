"""Canonical solver for ARC puzzle 58e15b12.

Rule
----
The input contains one or more "channel" objects, each a pair of parallel
straight lines of a single color (here drawn as two vertical columns) spanning
a segment of `L` rows.  Each individual line is re-drawn as a *wedge*: its apex
stays on the original segment, and as you move away from the segment (both up
and down) the line drifts outward by one column for every `L` rows traversed.
The left line drifts left, the right line drifts right, so the pair fans open
in both directions.  Rays are clipped at the grid edges (no wrapping).

Where rays belonging to two different objects (different colors) land on the
same cell, that cell becomes color 6 (a collision marker).

`infer_T` walks every line of every object and accumulates the set of colors
that want to occupy each cell.  `apply_T` overwrites each such cell with the
object color, or with 6 when two distinct colors collide.
"""


def _find_objects(g):
    """Return channel objects: {color, r0, r1, cols} for each non-bg color."""
    H, W = len(g), len(g[0])
    objs = []
    for color in range(1, 10):
        if color == 6:  # 6 is the collision marker, never an input object
            continue
        cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] == color]
        if not cells:
            continue
        rows = sorted(set(r for r, c in cells))
        cols = sorted(set(c for r, c in cells))
        objs.append({"color": color, "r0": rows[0], "r1": rows[-1],
                     "rows": rows, "cols": cols})
    return objs


def _emit_wedge(rays, color, a0, a1, base, direction, H_ax, W_ax, vertical):
    """Trace one line as a wedge.

    The segment runs along the major axis from a0..a1 (length L); `base` is the
    line's coordinate on the minor axis and `direction` (+1/-1) is the side it
    fans toward.  Block k (k>=1) sits one minor step further out and spans L
    positions along the major axis, mirrored above and below the segment.
    """
    def put(major, minor):
        r, c = (major, minor) if vertical else (minor, major)
        if 0 <= r < H_ax and 0 <= c < W_ax:
            rays.setdefault((r, c), []).append(color)
            return True
        return False

    L = a1 - a0 + 1
    # block 0: the original segment
    for a in range(a0, a1 + 1):
        put(a, base)
    k = 1
    while True:
        minor = base + direction * k
        in_minor = 0 <= minor < (W_ax if vertical else H_ax)
        if in_minor:
            for a in range(a0 - k * L, a0 - (k - 1) * L):  # block above
                put(a, minor)
            for a in range(a1 + 1 + (k - 1) * L, a1 + 1 + k * L):  # block below
                put(a, minor)
        # termination: minor axis exhausted, or major axis fully past both ends
        if not in_minor:
            break
        if a0 - k * L < -H_ax - W_ax and a1 + 1 + (k - 1) * L >= H_ax + W_ax:
            break
        k += 1
        if k > H_ax + W_ax:
            break


def infer_T(input_grid):
    """Latent mask: {(r,c): color} where rays land; collisions recorded as 6."""
    H, W = len(input_grid), len(input_grid[0])
    rays = {}
    for obj in _find_objects(input_grid):
        color = obj["color"]
        if len(obj["cols"]) == 2:          # vertical channel (two columns)
            cL, cR = obj["cols"]
            _emit_wedge(rays, color, obj["r0"], obj["r1"], cL, -1, H, W, True)
            _emit_wedge(rays, color, obj["r0"], obj["r1"], cR, +1, H, W, True)
        elif len(obj["rows"]) == 2:        # horizontal channel (two rows)
            rT, rB = obj["rows"]
            cols = obj["cols"]
            _emit_wedge(rays, color, cols[0], cols[-1], rT, -1, H, W, False)
            _emit_wedge(rays, color, cols[0], cols[-1], rB, +1, H, W, False)

    T = {}
    for (r, c), colors in rays.items():
        if not (0 <= r < H and 0 <= c < W):
            continue
        uniq = set(colors)
        T[(r, c)] = 6 if len(uniq) > 1 else colors[0]
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
