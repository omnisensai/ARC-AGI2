"""Canonical solver for ARC puzzle 9c1e755f.

Rule (same-size grid):
Each "L" gadget is a straight line of 5s (the ruler) with a small colored seed
block attached at one end, perpendicular to the line. The seed (a 1- or 2-thick
strip) is swept/tiled ALONG the line's axis, filling every position across the
line's full span. The seed's thickness along the line axis is the tiling period;
its perpendicular extent is preserved. Multiple independent Ls may coexist.

Canonical form: infer_T builds a latent mask {(r,c): new_color}; apply_T copies
the input and overwrites only the masked cells.
"""


def _components(grid, H, W, pred):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if pred(grid[r][c]) and not seen[r][c]:
                stack = [(r, c)]
                comp = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and pred(grid[nr][nc]) and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(comp)
    return comps


def _bbox(comp):
    rs = [r for r, c in comp]
    cs = [c for r, c in comp]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    lines = _components(input_grid, H, W, lambda v: v == 5)
    seeds = _components(input_grid, H, W, lambda v: v not in (0, 5))

    T = {}
    used = set()
    for line in lines:
        lr0, lr1, lc0, lc1 = _bbox(line)
        vert = (lr1 - lr0) >= (lc1 - lc0)  # is the line's axis vertical?

        # Pair this line with the nearest unused seed (the one forming its L).
        best = None
        best_d = None
        for idx, seed in enumerate(seeds):
            if idx in used:
                continue
            sr0, sr1, sc0, sc1 = _bbox(seed)
            if vert:
                d = min(abs(sr0 - lr1), abs(sr1 - lr0))
            else:
                d = min(abs(sc0 - lc1), abs(sc1 - lc0))
            if best_d is None or d < best_d:
                best_d = d
                best = (idx, seed)
        if best is None:
            continue
        idx, seed = best
        used.add(idx)

        tile = {(r, c): input_grid[r][c] for r, c in seed}
        sr0, sr1, sc0, sc1 = _bbox(seed)
        if vert:
            period = sr1 - sr0 + 1  # seed thickness along the (vertical) line axis
            for c in range(sc0, sc1 + 1):
                for r in range(lr0, lr1 + 1):
                    src = sr0 + ((r - lr0) % period)
                    if (src, c) in tile:
                        T[(r, c)] = tile[(src, c)]
        else:
            period = sc1 - sc0 + 1  # seed thickness along the (horizontal) line axis
            for r in range(sr0, sr1 + 1):
                for c in range(lc0, lc1 + 1):
                    src = sc0 + ((c - lc0) % period)
                    if (r, src) in tile:
                        T[(r, c)] = tile[(r, src)]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
