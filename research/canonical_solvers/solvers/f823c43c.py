"""Canonical latent-T solver for ARC puzzle f823c43c.

Rule: the grid is a clean, doubly-periodic two-color tiling (background +
pattern) onto which a "noise" color has been sprinkled, overwriting scattered
single cells. The transformation removes the noise by restoring the underlying
periodic pattern.

infer_T discovers, from the input alone:
  - the noise color and the spatial period (pr, pc) such that, after ignoring
    the noise color, every residue class (r mod pr, c mod pc) is perfectly
    consistent (a single non-noise value),
  - the per-residue-class template value.
The latent mask T marks every cell whose current value disagrees with its
template value (i.e. every noisy / corrupted cell) and records the restored
color. apply_T overwrites only those masked cells.
"""

from collections import Counter


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    colors = list(cnt.keys())

    best = None  # (key, noise, pr, pc, template)
    for noise in colors:
        # Search spatial periods using residue classes (divisibility not required).
        for pr in range(1, H + 1):
            for pc in range(1, W + 1):
                if pr == H and pc == W:
                    continue
                template = {}
                ok = True
                conflicts = 0
                for r0 in range(pr):
                    for c0 in range(pc):
                        vals = []
                        for r in range(r0, H, pr):
                            for c in range(c0, W, pc):
                                v = input_grid[r][c]
                                if v != noise:
                                    vals.append(v)
                        if not vals:
                            # this residue class is entirely noise -> can't define it
                            ok = False
                            break
                        c2 = Counter(vals)
                        mv, mc = c2.most_common(1)[0]
                        conflicts += len(vals) - mc
                        template[(r0, c0)] = mv
                    if not ok:
                        break
                if not ok:
                    continue
                # Require the de-noised grid to be exactly periodic.
                if conflicts != 0:
                    continue
                # Prefer the smallest period; tie-break by amount of noise removed.
                key = (-(pr * pc), cnt[noise])
                if best is None or key > best[0]:
                    best = (key, noise, pr, pc, template)

    T = [[None] * W for _ in range(H)]
    if best is None:
        return T
    _, noise, pr, pc, template = best
    for r in range(H):
        for c in range(W):
            tv = template[(r % pr, c % pc)]
            if input_grid[r][c] != tv:
                T[r][c] = tv
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
