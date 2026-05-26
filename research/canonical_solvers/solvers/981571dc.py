"""Canonical solver for ARC puzzle 981571dc.

Rule: the grid is a symmetric texture corrupted by rectangular blocks of holes
(color 0). Recover the symmetry group of the picture from the surviving
non-hole cells (the global transpose / anti-transpose plus the vertical and
horizontal mirror axes that hold with zero conflicts), then fill every hole
with the majority color found over its symmetry orbit.

Canonical latent-T form: infer_T returns a {(r,c): color} mask of the cells to
overwrite; apply_T copies the input and writes only those masked cells.
"""

from collections import Counter

HOLE = 0


def _mirror_v_axes(grid, H, W):
    """Vertical mirror axes a = c1 + c2 that are conflict-free over non-holes."""
    axes = []
    for a in range(0, 2 * W - 1):
        ok = 0
        bad = False
        for r in range(H):
            row = grid[r]
            for c in range(W):
                if row[c] == HOLE:
                    continue
                c2 = a - c
                if not (0 <= c2 < W) or row[c2] == HOLE:
                    continue
                if row[c] != row[c2]:
                    bad = True
                    break
                ok += 1
            if bad:
                break
        if not bad and ok >= 2 * H:
            axes.append(a)
    return axes


def _mirror_h_axes(grid, H, W):
    """Horizontal mirror axes a = r1 + r2 that are conflict-free over non-holes."""
    axes = []
    for a in range(0, 2 * H - 1):
        ok = 0
        bad = False
        for r in range(H):
            r2 = a - r
            inb = 0 <= r2 < H
            for c in range(W):
                if grid[r][c] == HOLE:
                    continue
                if not inb or grid[r2][c] == HOLE:
                    continue
                if grid[r][c] != grid[r2][c]:
                    bad = True
                    break
                ok += 1
            if bad:
                break
        if not bad and ok >= 2 * W:
            axes.append(a)
    return axes


def _diag_ok(grid, H, W, fn):
    """True if diagonal map fn is conflict-free over non-hole cells (and useful)."""
    ok = 0
    for r in range(H):
        for c in range(W):
            if grid[r][c] == HOLE:
                continue
            nr, nc = fn(r, c)
            if not (0 <= nr < H and 0 <= nc < W) or grid[nr][nc] == HOLE:
                continue
            if grid[r][c] != grid[nr][nc]:
                return False
            ok += 1
    return ok > 0


def _detect_symmetries(grid, H, W):
    """Infer the symmetry maps (r,c)->(r',c') that the picture obeys."""
    syms = []
    if H == W:
        if _diag_ok(grid, H, W, lambda r, c: (c, r)):
            syms.append(lambda r, c: (c, r))
        if _diag_ok(grid, H, W, lambda r, c: (W - 1 - c, H - 1 - r)):
            syms.append(lambda r, c: (W - 1 - c, H - 1 - r))
    for a in _mirror_v_axes(grid, H, W):
        syms.append((lambda a: (lambda r, c: (r, a - c)))(a))
    for a in _mirror_h_axes(grid, H, W):
        syms.append((lambda a: (lambda r, c: (a - r, c)))(a))
    return syms


def _orbit(r, c, H, W, syms):
    """Closure of (r,c) under the inferred symmetry maps."""
    seen = {(r, c)}
    stack = [(r, c)]
    while stack:
        rr, cc = stack.pop()
        for f in syms:
            nr, nc = f(rr, cc)
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def infer_T(input_grid):
    """Compute the latent repair mask {(r,c): color} for the hole cells."""
    H, W = len(input_grid), len(input_grid[0])
    syms = _detect_symmetries(input_grid, H, W)
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != HOLE:
                continue
            counts = Counter()
            for (rr, cc) in _orbit(r, c, H, W, syms):
                v = input_grid[rr][cc]
                if v != HOLE:
                    counts[v] += 1
            if counts:
                T[(r, c)] = counts.most_common(1)[0][0]
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked (hole) cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
