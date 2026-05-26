from collections import deque

NB8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
NB4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def infer_T(input_grid):
    """Latent mask: for each object (8-connected non-bg blob) wrap it in a 2
    outline; if the object encloses background holes recolor the object to 8 and
    the holes to 6; otherwise the object keeps its color."""
    g = input_grid
    H, W = len(g), len(g[0])
    cnt = {}
    for row in g:
        for v in row:
            cnt[v] = cnt.get(v, 0) + 1
    bg = max(cnt, key=cnt.get)

    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                st = [(r, c)]
                cells = []
                seen[r][c] = True
                while st:
                    y, x = st.pop()
                    cells.append((y, x))
                    for dy, dx in NB8:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != bg and not seen[ny][nx]:
                            seen[ny][nx] = True
                            st.append((ny, nx))
                cellset = set(cells)
                rs = [a for a, b in cells]
                cs = [b for a, b in cells]
                r0, r1 = min(rs) - 1, max(rs) + 1
                c0, c1 = min(cs) - 1, max(cs) + 1

                # background cells within the padded bounding box
                bgset = set(
                    (a, b)
                    for a in range(r0, r1 + 1)
                    for b in range(c0, c1 + 1)
                    if 0 <= a < H and 0 <= b < W and (a, b) not in cellset and g[a][b] == bg
                )
                # flood from the bbox border (4-connectivity) -> the "outside" bg
                reach = set()
                dq = deque()
                for a in range(r0, r1 + 1):
                    for b in range(c0, c1 + 1):
                        if (a == r0 or a == r1 or b == c0 or b == c1) and (a, b) in bgset:
                            reach.add((a, b))
                            dq.append((a, b))
                while dq:
                    y, x = dq.popleft()
                    for dy, dx in NB4:
                        nb = (y + dy, x + dx)
                        if nb in bgset and nb not in reach:
                            reach.add(nb)
                            dq.append(nb)
                holes = bgset - reach

                obj_color = 8 if holes else g[cells[0][0]][cells[0][1]]
                for (a, b) in cells:
                    T[(a, b)] = obj_color
                for (a, b) in holes:
                    T[(a, b)] = 6
                # outer 2-outline: background cells 8-adjacent to the object,
                # excluding interior holes
                for (a, b) in cells:
                    for dy, dx in NB8:
                        na, nb = a + dy, b + dx
                        if 0 <= na < H and 0 <= nb < W and g[na][nb] == bg and (na, nb) not in holes:
                            T[(na, nb)] = 2
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
