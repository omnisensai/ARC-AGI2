"""Micro-primitive family: sandwich_fill.

Several pairs of same-coloured markers sit on the grid, each pair aligned on a
row, column, or diagonal with only background between them. The background cells
between each pair are filled with that pair's colour. Horizontal, vertical, and
diagonal sandwiches.

Each sandwich uses a DISTINCT colour, so the solver pairs markers by colour with
no cross-talk; the generator draws only the intended fills, so the gate catches
any accidental alignment.

Tiers: 0 one horizontal sandwich | 1 1-2 sandwiches H/V, varied colour/bg
        2 up to 3 sandwiches incl. diagonal, varied size.
"""
import random

FAMILY = "sandwich_fill"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    by_color = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg:
                by_color.setdefault(g[r][c], []).append((r, c))
    T = {}
    for col, pts in by_color.items():
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                (r1, c1), (r2, c2) = pts[i], pts[j]
                dr, dc = r2 - r1, c2 - c1
                if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                    continue
                steps = max(abs(dr), abs(dc))
                if steps < 2:
                    continue
                sr = (dr > 0) - (dr < 0); sc = (dc > 0) - (dc < 0)
                between = [(r1 + sr * k, c1 + sc * k) for k in range(1, steps)]
                if all(g[r][c] == bg for (r, c) in between):
                    for (r, c) in between:
                        T[(r, c)] = col
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
    return "Fill the background between each same-coloured pair (row, column, or diagonal)."


def _free(occ, cells, H, W):
    halo = set()
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                halo.add((r + dr, c + dc))
    return all(0 <= r < H and 0 <= c < W for (r, c) in cells) and not (halo & occ)


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(9, 14); W = rng.randint(9, 14)
    bg = 0 if difficulty == 0 else rng.choice([0, 0, rng.randint(0, 9)])
    n_sand = 1 if difficulty == 0 else (rng.randint(1, 2) if difficulty == 1 else rng.randint(2, 3))
    orients = ["H"] if difficulty == 0 else (["H", "V"] if difficulty == 1 else ["H", "V", "D"])
    colors = [c for c in range(1, 10) if c != bg]
    rng.shuffle(colors)

    inp = [[bg] * W for _ in range(H)]
    out = [[bg] * W for _ in range(H)]
    occ = set()
    placed = 0
    for s in range(n_sand):
        color = colors[s % len(colors)]
        for _ in range(80):
            orient = rng.choice(orients)
            if orient == "H":
                r = rng.randint(0, H - 1); c1 = rng.randint(0, W - 3); c2 = rng.randint(c1 + 2, W - 1)
                p1, p2 = (r, c1), (r, c2)
            elif orient == "V":
                c = rng.randint(0, W - 1); r1 = rng.randint(0, H - 3); r2 = rng.randint(r1 + 2, H - 1)
                p1, p2 = (r1, c), (r2, c)
            else:
                sdr = rng.choice([1, -1]); sdc = rng.choice([1, -1]); L = rng.randint(2, min(H, W) - 1)
                r1 = rng.randint(0, H - 1 - L) if sdr > 0 else rng.randint(L, H - 1)
                c1 = rng.randint(0, W - 1 - L) if sdc > 0 else rng.randint(L, W - 1)
                p1, p2 = (r1, c1), (r1 + sdr * L, c1 + sdc * L)
            sr = (p2[0] > p1[0]) - (p2[0] < p1[0]); sc = (p2[1] > p1[1]) - (p2[1] < p1[1])
            steps = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))
            line = [(p1[0] + sr * k, p1[1] + sc * k) for k in range(steps + 1)]
            if _free(occ, line, H, W):
                for (r, c) in line:
                    occ.add((r, c))
                inp[p1[0]][p1[1]] = color; inp[p2[0]][p2[1]] = color
                out[p1[0]][p1[1]] = color; out[p2[0]][p2[1]] = color
                for (r, c) in line[1:-1]:
                    out[r][c] = color
                placed += 1
                break
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
