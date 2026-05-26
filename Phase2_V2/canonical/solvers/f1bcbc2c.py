"""Canonical latent-T solver for ARC puzzle f1bcbc2c.

Rule (inferred from input structure only):
  The grid contains a width-1 channel ("pipe") delimited by 7-walls and laid
  out against the background of 0s.  A 9-marker, when present, sits at one end
  of (or partway along) the pipe.  The transformation fills the pipe's interior
  with 8.

  * No marker: the pipe is a single thin connected component of empty cells
    (the only empty component with no 2x2 solid block).  Fill all its cells.
  * Marker that is a straight pass-through (its two open sides are opposite):
    the whole pipe is filled, painting over the marker cell as well.
  * Marker at a corner / junction (its two open sides are perpendicular): the
    marker stays, and only the longer arm leaving the marker is filled (the
    shorter arm is a decoy stub).

infer_T returns the latent mask {(r,c): 8} of cells to paint; apply_T copies the
input and overwrites only those cells.
"""


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _neighbors(r, c):
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _component(g, start, passable):
    H, W = len(g), len(g[0])
    seen = set()
    stack = [start]
    while stack:
        r, c = stack.pop()
        if (r, c) in seen or not (0 <= r < H and 0 <= c < W):
            continue
        if not passable(g[r][c]):
            continue
        seen.add((r, c))
        for nb in _neighbors(r, c):
            stack.append(nb)
    return seen


def infer_T(g):
    H, W = len(g), len(g[0])
    passable = lambda v: v in (0, 9)

    # locate the marker, if any
    start9 = next(
        ((r, c) for r in range(H) for c in range(W) if g[r][c] == 9), None
    )

    if start9 is not None:
        comp = _component(g, start9, passable)
    else:
        # choose the thin tube: the empty component with no 2x2 solid block;
        # if several qualify, take the largest.
        seen_all = set()
        comp = None
        for r in range(H):
            for c in range(W):
                if passable(g[r][c]) and (r, c) not in seen_all:
                    cc = _component(g, (r, c), passable)
                    seen_all |= cc
                    is_thin = all(
                        not all(
                            (a + da, b + db) in cc
                            for da in (0, 1)
                            for db in (0, 1)
                        )
                        for (a, b) in cc
                    )
                    if is_thin and (comp is None or len(cc) > len(comp)):
                        comp = cc
        if comp is None:
            comp = set()

    fill = set()
    if start9 is None:
        # single open tube: fill all its empty cells
        for (r, c) in comp:
            if g[r][c] == 0:
                fill.add((r, c))
    else:
        sr, sc = start9
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        open_dirs = [(dr, dc) for dr, dc in dirs if (sr + dr, sc + dc) in comp]
        collinear = (
            len(open_dirs) == 2
            and open_dirs[0][0] == -open_dirs[1][0]
            and open_dirs[0][1] == -open_dirs[1][1]
        )
        if len(open_dirs) <= 1 or collinear:
            # straight pass-through (or single arm): fill the whole tube,
            # painting over the marker cell as well
            for (r, c) in comp:
                fill.add((r, c))
        else:
            # corner / junction: walk each arm from the marker, keep the longest
            best = set()
            for dr, dc in open_dirs:
                arm = set()
                prev = (sr, sc)
                cur = (sr + dr, sc + dc)
                while True:
                    arm.add(cur)
                    r, c = cur
                    nxts = [
                        nb for nb in _neighbors(r, c) if nb in comp and nb != prev
                    ]
                    if len(nxts) == 1:
                        prev, cur = cur, nxts[0]
                    else:
                        break
                if len(arm) > len(best):
                    best = arm
            for (r, c) in best:
                if g[r][c] == 0:
                    fill.add((r, c))

    return {(r, c): 8 for (r, c) in fill}


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
