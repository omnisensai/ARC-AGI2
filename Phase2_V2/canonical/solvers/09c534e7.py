def infer_T(input_grid):
    """Latent transformation mask {(r,c): new_color}.

    Structure: the grid contains networks of box outlines drawn in 1s, joined
    by 1-pixel bridges. Each 4-connected network of nonzero cells contains
    exactly one colored marker cell (value not in {0,1}). The transformation
    fills every INTERIOR cell of that network (a 1-cell whose full 8-neighbour
    ring is all nonzero, i.e. inside a box) with the network's marker color.
    """
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    # 4-connected components over all nonzero cells; record the marker per comp.
    comp_id = [[-1] * W for _ in range(H)]
    comp_marker = {}
    cid = 0
    for sr in range(H):
        for sc in range(W):
            if g[sr][sc] != 0 and comp_id[sr][sc] == -1:
                stack = [(sr, sc)]
                marker = None
                while stack:
                    r, c = stack.pop()
                    if not (0 <= r < H and 0 <= c < W):
                        continue
                    if g[r][c] == 0 or comp_id[r][c] != -1:
                        continue
                    comp_id[r][c] = cid
                    if g[r][c] != 1:
                        marker = g[r][c]
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((r + dr, c + dc))
                comp_marker[cid] = marker
                cid += 1

    # Interior cells: value 1 with a fully-nonzero 3x3 neighbourhood.
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 1:
                continue
            full = True
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < H and 0 <= nc < W) or g[nr][nc] == 0:
                        full = False
                        break
                if not full:
                    break
            if full:
                m = comp_marker[comp_id[r][c]]
                if m is not None:
                    T[(r, c)] = m
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
