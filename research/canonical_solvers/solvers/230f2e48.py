def _objects(g):
    """Connected components (4-neighbour) of non-background (non-7) cells."""
    H, W = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != 7 and (r, c) not in seen:
                st = [(r, c)]
                comp = []
                while st:
                    rr, cc = st.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W) or g[rr][cc] == 7:
                        continue
                    seen.add((rr, cc))
                    comp.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        st.append((rr + dr, cc + dc))
                comps.append(comp)
    return comps


def infer_T(input_grid):
    """Latent mask {(r,c): new_color}.

    Each object is a straight line of 2s with a single 5 endpoint and a single
    interior 0. The segment from the 5 end through the 0 is preserved; the tail
    (cells beyond the 0, on the side away from the 5) is erased and re-drawn
    perpendicular to the line, bending toward the grid centre, starting one cell
    adjacent to the 0 and keeping the same length.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    cr, cc = (H - 1) / 2.0, (W - 1) / 2.0
    T = {}
    for comp in _objects(g):
        fives = [x for x in comp if g[x[0]][x[1]] == 5]
        zeros = [x for x in comp if g[x[0]][x[1]] == 0]
        rows = set(r for r, c in comp)
        cols = set(c for r, c in comp)
        if len(fives) != 1 or len(zeros) != 1:
            continue
        if not (len(rows) == 1 or len(cols) == 1):
            continue
        fr, fc = fives[0]
        zr, zc = zeros[0]
        if len(cols) == 1:  # vertical line -> bend horizontally
            col = next(iter(cols))
            if zr > fr:
                tail = [(r, c) for (r, c) in comp if r > zr]
            else:
                tail = [(r, c) for (r, c) in comp if r < zr]
            n = len(tail)
            for (r, c) in tail:
                T[(r, c)] = 7
            step = 1 if col < cc else -1  # toward grid centre
            for k in range(1, n + 1):
                nc = zc + step * k
                if 0 <= nc < W:
                    T[(zr, nc)] = 2
        else:  # horizontal line -> bend vertically
            row = next(iter(rows))
            if zc > fc:
                tail = [(r, c) for (r, c) in comp if c > zc]
            else:
                tail = [(r, c) for (r, c) in comp if c < zc]
            n = len(tail)
            for (r, c) in tail:
                T[(r, c)] = 7
            step = 1 if row < cr else -1  # toward grid centre
            for k in range(1, n + 1):
                nr = zr + step * k
                if 0 <= nr < H:
                    T[(nr, zc)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
