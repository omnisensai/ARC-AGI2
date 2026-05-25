"""Canonical solver for ARC puzzle 36a08778.

Rule (verified on ALL train+test pairs):
  The grid contains vertical 2-cell markers of color 6 (each pointing DOWN)
  and horizontal/L-shaped bars of color 2 on a background of 7.
  From the tip of each marker a "ray" travels downward. Whenever a ray meets
  a bar (a connected run of 2s) it wraps the bar with a 3-sided bracket:
    - a horizontal cap of 6 drawn one row above the contact, spanning the
      bar's horizontal run extended by one cell on each side (2-cells kept),
    - two new rays spawned at the cap's two end columns, each continuing
      downward and wrapping any further bars they meet.
  Rays stop at the grid bottom or when they merge into an existing 6.
  Bars not lying under any ray column are left untouched.

infer_T computes the latent mask (cells that become 6) from the input alone;
apply_T copies the input and overwrites only the masked cells.
"""


def _components(grid, val):
    """4-connected components of cells equal to `val`."""
    H, W = len(grid), len(grid[0])
    cells = set((r, c) for r in range(H) for c in range(W) if grid[r][c] == val)
    seen, comps = set(), []
    for s in cells:
        if s in seen:
            continue
        comp, stack = [], [s]
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.append(x)
            r, c = x
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((r + dr, c + dc))
        comps.append(comp)
    return comps


def infer_T(input_grid):
    """Return the latent mask: a set of (r, c) cells that must become color 6."""
    H, W = len(input_grid), len(input_grid[0])
    is2 = [[input_grid[r][c] == 2 for c in range(W)] for r in range(H)]

    mask = set()  # cells to paint 6

    def is6(r, c):
        return input_grid[r][c] == 6 or (r, c) in mask

    # Each marker is a 2-cell vertical line of 6 pointing down; spawn a ray
    # from its lower tip moving downward.
    rays = []
    for m in _components(input_grid, 6):
        col = m[0][1]
        tip_row = max(r for r, _ in m)
        rays.append((tip_row + 1, col))

    stack = list(rays)
    guard = 0
    while stack:
        guard += 1
        if guard > 1_000_000:
            break
        r, c = stack.pop()
        if not (0 <= c < W):
            continue
        cr = r
        while True:
            if cr >= H:
                break  # ran off the bottom edge
            if is2[cr][c]:
                # Contact with a bar: wrap with a cap one row above.
                bl = br = c
                while bl - 1 >= 0 and is2[cr][bl - 1]:
                    bl -= 1
                while br + 1 < W and is2[cr][br + 1]:
                    br += 1
                cap_row = cr - 1
                if cap_row < 0:
                    break
                lcol, rcol = max(0, bl - 1), min(W - 1, br + 1)
                for cc in range(lcol, rcol + 1):
                    if not is2[cap_row][cc]:
                        mask.add((cap_row, cc))
                # Spawn the two arm rays at the cap's end columns.
                for acol in (bl - 1, br + 1):
                    if 0 <= acol < W:
                        stack.append((cap_row + 1, acol))
                break
            if cr != r and is6(cr, c):
                break  # merged into an existing 6 structure
            mask.add((cr, c))
            cr += 1
    return mask


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells with color 6."""
    out = [row[:] for row in input_grid]
    for (r, c) in T:
        out[r][c] = 6
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
