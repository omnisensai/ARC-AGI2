"""Canonical solver for ARC puzzle df978a02.

Scene: four arrow/wedge objects (one per non-background color) arranged around a
common center, each with a stem pointing toward that center. The single LARGEST
object advances one step away from the center, growing a new width-3 segment one
cell beyond its base (centered on its stem axis). Every other object retracts:
its tip cell (the cell furthest toward the center) is erased back to background.

infer_T computes, from the input alone, the latent change mask:
  {(r, c): new_color or None}  (None means erase that cell to background).
apply_T copies the input and overwrites only those masked cells.
"""


def _background(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if seen[rr][cc] or g[rr][cc] != col:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append((col, cells))
    return comps


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _background(g)
    comps = _components(g, bg)
    if not comps:
        return {}

    all_cells = [cell for _, cells in comps for cell in cells]
    gr = sum(r for r, _ in all_cells) / len(all_cells)
    gc = sum(c for _, c in all_cells) / len(all_cells)
    max_size = max(len(cells) for _, cells in comps)

    T = {}
    for col, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        cr = sum(rs) / len(rs)
        cc = sum(cs) / len(cs)
        dr, dc = cr - gr, cc - gc
        # Dominant axis direction pointing AWAY from the global center.
        if abs(dr) >= abs(dc):
            away = (1 if dr > 0 else -1, 0)
        else:
            away = (0, 1 if dc > 0 else -1)
        toward = (-away[0], -away[1])

        # Tip = the stem endpoint, i.e. the cell reaching furthest toward center.
        tip = max(cells, key=lambda rc: rc[0] * toward[0] + rc[1] * toward[1])

        if len(cells) == max_size:
            # Largest object advances away from center: emit a width-3 segment
            # one cell beyond its base edge, centered on the stem axis.
            if away[0] != 0:
                base_row = max(rs) if away[0] > 0 else min(rs)
                new_row = base_row + away[0]
                axis_c = tip[1]
                for c2 in (axis_c - 1, axis_c, axis_c + 1):
                    T[(new_row, c2)] = col
            else:
                base_col = max(cs) if away[1] > 0 else min(cs)
                new_col = base_col + away[1]
                axis_r = tip[0]
                for r2 in (axis_r - 1, axis_r, axis_r + 1):
                    T[(r2, new_col)] = col
        else:
            # Every other object retracts: erase its tip cell.
            T[tip] = None

    return T


def apply_T(input_grid, T):
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _background(g)
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = bg if v is None else v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
