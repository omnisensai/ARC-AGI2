from collections import Counter


def infer_T(input_grid):
    """Infer a latent stamp mask {(r,c): color}.

    Structure: a background color, a single foreground shape color, and a
    short line of 4s (the 'ruler' marker) on one edge. The marker projects
    perpendicularly across the grid, leaving a clean ruler in its own band
    (the columns/rows it spans): the band is cleared to background except on
    every 2nd line (a 'stamp'), where it is painted. Stamps are color 4,
    except every 3rd stamp which is color 3. On a 3-stamp line, every
    foreground cell in that whole line is also recolored to 3.
    """
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]
    fg = None
    for v, _ in cnt.most_common():
        if v != bg and v != 4:
            fg = v
            break

    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    T = {}
    if not fours:
        return T

    rows = set(r for r, c in fours)
    cols = set(c for r, c in fours)
    horizontal = len(rows) == 1  # marker line lies along a single row

    if horizontal:
        mr = next(iter(rows))
        band = sorted(cols)
        scan_down = (mr == 0)
        order = range(mr, H) if scan_down else range(mr, -1, -1)
        k = 0
        for r in order:
            if abs(r - mr) % 2 == 0:                 # stamp line
                color = 3 if k % 3 == 2 else 4
                for c in band:
                    T[(r, c)] = color
                if color == 3:
                    for c in range(W):
                        if input_grid[r][c] == fg:
                            T[(r, c)] = 3
                k += 1
            else:                                    # gap line: clear band
                for c in band:
                    T[(r, c)] = bg
    else:
        mc = next(iter(cols))
        band = sorted(rows)
        scan_right = (mc == 0)
        order = range(mc, W) if scan_right else range(mc, -1, -1)
        k = 0
        for c in order:
            if abs(c - mc) % 2 == 0:                 # stamp line
                color = 3 if k % 3 == 2 else 4
                for r in band:
                    T[(r, c)] = color
                if color == 3:
                    for r in range(H):
                        if input_grid[r][c] == fg:
                            T[(r, c)] = 3
                k += 1
            else:                                    # gap line: clear band
                for r in band:
                    T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
