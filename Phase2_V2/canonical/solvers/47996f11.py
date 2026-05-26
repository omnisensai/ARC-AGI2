"""Canonical solver for ARC puzzle 47996f11.

Rule: The grid is a highly symmetric mosaic with a rectangular block of noise
(color 6) masking part of the pattern. Recover the masked cells by exploiting
the symmetries that the unmasked cells obey: reflection about a horizontal axis
(r -> A-r), reflection about a vertical axis (c -> B-c), the main-diagonal
transpose, the anti-diagonal flip, and 180-degree rotation. Only the symmetry
maps that hold *exactly* on every non-noise cell pair are kept (inferred from
the input alone). Each noise cell is then resolved by walking its orbit under
those valid maps until a non-noise cell is reached; that cell's color is copied
back. No global mirror is assumed -- the valid maps (e.g. offset reflection
axes) are discovered per input.
"""

NOISE = 6


def _apply_map(kind, par, r, c, H, W):
    if kind == 'row':
        return (par - r, c)
    if kind == 'col':
        return (r, par - c)
    if kind == 'transpose':
        return (c, r)
    if kind == 'antitrans':
        return (W - 1 - c, H - 1 - r)
    if kind == 'rot180':
        return (H - 1 - r, W - 1 - c)
    return None


def _valid_symmetries(inp):
    """Return the symmetry maps that hold on all non-noise cell pairs."""
    H, W = len(inp), len(inp[0])
    candidates = []
    for A in range(2 * H - 1):
        candidates.append(('row', A))
    for B in range(2 * W - 1):
        candidates.append(('col', B))
    candidates.append(('transpose', 0))
    candidates.append(('antitrans', 0))
    candidates.append(('rot180', 0))

    valid = []
    for kind, par in candidates:
        ok = True
        useful = False
        for r in range(H):
            for c in range(W):
                rr, cc = _apply_map(kind, par, r, c, H, W)
                if not (0 <= rr < H and 0 <= cc < W):
                    continue
                a = inp[r][c]
                b = inp[rr][cc]
                if a == NOISE or b == NOISE:
                    continue
                useful = True
                if a != b:
                    ok = False
                    break
            if not ok:
                break
        if ok and useful:
            valid.append((kind, par))
    return valid


def infer_T(input_grid):
    """Infer the latent repair mask: {(r, c): recovered_color} for noise cells."""
    H, W = len(input_grid), len(input_grid[0])
    valid = _valid_symmetries(input_grid)
    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != NOISE:
                continue
            seen = {(r, c)}
            stack = [(r, c)]
            found = None
            while stack:
                cr, cc = stack.pop()
                if input_grid[cr][cc] != NOISE:
                    found = input_grid[cr][cc]
                    break
                for kind, par in valid:
                    nr, nc = _apply_map(kind, par, cr, cc, H, W)
                    if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if found is not None:
                T[(r, c)] = found
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
