from collections import Counter, deque


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)


def infer_T(input_grid):
    """Infer the latent fill mask.

    The grid is partitioned by a 'frame' color (lines / nested rectangles) into
    rectangular 'rooms' (4-connected components of non-frame cells; a room that
    encloses a child box is naturally produced as a rectangle-with-a-hole).
    Each room is painted with concentric rings: the ring index of a cell is its
    8-connected distance to the nearest non-room cell (room wall, grid edge, or
    inner child box). The per-ring colors are taken from the diagonal marker
    pixels that sit in the room -- each marker anchors the color of the ring it
    occupies; rings with no marker stay background; the resulting prefix of ring
    colors cycles outward-to-inward.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    cnt = Counter(v for row in g for v in row)
    bg = cnt.most_common(1)[0][0]
    frame = cnt.most_common(2)[1][0]

    # Rooms = 4-connected components of non-frame cells.
    seen = [[False] * W for _ in range(H)]
    rooms = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != frame and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    a, b = q.popleft()
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + da, b + db
                        if 0 <= na < H and 0 <= nb < W and not seen[na][nb] and g[na][nb] != frame:
                            seen[na][nb] = True
                            q.append((na, nb))
                rooms.append(cells)

    T = [[None] * W for _ in range(H)]
    for cells in rooms:
        roomset = set(cells)

        # Ring index = 8-connected distance from the room boundary.
        dist = {}
        q = deque()
        for (a, b) in cells:
            on_edge = any(
                not (0 <= a + da < H and 0 <= b + db < W) or (a + da, b + db) not in roomset
                for da in (-1, 0, 1) for db in (-1, 0, 1) if (da, db) != (0, 0)
            )
            if on_edge:
                dist[(a, b)] = 0
                q.append((a, b))
        while q:
            a, b = q.popleft()
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    if (da, db) == (0, 0):
                        continue
                    na, nb = a + da, b + db
                    if (na, nb) in roomset and (na, nb) not in dist:
                        dist[(na, nb)] = dist[(a, b)] + 1
                        q.append((na, nb))

        # Marker pixels anchor the color of the ring they occupy.
        ring_color = {}
        for (a, b) in cells:
            v = g[a][b]
            if v != bg and v != frame:
                ring_color[dist[(a, b)]] = v

        if ring_color:
            top = max(ring_color)
            seq = [ring_color.get(k, bg) for k in range(top + 1)]
        else:
            seq = [bg]

        for (a, b) in cells:
            T[a][b] = seq[dist[(a, b)] % len(seq)]

    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out
