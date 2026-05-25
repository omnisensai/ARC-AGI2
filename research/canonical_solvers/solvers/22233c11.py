def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def _components(g, color):
    H, W = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == color and (r, c) not in seen:
                st = [(r, c)]
                cells = []
                while st:
                    rr, cc = st.pop()
                    if (rr, cc) in seen:
                        continue
                    if not (0 <= rr < H and 0 <= cc < W) or g[rr][cc] != color:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        st.append((rr + dr, cc + dc))
                out.append(cells)
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def infer_T(input_grid):
    # The 3-colored cells form NxN square blocks. Blocks come in diagonal
    # "domino" pairs: two equal-size blocks touching at a corner, i.e. they
    # occupy two opposite quadrants of a 2Nx2N region. The transformation adds
    # an 8-block (same NxN size) for each EMPTY quadrant, pushed one block-step
    # further outward along the diagonal away from the domino center (clipped
    # to the grid).
    H, W = len(input_grid), len(input_grid[0])
    blocks = _components(input_grid, 3)
    boxes = [_bbox(b) for b in blocks]
    N = boxes[0][2] - boxes[0][0] + 1 if boxes else 1
    used = [False] * len(boxes)
    T = {}
    for i in range(len(boxes)):
        if used[i]:
            continue
        bi = boxes[i]
        for j in range(len(boxes)):
            if j == i or used[j]:
                continue
            bj = boxes[j]
            dr = bj[0] - bi[0]
            dc = bj[1] - bi[1]
            if abs(dr) == N and abs(dc) == N:
                used[i] = used[j] = True
                _emit_domino(bi, bj, N, H, W, T)
                break
    return T


def _emit_domino(bi, bj, N, H, W, T):
    r0 = min(bi[0], bj[0])
    c0 = min(bi[1], bj[1])
    filled = {(bi[0], bi[1]), (bj[0], bj[1])}
    slots = [(r0, c0), (r0, c0 + N), (r0 + N, c0), (r0 + N, c0 + N)]
    center_r = r0 + N - 0.5
    center_c = c0 + N - 0.5
    for (sr, sc) in slots:
        if (sr, sc) in filled:
            continue
        slot_center_r = sr + (N - 1) / 2.0
        slot_center_c = sc + (N - 1) / 2.0
        odr = 1 if slot_center_r > center_r else -1
        odc = 1 if slot_center_c > center_c else -1
        nr = sr + odr * N
        nc = sc + odc * N
        for rr in range(nr, nr + N):
            for cc in range(nc, nc + N):
                if 0 <= rr < H and 0 <= cc < W:
                    T[(rr, cc)] = 8


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    H, W = len(input_grid), len(input_grid[0])
    for (r, c), v in T.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v
    return out
