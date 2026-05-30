from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]

    # Identify the wall: a full edge whose cells are all one non-bg colour.
    def edge(name):
        if name == "top":    return [(0, c) for c in range(W)]
        if name == "bottom": return [(H - 1, c) for c in range(W)]
        if name == "left":   return [(r, 0) for r in range(H)]
        if name == "right":  return [(r, W - 1) for r in range(H)]
    wall_dir = None; wall_col = None
    for name in ("top", "bottom", "left", "right"):
        vals = {g[r][c] for r, c in edge(name)}
        if len(vals) == 1 and bg not in vals:
            wall_dir = name; wall_col = next(iter(vals)); break
    if wall_dir is None:
        return {}
    wall_cells = set(edge(wall_dir))

    # Object = the connected component(s) of non-bg, non-wall cells.
    seen = [[False] * W for _ in range(H)]
    for (r, c) in wall_cells:
        seen[r][c] = True
    obj = []
    for r in range(H):
        for c in range(W):
            if seen[r][c] or g[r][c] == bg:
                continue
            obj_col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == obj_col:
                        seen[ny][nx] = True; q.append((ny, nx))
            obj.append((obj_col, cells))
    if len(obj) != 1:
        return {}
    obj_col, cells = obj[0]

    # Direction vector toward the wall.
    dr, dc = {"top": (-1, 0), "bottom": (1, 0),
              "left": (0, -1), "right": (0, 1)}[wall_dir]
    # Slide until any cell is adjacent to the wall.
    shift = 0
    while True:
        next_shift = shift + 1
        new_cells = [(y + dr * next_shift, x + dc * next_shift) for (y, x) in cells]
        # Stop if any new cell would BE in the wall or out of bounds.
        if any(not (0 <= ny < H and 0 <= nx < W) or (ny, nx) in wall_cells
               for (ny, nx) in new_cells):
            break
        shift = next_shift

    T = {}
    new_cells = [(y + dr * shift, x + dc * shift) for (y, x) in cells]
    for (y, x) in cells:
        T[(y, x)] = bg
    for (y, x) in new_cells:
        T[(y, x)] = obj_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
