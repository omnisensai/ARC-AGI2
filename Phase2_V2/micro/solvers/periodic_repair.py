def infer_T(g):
    H, W = len(g), len(g[0])

    def consistent(pr, pc):
        seen = {}
        for r in range(H):
            for c in range(W):
                v = g[r][c]
                if v == 0:
                    continue
                k = (r % pr, c % pc)
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    pr = pc = None
    for a in range(1, H + 1):
        done = False
        for b in range(1, W + 1):
            if consistent(a, b):
                pr, pc = a, b; done = True; break
        if done:
            break
    template = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                template[(r % pr, c % pc)] = g[r][c]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0:
                k = (r % pr, c % pc)
                if k in template:
                    T[(r, c)] = template[k]
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
