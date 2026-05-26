"""Canonical solver for ARC puzzle 7b0280bc.

Rule
----
The grid contains a network of "snakes": solid square *blocks* of two colors
connected by thin *path* lines of a third (connector) color, all drawn over a
uniform background.

  * The connector color forms long / irregular connected components (the path
    lines).  Every other non-background color forms perfectly-square solid
    components (the blocks).
  * Of the two block colors, the one with the fewest components (always two)
    is the *marker* color; the other is the *main* block color.

Treating each block as a graph node and each path component as an edge between
the two blocks it touches, we trace the shortest path between the two marker
blocks.  Along that traced path we recolor:

  * every traversed path (connector) segment -> 5
  * every traversed *main* block             -> 3
  * marker blocks stay unchanged.

Everything off the traced path is left as-is.
"""

from collections import Counter, deque


def _bg(grid):
    cnt = Counter(v for row in grid for v in row)
    return cnt.most_common(1)[0][0]


def _color_components(grid, color, bg):
    """8-connected components of a single color."""
    H, W = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cells = []
                while q:
                    a, b = q.popleft()
                    cells.append((a, b))
                    for da in (-1, 0, 1):
                        for db in (-1, 0, 1):
                            if da == 0 and db == 0:
                                continue
                            na, nb = a + da, b + db
                            if (0 <= na < H and 0 <= nb < W
                                    and grid[na][nb] == color
                                    and (na, nb) not in seen):
                                seen.add((na, nb))
                                q.append((na, nb))
                comps.append(cells)
    return comps


def _is_square(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    return h == w and len(cells) == h * w


def infer_T(input_grid):
    """Compute the latent transformation mask {(r, c): new_color}."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    colors = set(v for row in input_grid for v in row) - {bg}

    # Classify colors: block colors have all-square components; the connector
    # (path) color is the remaining one with irregular components.
    block_colors = []
    path_color = None
    for col in colors:
        comps = _color_components(input_grid, col, bg)
        if comps and all(_is_square(c) for c in comps):
            block_colors.append(col)
        else:
            path_color = col

    T = {}
    if path_color is None or len(block_colors) < 2:
        return T

    # marker color = block color with the fewest components.
    ncomp = {col: len(_color_components(input_grid, col, bg)) for col in block_colors}
    min_n = min(ncomp.values())
    marker_colors = set(col for col in block_colors if ncomp[col] == min_n)

    # Enumerate block objects (nodes).
    blocks = []  # (color, set(cells))
    for col in block_colors:
        for cells in _color_components(input_grid, col, bg):
            blocks.append((col, set(cells)))

    cell2block = {}
    for bi, (_, cells) in enumerate(blocks):
        for cc in cells:
            cell2block[cc] = bi

    # Path components (edges): each connects the blocks it is adjacent to.
    edges = []  # (cells, sorted adjacent block ids)
    for cells in _color_components(input_grid, path_color, bg):
        adj = set()
        for a, b in cells:
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    n = (a + da, b + db)
                    if n in cell2block:
                        adj.add(cell2block[n])
        edges.append((cells, sorted(adj)))

    # Block adjacency graph (only edges joining exactly two blocks).
    graph = {i: [] for i in range(len(blocks))}
    for ei, (_, adj) in enumerate(edges):
        if len(adj) == 2:
            graph[adj[0]].append((adj[1], ei))
            graph[adj[1]].append((adj[0], ei))

    marker_blocks = [bi for bi, (v, _) in enumerate(blocks) if v in marker_colors]
    if len(marker_blocks) != 2:
        return T

    # Shortest path between the two marker blocks (BFS).
    s, t = marker_blocks
    prev = {s: None}
    q = deque([s])
    while q:
        u = q.popleft()
        for v2, ei in graph[u]:
            if v2 not in prev:
                prev[v2] = (u, ei)
                q.append(v2)
    if t not in prev:
        return T

    path_nodes = set()
    path_edges = set()
    cur = t
    while cur != s:
        u, ei = prev[cur]
        path_nodes.add(cur)
        path_edges.add(ei)
        cur = u
    path_nodes.add(s)

    # Build mask: main blocks -> 3, path segments -> 5, markers unchanged.
    for bi in path_nodes:
        col, cells = blocks[bi]
        if col not in marker_colors:
            for r, c in cells:
                T[(r, c)] = 3
    for ei in path_edges:
        for r, c in edges[ei][0]:
            T[(r, c)] = 5

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
