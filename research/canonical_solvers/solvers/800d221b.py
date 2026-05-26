"""Canonical latent-T solver for ARC puzzle 800d221b.

Rule (derived from ALL pairs):
  The grid has a background color (most common) and a wall/pipe color
  (second most common). The remaining colors form small two-color "key"
  patches placed at the ends of a pipe network. Each patch has a dominant
  color (its majority). The wall pipes are recolored: every pipe cell takes
  the dominant color of the patch it is connected to along the pipes.

  There is exactly one special 3x3 "junction" ring (its 8 border cells are
  all wall, surrounding a hollow center). The ring's 8 wall cells STAY wall
  and act as a barrier that separates the pipe networks of the different
  patches (so the same straight wall line can carry two different colors on
  opposite sides of the ring). The ring's center cell is recolored to the
  majority color among the recolored pipe cells immediately adjacent to the
  ring.

infer_T computes a mask T[(r,c)] = new_color for every cell that changes;
apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter, deque


def infer_T(input_grid):
    inp = input_grid
    H, W = len(inp), len(inp[0])

    # Identify background (most common) and wall/pipe color (second most common).
    counts = Counter(v for row in inp for v in row).most_common()
    bg = counts[0][0]
    wall = counts[1][0]
    keycolors = set(v for row in inp for v in row) - {bg, wall}

    # Find key patches: 8-connected components of key-colored cells.
    seen = [[False] * W for _ in range(H)]
    patches = []
    for r in range(H):
        for c in range(W):
            if inp[r][c] in keycolors and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = [(r, c)]
                while q:
                    y, x = q.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < H and 0 <= nx < W and not seen[ny][nx]
                                    and inp[ny][nx] in keycolors):
                                seen[ny][nx] = True
                                q.append((ny, nx))
                                cells.append((ny, nx))
                patches.append(cells)

    # Dominant color of each patch.
    doms = [Counter(inp[y][x] for y, x in cells).most_common(1)[0][0]
            for cells in patches]

    # Find the 3x3 junction ring: 8 wall border cells (center ignored).
    ring_origin = None
    for r in range(H - 2):
        for c in range(W - 2):
            border = [(r, c), (r, c + 1), (r, c + 2),
                      (r + 1, c), (r + 1, c + 2),
                      (r + 2, c), (r + 2, c + 1), (r + 2, c + 2)]
            if all(inp[y][x] == wall for y, x in border):
                ring_origin = (r, c)
    ringcells = set()
    rcenter = None
    if ring_origin is not None:
        r, c = ring_origin
        ringcells = {(r, c), (r, c + 1), (r, c + 2),
                     (r + 1, c), (r + 1, c + 2),
                     (r + 2, c), (r + 2, c + 1), (r + 2, c + 2)}
        rcenter = (r + 1, c + 1)

    # Multi-source BFS over wall cells, starting from cells adjacent to each
    # patch. The ring's border cells are barriers (they stay wall and are not
    # traversed), which keeps distinct pipe networks separate.
    INF = float("inf")
    dist = [[INF] * W for _ in range(H)]
    lab = [[None] * W for _ in range(H)]
    q = deque()
    for pi, cells in enumerate(patches):
        for (y, x) in cells:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < H and 0 <= nx < W and inp[ny][nx] == wall
                            and (ny, nx) not in ringcells and dist[ny][nx] == INF):
                        dist[ny][nx] = 0
                        lab[ny][nx] = pi
                        q.append((ny, nx))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if (0 <= ny < H and 0 <= nx < W and inp[ny][nx] == wall
                    and (ny, nx) not in ringcells and dist[ny][nx] == INF):
                dist[ny][nx] = dist[y][x] + 1
                lab[ny][nx] = lab[y][x]
                q.append((ny, nx))

    # Build the latent transformation mask: changed cell -> new color.
    T = {}
    for r in range(H):
        for c in range(W):
            if inp[r][c] == wall and (r, c) not in ringcells and lab[r][c] is not None:
                T[(r, c)] = doms[lab[r][c]]

    # Ring center: majority color among recolored pipe cells adjacent to the ring.
    if rcenter is not None:
        adj = Counter()
        for (y, x) in ringcells:
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if ((ny, nx) not in ringcells and 0 <= ny < H and 0 <= nx < W
                        and inp[ny][nx] == wall and lab[ny][nx] is not None):
                    adj[doms[lab[ny][nx]]] += 1
        if adj:
            T[rcenter] = adj.most_common(1)[0][0]

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
