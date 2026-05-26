HOLE = 2


def _candidate_symmetries(H, W):
    """Symmetry maps that may hold for the underlying (hole-free) pattern."""
    syms = [
        lambda r, c: (H - 1 - r, c),          # horizontal mirror (flip rows)
        lambda r, c: (r, W - 1 - c),          # vertical mirror (flip cols)
        lambda r, c: (H - 1 - r, W - 1 - c),  # 180 rotation
    ]
    if H == W:
        syms.append(lambda r, c: (c, r))                  # main-diagonal transpose
        syms.append(lambda r, c: (W - 1 - c, H - 1 - r))  # anti-diagonal transpose
    return syms


def _valid_syms(grid):
    """Keep only symmetries consistent with every non-hole cell."""
    H, W = len(grid), len(grid[0])
    good = []
    for f in _candidate_symmetries(H, W):
        ok = True
        for r in range(H):
            for c in range(W):
                rr, cc = f(r, c)
                a, b = grid[r][c], grid[rr][cc]
                if a == HOLE or b == HOLE:
                    continue
                if a != b:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            good.append(f)
    return good


def infer_T(input_grid):
    """Latent repair mask: for each hole (color 2), recover its color by walking
    the orbit of valid grid symmetries until a non-hole counterpart is found."""
    H, W = len(input_grid), len(input_grid[0])
    syms = _valid_syms(input_grid)
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != HOLE:
                continue
            val = None
            seen = set()
            stack = [(r, c)]
            while stack:
                pr, pc = stack.pop()
                if (pr, pc) in seen:
                    continue
                seen.add((pr, pc))
                if input_grid[pr][pc] != HOLE:
                    val = input_grid[pr][pc]
                    break
                for f in syms:
                    stack.append(f(pr, pc))
            if val is not None:
                T[(r, c)] = val
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
