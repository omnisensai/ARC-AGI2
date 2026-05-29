"""Micro-primitive family: fit_piece_to_hole (ghost + 2 pieces variant).

Input has:
  - Two SOLID pieces of DIFFERENT shapes (and different colours)
  - One SOLID "ghost" of the same shape as EXACTLY ONE of the pieces
    (different colour from both pieces)
  - No marker — the matching itself disambiguates (shape uniquely identifies
    which piece corresponds to which ghost)

Rule: the piece whose shape matches the ghost is the SOURCE. Output:
  - source's cells  -> bg
  - ghost's cells   -> source's colour (ghost is "filled in" with the piece)
  - non-matching piece stays put

Works for rectangles AND irregular shapes.

Tiers: 0 fixed 13x13 rect | 1 + colour/bg | 2 irregular blobs.
"""
import random

FAMILY = "fit_piece_to_hole"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def _components_by_colour(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True; q.append((ny, nx))
            comps.append((col, cells))
    return comps


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    if len(comps) != 3:
        return {}
    # Find a pair of components with matching normalized shape.
    pairs = []
    for i in range(3):
        for j in range(i + 1, 3):
            if _normalize(comps[i][1]) == _normalize(comps[j][1]):
                pairs.append((i, j))
    if len(pairs) != 1:
        return {}
    i, j = pairs[0]
    # The third component is the non-matching piece (irrelevant); pick one of
    # the matching pair as ghost (destination) and the other as source. We use
    # the deterministic rule: source = the one whose top-left (row, col) is
    # smaller. This makes the rule reversible from the data without an
    # explicit marker.
    a_cells = comps[i][1]; b_cells = comps[j][1]
    a_tl = (min(r for r, _ in a_cells), min(c for _, c in a_cells))
    b_tl = (min(r for r, _ in b_cells), min(c for _, c in b_cells))
    if a_tl < b_tl:
        src = comps[i]; dst = comps[j]
    else:
        src = comps[j]; dst = comps[i]
    src_col, src_cells = src
    dst_col, dst_cells = dst

    T = {}
    for (y, x) in src_cells:
        T[(y, x)] = bg
    for (y, x) in dst_cells:
        T[(y, x)] = src_col
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
    return ("Of the three solid shapes, two have the same shape. The top-left "
            "one (the source) moves into the other (the destination), which "
            "takes the source's colour; the third piece is untouched.")


def _shape_rect(rng, max_dim):
    h = rng.randint(2, max_dim); w = rng.randint(2, max_dim)
    return frozenset((r, c) for r in range(h) for c in range(w))


def _shape_blob(rng, max_dim):
    h = rng.randint(2, max_dim); w = rng.randint(2, max_dim)
    cells = {(r, c) for r in range(h) for c in range(w)}
    for _ in range(rng.randint(1, 3)):
        cs = list(cells)
        y, x = rng.choice(cs)
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if ny >= 0 and nx >= 0:
            cells.add((ny, nx))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _place(rng, H, W, shape_cells, occupied, margin=1):
    sh = max(r for r, _ in shape_cells) + 1
    sw = max(c for _, c in shape_cells) + 1
    if H - sh < 0 or W - sw < 0:
        return None
    for _ in range(80):
        r0 = rng.randint(0, H - sh); c0 = rng.randint(0, W - sw)
        placed = {(r0 + r, c0 + c) for (r, c) in shape_cells}
        halo = {(y + dy, x + dx) for (y, x) in placed
                for dy in range(-margin, margin + 1)
                for dx in range(-margin, margin + 1)}
        if not (halo & occupied):
            return placed
    return None


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 13
    else:
        H = rng.randint(13, 16); W = rng.randint(13, 16)

    if difficulty == 0:
        bg, src_col, dst_col, other_col = 0, 2, 4, 7
        shape_A = frozenset((r, c) for r in range(2) for c in range(2))
        shape_B = frozenset((r, c) for r in range(3) for c in range(2))
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        src_col, dst_col, other_col = rng.sample(avail, 3)
        for _ in range(10):
            shape_A = _shape_rect(rng, 3)
            shape_B = _shape_rect(rng, 3)
            if shape_A != shape_B: break
        else:
            shape_A = frozenset((r, c) for r in range(2) for c in range(2))
            shape_B = frozenset((r, c) for r in range(3) for c in range(2))
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        src_col, dst_col, other_col = rng.sample(avail, 3)
        for _ in range(10):
            shape_A = _shape_blob(rng, 4) if rng.random() < 0.5 else _shape_rect(rng, 3)
            shape_B = _shape_blob(rng, 4) if rng.random() < 0.5 else _shape_rect(rng, 3)
            if shape_A != shape_B: break
        else:
            shape_A = frozenset((r, c) for r in range(2) for c in range(2))
            shape_B = frozenset((r, c) for r in range(3) for c in range(2))

    occupied = set()
    # source: shape_A (top-left will be smallest)
    src_placed = _place(rng, H, W, shape_A, occupied, margin=1)
    if src_placed is None: return _instance(rng, difficulty)
    occupied |= {(y + dy, x + dx) for (y, x) in src_placed
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
    dst_placed = _place(rng, H, W, shape_A, occupied, margin=1)
    if dst_placed is None: return _instance(rng, difficulty)
    occupied |= {(y + dy, x + dx) for (y, x) in dst_placed
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
    other_placed = _place(rng, H, W, shape_B, occupied, margin=1)
    if other_placed is None: return _instance(rng, difficulty)

    # Enforce source has smaller (top-left row, col) than destination.
    src_tl = (min(r for r, _ in src_placed), min(c for _, c in src_placed))
    dst_tl = (min(r for r, _ in dst_placed), min(c for _, c in dst_placed))
    if src_tl > dst_tl:
        src_placed, dst_placed = dst_placed, src_placed

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in src_placed:   inp[y][x] = src_col
    for (y, x) in dst_placed:   inp[y][x] = dst_col
    for (y, x) in other_placed: inp[y][x] = other_col

    out = [row[:] for row in inp]
    for (y, x) in src_placed: out[y][x] = bg
    for (y, x) in dst_placed: out[y][x] = src_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
