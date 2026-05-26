def infer_T(input_grid):
    """Each connected 3-rectangle carries one marker (color 2) on one of its
    edges. The marker points outward (perpendicular to that edge). A band grows
    from the marker edge out to the grid boundary, centered on the marker along
    the edge, with half-width = (rectangle extent in the growth direction - 1).
    The band is color 3, except the marker's own line which is color 2.
    Returns a latent mask dict {(r,c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]

    def comp(sr, sc):
        st = [(sr, sc)]
        cells = []
        while st:
            r, c = st.pop()
            if r < 0 or c < 0 or r >= H or c >= W or seen[r][c] or input_grid[r][c] == 0:
                continue
            seen[r][c] = True
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                st.append((r + dr, c + dc))
        return cells

    T = {}
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0 and not seen[r][c]:
                cells = comp(r, c)
                markers = [(a, b) for a, b in cells if input_grid[a][b] == 2]
                if len(markers) != 1:
                    continue
                rs = [a for a, b in cells]
                cs = [b for a, b in cells]
                r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
                mr, mc = markers[0]
                # outward direction = perpendicular to the edge the marker lies on
                if mr == r0:
                    dr, dc, thick, vertical = -1, 0, r1 - r0 + 1, True
                elif mr == r1:
                    dr, dc, thick, vertical = 1, 0, r1 - r0 + 1, True
                elif mc == c0:
                    dr, dc, thick, vertical = 0, -1, c1 - c0 + 1, False
                elif mc == c1:
                    dr, dc, thick, vertical = 0, 1, c1 - c0 + 1, False
                else:
                    continue
                hw = thick - 1
                if vertical:  # grow up/down; band spans columns mc-hw .. mc+hw
                    rr = r0 - 1 if dr == -1 else r1 + 1
                    while 0 <= rr < H:
                        for cc in range(mc - hw, mc + hw + 1):
                            if 0 <= cc < W:
                                T[(rr, cc)] = 2 if cc == mc else 3
                        rr += dr
                else:  # grow left/right; band spans rows mr-hw .. mr+hw
                    cc = c0 - 1 if dc == -1 else c1 + 1
                    while 0 <= cc < W:
                        for rr in range(mr - hw, mr + hw + 1):
                            if 0 <= rr < H:
                                T[(rr, cc)] = 2 if rr == mr else 3
                        cc += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
