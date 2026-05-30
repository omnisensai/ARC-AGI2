"""Micro-primitive family: move_to_marker.

A rigid object (a connected blob of colour C) and a single marker pixel (colour
M) sit on the background. The object is translated so its bounding-box top-left
lands on the marker; the original cells clear to background. The marker is the
seed that names the destination. Teaches anchoring + translation by a target.

Tiers: 0 fixed-ish, bg 0 | 1 + colour/bg | 2 + varied size/shape.
"""
import random

FAMILY = "move_to_marker"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    if len(nz) < 2:
        return {}
    M = min(nz, key=lambda k: nz[k])              # marker = rarest non-bg (single cell)
    mr, mc = next((r, c) for r in range(H) for c in range(W) if g[r][c] == M)
    obj = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg and g[r][c] != M]
    if not obj:
        return {}
    or0 = min(r for r, c in obj); oc0 = min(c for r, c in obj)
    dr, dc = mr - or0, mc - oc0
    T = {}
    for (r, c) in obj:
        T[(r, c)] = bg                            # clear old object
    T[(mr, mc)] = bg                              # clear the consumed marker
    for (r, c) in obj:
        T[(r + dr, c + dc)] = g[r][c]             # draw at destination (overrides)
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
    return "Move the object so its top-left corner lands on the marker."


def _blob(rng, max_h, max_w):
    target = rng.randint(3, max(3, (max_h * max_w) // 2))    # >= 3 cells (never degenerate)
    cells = {(0, 0)}
    for _ in range(target * 60):
        if len(cells) >= target:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < max_h and 0 <= nx < max_w and (ny, nx) not in cells:
            cells.add((ny, nx))
    mnr = min(r for r, c in cells); mnc = min(c for r, c in cells)
    return {(r - mnr, c - mnc) for (r, c) in cells}


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10; mh = mw = 3
    else:
        H = rng.randint(9, 14); W = rng.randint(9, 14); mh = mw = 4
    if difficulty == 0:
        bg, C, M = 0, 3, 4
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, M = rng.sample([c for c in range(1, 10) if c != bg], 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, M = rng.sample([c for c in range(0, 10) if c != bg], 2)

    rel = _blob(rng, mh, mw)
    oh = max(r for r, c in rel) + 1; ow = max(c for r, c in rel) + 1
    for _ in range(60):
        r0 = rng.randint(0, H - oh); c0 = rng.randint(0, W - ow)        # object position
        mr = rng.randint(0, H - oh); mc = rng.randint(0, W - ow)        # marker = destination top-left
        if (mr, mc) == (r0, c0):
            continue
        obj = {(r0 + r, c0 + c) for (r, c) in rel}
        dest = {(mr + r, mc + c) for (r, c) in rel}
        if (mr, mc) in obj:                                            # marker must not sit under the object
            continue
        inp = [[bg] * W for _ in range(H)]
        for (r, c) in obj:
            inp[r][c] = C
        inp[mr][mc] = M
        out = [[bg] * W for _ in range(H)]
        for (r, c) in dest:
            out[r][c] = C
        return {"input": inp, "output": out}
    # fallback
    inp = [[bg] * W for _ in range(H)]
    for (r, c) in rel:
        inp[r][c] = C
    inp[H - 1][W - 1] = M
    out = [[bg] * W for _ in range(H)]
    for (r, c) in rel:
        out[(H - oh) + r][(W - ow) + c] = C
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
