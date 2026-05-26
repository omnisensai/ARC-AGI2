"""Canonical solver for ARC task f9d67f8b.

Structure of the task
---------------------
Every grid is a symmetric coloured "fabric" of dimension HxW in which a
rectangular patch of cells has been overwritten by a single marker colour
(here 9).  The fabric is invariant under a group of geometric symmetries:
the mirror reflections about its central vertical / horizontal axes (and
their composition, the 180-degree rotation), plus -- in the corner regions --
the diagonal reflections / quarter-turns.  Every marker cell must therefore
be restored to the value that the symmetry forces it to have.

Approach
--------
``infer_T`` discovers, *from the input alone*, every reflection / glide axis
that the revealed (non-marker) part of the grid respects, then propagates the
known colours into the marker cells along those symmetries until a fixed
point is reached.  Marker cells that no global axis can reach (cells that sit
in the asymmetric "overhang" band whose mirror partner is itself masked) are
recovered with the diagonal D4 maps (transpose / anti-transpose / quarter
turns), which encode the texture's local corner symmetry.  The resulting
``{(r, c): colour}`` mapping is the latent transformation mask.

``apply_T`` copies the input and overwrites only the masked cells.
"""


def _marker_color(grid):
    """The marker is the colour that forms a solid axis-aligned rectangle
    (the deleted patch).  It is found as the colour whose occupied cells form
    a full filled bounding box; ties fall back to a sensible default."""
    H, W = len(grid), len(grid[0])
    cells = {}
    for r in range(H):
        for c in range(W):
            cells.setdefault(grid[r][c], []).append((r, c))
    best = None
    for color, pts in cells.items():
        rs = [p[0] for p in pts]
        cs = [p[1] for p in pts]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        area = (r1 - r0 + 1) * (c1 - c0 + 1)
        # candidate if the cells exactly fill their bounding rectangle
        if len(pts) == area and area > 1:
            score = area
            if best is None or score > best[0]:
                best = (score, color)
    if best is not None:
        return best[1]
    # fallback: a colour that appears but is plausibly the marker (rare)
    return 9 if any(9 in row for row in grid) else None


def _reflection_maps(H, W):
    """All candidate reflection / glide axes (vertical, horizontal and the two
    diagonal orientations) at every integer offset."""
    maps = []
    for s in range(0, 2 * W - 1):
        maps.append(lambda r, c, s=s: (r, s - c))          # vertical mirror
    for s in range(0, 2 * H - 1):
        maps.append(lambda r, c, s=s: (s - r, c))          # horizontal mirror
    for t in range(-(W - 1), H):
        maps.append(lambda r, c, t=t: (c + t, r - t))      # main-diagonal mirror
    for t in range(0, H + W - 1):
        maps.append(lambda r, c, t=t: (t - c, t - r))      # anti-diagonal mirror
    return maps


def _respected(grid, f, marker, H, W):
    """Return support count if every revealed pair agrees under ``f``;
    -1 if any contradiction is found."""
    support = 0
    for r in range(H):
        for c in range(W):
            rr, cc = f(r, c)
            if 0 <= rr < H and 0 <= cc < W:
                a, b = grid[r][c], grid[rr][cc]
                if a != marker and b != marker:
                    if a != b:
                        return -1
                    support += 1
    return support


def infer_T(input_grid):
    """Infer the latent transformation: a mapping {(r, c): new_color} for the
    marker cells, derived purely from the symmetry structure of the input."""
    H, W = len(input_grid), len(input_grid[0])
    marker = _marker_color(input_grid)
    T = {}
    if marker is None:
        return T

    # working copy that we fill in place while reasoning about symmetry
    work = [row[:] for row in input_grid]

    # 1) every reflection / glide axis the revealed grid respects
    sym = [f for f in _reflection_maps(H, W)
           if _respected(input_grid, f, marker, H, W) >= 1]

    def propagate(maps):
        changed = True
        while changed:
            changed = False
            for r in range(H):
                for c in range(W):
                    if work[r][c] != marker:
                        continue
                    for f in maps:
                        rr, cc = f(r, c)
                        if 0 <= rr < H and 0 <= cc < W and work[rr][cc] != marker:
                            work[r][c] = work[rr][cc]
                            T[(r, c)] = work[rr][cc]
                            changed = True
                            break

    propagate(sym)

    # 2) corner diagonal D4 maps (transpose / anti-transpose / quarter turns)
    #    recover cells in the asymmetric overhang band whose mirror partner is
    #    itself masked.
    diag = [
        lambda r, c: (c, r),
        lambda r, c: (W - 1 - c, H - 1 - r),
        lambda r, c: (c, H - 1 - r),
        lambda r, c: (W - 1 - c, r),
    ]
    propagate(diag)

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
