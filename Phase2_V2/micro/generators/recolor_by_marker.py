"""Micro-primitive family: recolor_by_marker.

Several objects of one neutral colour C sit on the background; each object has a
single marker pixel of a distinct colour touching it. Every object is recoloured
to the colour of its own marker. The marker is the seed that names the object's
new colour. Teaches colour-binding (object <- adjacent marker).

Tiers: 0 fixed-ish, bg 0 | 1 + colour/bg | 2 + varied size/count.
"""
import random

FAMILY = "recolor_by_marker"


def canonical_solver() -> str:
    return '''from collections import Counter, deque

NB8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if not nz:
        return {}
    C = max(nz, key=lambda k: nz[k])              # neutral object colour = most common non-bg
    seen = [[False] * W for _ in range(H)]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == C and not seen[r][c]:
                comp = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == C:
                            seen[ny][nx] = True; q.append((ny, nx))
                mark = None
                for (y, x) in comp:
                    for dy, dx in NB8:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != bg and g[ny][nx] != C:
                            mark = g[ny][nx]; break
                    if mark is not None:
                        break
                if mark is not None:
                    for (y, x) in comp:
                        T[(y, x)] = mark
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
    return "Recolour each object to the colour of the marker touching it."


def _blob(rng, H, W, size, taken):
    start = None
    for _ in range(40):
        r, c = rng.randrange(H), rng.randrange(W)
        if (r, c) not in taken:
            start = (r, c); break
    if start is None:
        return None
    cells = {start}
    for _ in range(size * 60):
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in cells and (ny, nx) not in taken:
            cells.add((ny, nx))
    return cells if len(cells) == size else None


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(10, 15); W = rng.randint(10, 15)
    if difficulty == 0:
        bg, C = 0, 5; n_obj = 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C = rng.choice([c for c in range(1, 10) if c != bg]); n_obj = rng.randint(2, 3)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C = rng.choice([c for c in range(0, 10) if c != bg]); n_obj = rng.randint(2, 4)
    mcolors = [c for c in range(0, 10) if c != bg and c != C]

    nb4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for _ in range(40):
        inp = [[bg] * W for _ in range(H)]
        taken = set()                                  # cells blocked (objects + halos + markers)
        objs = []
        ok = True
        for _o in range(n_obj):
            b = _blob(rng, H, W, rng.randint(3, 6), taken)
            if b is None:
                ok = False; break
            objs.append(b)
            for (y, x) in b:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        taken.add((y + dy, x + dx))
        if not ok or len(objs) < 2:
            continue
        # give each object one marker on a free bg cell 4-adjacent to it
        used_m = set(taken)
        markers = []
        for b in objs:
            spot = None
            cand = [(y + dy, x + dx) for (y, x) in b for dy, dx in nb4]
            rng.shuffle(cand)
            for (ny, nx) in cand:
                if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in b and (ny, nx) not in used_m and inp[ny][nx] == bg:
                    spot = (ny, nx); break
            if spot is None:
                markers = None; break
            markers.append(spot)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    used_m.add((spot[0] + dy, spot[1] + dx))
        if markers is None:
            continue
        mcols = rng.sample(mcolors, k=len(objs)) if len(mcolors) >= len(objs) else [rng.choice(mcolors) for _ in objs]
        for b in objs:
            for (y, x) in b:
                inp[y][x] = C
        for (spot, mcol) in zip(markers, mcols):
            inp[spot[0]][spot[1]] = mcol
        out = [row[:] for row in inp]
        for (b, mcol) in zip(objs, mcols):
            for (y, x) in b:
                out[y][x] = mcol
        return {"input": inp, "output": out}
    # fallback: two fixed objects + markers
    bg, C = 0, 5
    inp = [[bg] * W for _ in range(H)]
    A = [(1, 1), (1, 2), (2, 1)]; B = [(6, 6), (6, 7), (7, 6)]
    for (y, x) in A:
        inp[y][x] = C
    for (y, x) in B:
        inp[y][x] = C
    inp[1][3] = 2; inp[6][8] = 3
    out = [row[:] for row in inp]
    for (y, x) in A:
        out[y][x] = 2
    for (y, x) in B:
        out[y][x] = 3
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
