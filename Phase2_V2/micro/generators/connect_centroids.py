"""Micro-primitive family: connect_centroids.

Two solid same-colour blobs (rectangular, odd dimensions so centroid is an
exact grid cell) whose centroids share a row OR a column. Draw an axis-aligned
line between the two centroids in the blob's colour. Path cells that fall
inside either blob are skipped (they're already the colour); only the
between-blob cells are written into T.

The non-collinear (L-shaped) version of the same rule is manhattan_path.
This family teaches: detect components, compute centroid, then bridge.

Tiers: 0 fixed 10x10, bg 0, colour 4 | 1 + colour/bg | 2 + varied size/orientation.
"""
import random

FAMILY = "connect_centroids"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
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
    if len(comps) != 2:
        return {}
    col = comps[0][0]
    blob_cells = set(comps[0][1]) | set(comps[1][1])
    centroids = []
    for _, cells in comps:
        cr = sum(r for r, c in cells) // len(cells)
        cc = sum(c for r, c in cells) // len(cells)
        centroids.append((cr, cc))
    (r1, c1), (r2, c2) = centroids
    T = {}
    if r1 == r2:
        step = 1 if c2 > c1 else -1
        for c in range(c1 + step, c2, step):
            if (r1, c) not in blob_cells:
                T[(r1, c)] = col
    elif c1 == c2:
        step = 1 if r2 > r1 else -1
        for r in range(r1 + step, r2, step):
            if (r, c1) not in blob_cells:
                T[(r, c1)] = col
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
    return "Draw an axis-aligned line between the two blobs' centroids in the blob colour."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(11, 15); W = rng.randint(11, 15)

    if difficulty == 0:
        bg, col = 0, 4
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])

    # Odd-sized solid blobs (so centroid is exactly the middle cell).
    sz1 = rng.choice([1, 3])
    sz2 = rng.choice([1, 3])
    horizontal = rng.choice([True, False])

    inp = [[bg] * W for _ in range(H)]
    for _ in range(50):
        if horizontal:
            # share a row -- centroid row = blob top + sz//2 (since sz is odd)
            r = rng.randint(sz1 // 2 + 1, H - sz1 // 2 - 2)
            c1 = rng.randint(0, W - sz1)
            c2 = rng.randint(0, W - sz2)
            # need different cols + gap of at least 2 between blobs' bounding boxes
            if abs(c1 - c2) < sz1 + sz2 + 2:
                continue
            # second blob's row chosen so its centroid row == r
            r1_top = r - sz1 // 2; r2_top = r - sz2 // 2
            if not (0 <= r1_top and r1_top + sz1 <= H and 0 <= r2_top and r2_top + sz2 <= H):
                continue
            blob1 = {(r1_top + dr, c1 + dc) for dr in range(sz1) for dc in range(sz1)}
            blob2 = {(r2_top + dr, c2 + dc) for dr in range(sz2) for dc in range(sz2)}
            break
        else:
            c = rng.randint(sz1 // 2 + 1, W - sz1 // 2 - 2)
            r1 = rng.randint(0, H - sz1); r2 = rng.randint(0, H - sz2)
            if abs(r1 - r2) < sz1 + sz2 + 2:
                continue
            c1_left = c - sz1 // 2; c2_left = c - sz2 // 2
            if not (0 <= c1_left and c1_left + sz1 <= W and 0 <= c2_left and c2_left + sz2 <= W):
                continue
            blob1 = {(r1 + dr, c1_left + dc) for dr in range(sz1) for dc in range(sz1)}
            blob2 = {(r2 + dr, c2_left + dc) for dr in range(sz2) for dc in range(sz2)}
            break
    else:
        return _instance(rng, difficulty)

    for (r, c) in blob1 | blob2:
        inp[r][c] = col
    out = [row[:] for row in inp]

    # centroids (each blob is odd × odd, so the centroid IS a grid cell)
    def centroid(cells):
        return (sum(r for r, c in cells) // len(cells),
                sum(c for r, c in cells) // len(cells))
    (r1c, c1c) = centroid(blob1); (r2c, c2c) = centroid(blob2)
    blobs = blob1 | blob2
    if r1c == r2c:
        step = 1 if c2c > c1c else -1
        for c in range(c1c + step, c2c, step):
            if (r1c, c) not in blobs:
                out[r1c][c] = col
    elif c1c == c2c:
        step = 1 if r2c > r1c else -1
        for r in range(r1c + step, r2c, step):
            if (r, c1c) not in blobs:
                out[r][c1c] = col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
