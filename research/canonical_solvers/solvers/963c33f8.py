"""Canonical latent-T solver for ARC puzzle 963c33f8.

Rule (inferred from all train+test pairs):
  - The grid contains a 3x3 "key" block made of colors 9 and 1 (top two rows are
    9, bottom row encodes a per-column tip color of 1 or 9), plus several 5-shapes.
  - The key is erased.
  - For each of the key's 3 columns (taken left-to-right) we emit one length-3
    vertical "ray" colored exactly like that key column read top->bottom, i.e.
    [9, 9, tip] where tip is the key's bottom cell for that column.
      * If the key column's tip is 1 AND there is a 5-cell somewhere below the key
        in that grid column, the ray points UP: it sits in the 3 cells directly
        above the topmost such 5-cell (so the tip `1` lands right on the shape).
      * Otherwise the ray points DOWN and occupies the bottom 3 rows of the grid:
          - free in the key column if no shape reaches the bottom band there;
          - if the shape cell in the key column inside the bottom band is part of a
            vertical run, the ray stays in that column (overwriting it);
          - if that shape cell is vertically isolated but the shape has a vertical
            run elsewhere, the ray snaps to the deepest vertical-run column;
          - if the shape is purely horizontal there, the ray stays and the shape's
            cells to the right (within the key width) are carved away.

infer_T returns a latent mask {(r,c): new_color}; apply_T overwrites those cells.
"""


def _components(grid):
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == 5 and (r, c) not in seen:
                stack = [(r, c)]
                comp = []
                while stack:
                    rr, cc = stack.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if grid[rr][cc] != 5:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    # Locate the key (block of 9/1 cells).
    key_cells = [(r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] in (9, 1)]
    if not key_cells:
        return T
    krs = [r for r, _ in key_cells]
    kcs = [c for _, c in key_cells]
    r0, r1, c0, c1 = min(krs), max(krs), min(kcs), max(kcs)
    key = [[input_grid[r][c] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]
    kh = r1 - r0 + 1

    # Erase the key.
    for r, c in key_cells:
        T[(r, c)] = 7

    comps = _components(input_grid)

    def comp_at(cell):
        for cp in comps:
            if cell in cp:
                return cp
        return None

    def place(col, base, vals):
        # vals top->bottom, with vals[-1] placed at row `base`.
        for k in range(kh):
            rr = base - (kh - 1 - k)
            if 0 <= rr < H:
                T[(rr, col)] = vals[k]

    for ci in range(c1 - c0 + 1):
        col = c0 + ci
        vals = [key[k][ci] for k in range(kh)]  # top -> bottom for this key column
        bottomval = vals[-1]

        # First 5-cell strictly below the key in this column.
        hit = None
        for r in range(r1 + 1, H):
            if input_grid[r][col] == 5:
                hit = r
                break

        if bottomval == 1 and hit is not None:
            # UP ray: sits directly above the shape, tip (1) adjacent to it.
            place(col, hit - 1, vals)
            continue

        # DOWN ray: occupies the bottom kh rows.
        bottom_rows = range(H - kh, H)
        obj_rows = [r for r in bottom_rows if input_grid[r][col] == 5]
        if not obj_rows:
            place(col, H - 1, vals)
            continue

        lr = max(obj_rows)
        cp = comp_at((lr, col))
        cpset = set(cp)
        in_vrun = (lr - 1, col) in cpset or (lr + 1, col) in cpset
        if in_vrun:
            place(col, H - 1, vals)
            continue

        # Vertically isolated landing cell: look for a vertical stem elsewhere.
        stems = {}
        for c in set(cc for _, cc in cp):
            rows = sorted(rr for rr, cc in cp if cc == c)
            runs = []
            start = rows[0]
            for j in range(1, len(rows)):
                if rows[j] != rows[j - 1] + 1:
                    runs.append((start, rows[j - 1]))
                    start = rows[j]
            runs.append((start, rows[-1]))
            best = max(runs, key=lambda x: x[1] - x[0])
            if best[1] - best[0] + 1 >= 2:
                stems[c] = best[1]
        if stems:
            rc = max(stems, key=lambda c: (stems[c], -abs(c - col)))
            place(rc, H - 1, vals)
        else:
            # Purely horizontal shape: stay in column, carve the cells to the right.
            place(col, H - 1, vals)
            for dd in range(1, kh):
                cc = col + dd
                if cc < W and (lr, cc) in cpset:
                    T[(lr, cc)] = 7

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
