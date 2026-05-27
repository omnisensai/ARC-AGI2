"""Micro-primitive family: extract_largest_recolor.

Several disjoint blobs of one colour C sit on a background, plus a single seed
pixel of a marker colour M. The LARGEST blob is recoloured to M; every smaller
blob is erased to background; the seed stays. Teaches SELECTION (by size) bound
to a COLOUR taken from a seed/legend — the seed is the trigger that names the
target colour.

(Replaces the old component_recolor, which was a byte-for-byte duplicate of
component_4conn. This now actually recolours, so the two are mutually exclusive:
component_4conn keeps the largest in its original colour; this repaints it.)

Tiers: 0 fixed-ish, bg 0 | 1 + colour/bg | 2 + varied size/count.
"""
import random

FAMILY = "extract_largest_recolor"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if len(nz) < 2:
        return {}
    M = min(nz, key=lambda k: nz[k])          # seed/marker = rarest non-bg colour
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and g[r][c] != M and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    if not comps:
        return {}
    largest = max(comps, key=len)
    T = {}
    for cells in comps:
        tgt = M if cells is largest else bg
        for (y, x) in cells:
            T[(y, x)] = tgt
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
    return "Recolour the largest blob to the seed colour; erase the smaller blobs."


def _rand_blob(rng, H, W, size, taken):
    start = None
    for _ in range(40):
        r, c = rng.randrange(H), rng.randrange(W)
        if (r, c) not in taken:
            start = (r, c); break
    if start is None:
        return None
    cells = {start}
    for _ in range(size * 60):                 # bounded: never spin when boxed in
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in cells and (ny, nx) not in taken:
            cells.add((ny, nx))
    return cells if len(cells) == size else None


def _fallback(rng):
    """Guaranteed-valid instance, used only if random placement keeps failing."""
    H = W = 10; bg = 0; C, M = 3, 4
    A = [(0, 0), (0, 1), (1, 0)]               # size 3 (unique largest)
    B = [(H - 1, W - 1), (H - 1, W - 2)]       # size 2
    inp = [[bg] * W for _ in range(H)]
    for (y, x) in A + B:
        inp[y][x] = C
    inp[H // 2][W // 2] = M
    out = [row[:] for row in inp]
    for (y, x) in A:
        out[y][x] = M
    for (y, x) in B:
        out[y][x] = bg
    return {"input": inp, "output": out}


def _instance(rng, difficulty):
    for _ in range(300):                       # bounded retries (no recursion)
        res = _try(rng, difficulty)
        if res is not None:
            return res
    return _fallback(rng)


def _try(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(9, 14); W = rng.randint(9, 14)
    if difficulty == 0:
        bg = 0; C, M = 3, 4
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        C, M = rng.sample([c for c in range(1, 10) if c != bg], 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        C, M = rng.sample([c for c in range(0, 10) if c != bg], 2)

    n_blobs = rng.randint(2, 4) if difficulty < 2 else rng.randint(2, 5)
    sizes = sorted((rng.randint(2, 8) for _ in range(n_blobs)), reverse=True)
    if len(sizes) >= 2 and sizes[0] == sizes[1]:
        sizes[0] += 1                          # guarantee a UNIQUE largest

    inp = [[bg] * W for _ in range(H)]
    taken = set()
    blobs = []
    for s in sizes:
        # pad each blob with a 1-cell halo so distinct blobs never touch/merge
        b = _rand_blob(rng, H, W, s, taken)
        if b is None:
            continue
        blobs.append(b)
        for (y, x) in b:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    taken.add((y + dy, x + dx))
    if len(blobs) < 2:
        return None      # retry on a crowded layout
    bs = sorted((len(b) for b in blobs), reverse=True)
    if bs[0] == bs[1]:
        return None      # need a strictly unique largest
    for b in blobs:
        for (y, x) in b:
            inp[y][x] = C
    # single seed pixel of colour M on free background
    seed = None
    for _ in range(60):
        r, c = rng.randrange(H), rng.randrange(W)
        if (r, c) not in taken and inp[r][c] == bg:
            seed = (r, c); break
    if seed is None:
        return None
    inp[seed[0]][seed[1]] = M

    largest = max(blobs, key=len)
    out = [row[:] for row in inp]
    for b in blobs:
        tgt = M if b is largest else bg
        for (y, x) in b:
            out[y][x] = tgt
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
