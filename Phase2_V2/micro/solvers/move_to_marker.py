from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if len(nz) < 2:
        return {}
    M = min(nz, key=lambda k: nz[k])              # marker = rarest non-bg (single cell)
    mr, mc = next((r, c) for r in range(H) for c in range(W) if g[r][c] == M)
    obj = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg and g[r][c] != M]
    if not obj:
        return {}
    or0 = min(r for r, c in obj); oc0 = min(c for r, c in obj)
    dr, dc = mr - or0, mc - oc0
    T = {}
    for (r, c) in obj:
        T[(r, c)] = bg                            # clear old object
    T[(mr, mc)] = bg                              # clear the consumed marker
    for (r, c) in obj:
        T[(r + dr, c + dc)] = g[r][c]             # draw at destination (overrides)
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
