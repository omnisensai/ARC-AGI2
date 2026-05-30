"""Micro-primitive family: gravity_to_wall.

One full edge (row 0, row H-1, col 0, or col W-1) is a solid stripe of a single
non-bg "wall" colour. Exactly one other object (a small blob of a different
colour) sits elsewhere on the bg. The object slides toward the wall along the
perpendicular axis until any of its cells is adjacent to the wall, then stops.

Generalises drop_to_floor (which only handles "down"); the wall edge dictates
the gravity direction. Only one object per task here — stacking-against-multiple
is a separate family (stack_against, not in this batch).

Tiers: 0 fixed 10x10, bg 0 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "gravity_to_wall"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


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
'''


def family_prompt_hint() -> str:
    return "Slide the object toward the wall (the full-edge stripe) until it touches the wall."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(9, 13); W = rng.randint(9, 13)

    if difficulty == 0:
        bg, wall_col, obj_col = 0, 5, 3
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, obj_col = rng.sample(avail, 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, obj_col = rng.sample(avail, 2)

    wall_dir = rng.choice(["top", "bottom", "left", "right"])
    inp = [[bg] * W for _ in range(H)]
    if wall_dir == "top":
        for c in range(W): inp[0][c] = wall_col
    elif wall_dir == "bottom":
        for c in range(W): inp[H - 1][c] = wall_col
    elif wall_dir == "left":
        for r in range(H): inp[r][0] = wall_col
    else:
        for r in range(H): inp[r][W - 1] = wall_col

    # Place a small object somewhere with margin to the wall.
    sz_r = rng.randint(1, 2); sz_c = rng.randint(1, 2)
    # margins: keep at least 2 cells of bg between the object and the wall
    if wall_dir == "top":
        r0 = rng.randint(3, H - sz_r - 1); c0 = rng.randint(1, W - sz_c - 1)
    elif wall_dir == "bottom":
        r0 = rng.randint(1, H - sz_r - 3); c0 = rng.randint(1, W - sz_c - 1)
    elif wall_dir == "left":
        r0 = rng.randint(1, H - sz_r - 1); c0 = rng.randint(3, W - sz_c - 1)
    else:
        r0 = rng.randint(1, H - sz_r - 1); c0 = rng.randint(1, W - sz_c - 3)
    cells = [(r0 + dr, c0 + dc) for dr in range(sz_r) for dc in range(sz_c)]
    for (y, x) in cells:
        inp[y][x] = obj_col

    # Build output: slide cells until adjacent to wall.
    dr, dc = {"top": (-1, 0), "bottom": (1, 0),
              "left": (0, -1), "right": (0, 1)}[wall_dir]
    wall_cells = set()
    if wall_dir == "top":    wall_cells = {(0, c) for c in range(W)}
    elif wall_dir == "bottom": wall_cells = {(H - 1, c) for c in range(W)}
    elif wall_dir == "left":   wall_cells = {(r, 0) for r in range(H)}
    else:                       wall_cells = {(r, W - 1) for r in range(H)}
    shift = 0
    while True:
        next_shift = shift + 1
        new_cells = [(y + dr * next_shift, x + dc * next_shift) for (y, x) in cells]
        if any(not (0 <= ny < H and 0 <= nx < W) or (ny, nx) in wall_cells
               for (ny, nx) in new_cells):
            break
        shift = next_shift

    out = [row[:] for row in inp]
    for (y, x) in cells:
        out[y][x] = bg
    for (y, x) in cells:
        ny, nx = y + dr * shift, x + dc * shift
        out[ny][nx] = obj_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
