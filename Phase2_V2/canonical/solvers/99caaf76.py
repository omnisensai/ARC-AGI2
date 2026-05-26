"""Canonical solver for ARC puzzle 99caaf76.

Rule: The grid (background 8) contains one or more "creatures". Each creature is
an 8-connected component made of:
  - a CROSS / head: a center cell colored 4 plus its 4 orthogonal arm cells
    (non-background, non-1 colors);
  - a TAIL: a short stem of 1s extending from the cross in one direction, ending
    in a split (two 1s).
The tail points in a direction D (away from the cross). The creature moves in its
HEAD direction (-D) and slides until its leading edge touches the grid wall.
During the move the head/cross is rotated 180 degrees (its arm colors swap
up<->down and left<->right) while the tail keeps its shape and orientation.

Canonical latent-T form: infer_T builds the explicit overwrite mask
{(r,c): new_color} (cleared source cells -> background, transformed cells ->
their color); apply_T copies the input and overwrites only the masked cells.
"""


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = 8

    # 8-connected components of non-background cells.
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W
                                    and g[nr][nc] != bg and not seen[nr][nc]):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                comps.append(comp)

    sets = {}  # latent transformation mask: (r,c) -> new color
    for comp in comps:
        # The cross center is the unique cell colored 4.
        center = next(((r, c) for (r, c) in comp if g[r][c] == 4), None)
        if center is None:
            continue
        cr, cc = center

        # Cross = center + orthogonal colored arms (exclude tail 1s).
        cross = {(cr, cc): g[cr][cc]}
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = cr + dr, cc + dc
            if (0 <= nr < H and 0 <= nc < W
                    and g[nr][nc] != bg and g[nr][nc] != 1):
                cross[(nr, nc)] = g[nr][nc]

        # Tail = the 1 cells of the component.
        tail = [(r, c) for (r, c) in comp if g[r][c] == 1]
        if not tail:
            continue

        # Tail direction D = from cross center toward the tail's centroid.
        tr = sum(r for r, _ in tail) / len(tail) - cr
        tc = sum(c for _, c in tail) / len(tail) - cc
        if abs(tr) >= abs(tc):
            D = (1 if tr > 0 else -1, 0)
        else:
            D = (0, 1 if tc > 0 else -1)
        head = (-D[0], -D[1])  # head/movement direction

        # Transformed (untranslated) object: rotate cross 180 about its center,
        # keep the tail as-is.
        new = {}
        for (r, c), v in cross.items():
            new[(cr - (r - cr), cc - (c - cc))] = v
        for (r, c) in tail:
            new[(r, c)] = 1

        # Slide in the head direction until the leading edge touches the wall.
        if head[0] != 0:
            rows = [r for r, _ in new]
            shift = (-min(rows), 0) if head[0] < 0 else (H - 1 - max(rows), 0)
        else:
            cols = [c for _, c in new]
            shift = (0, -min(cols)) if head[1] < 0 else (0, W - 1 - max(cols))

        # Clear the original cells, then place the moved object.
        for (r, c) in comp:
            sets[(r, c)] = bg
        for (r, c), v in new.items():
            sets[(r + shift[0], c + shift[1])] = v

    return sets


def apply_T(g, T):
    out = [row[:] for row in g]
    H, W = len(g), len(g[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
