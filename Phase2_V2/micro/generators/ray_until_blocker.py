"""Micro-primitive family: ray_until_blocker.

A marker on a grid border shoots a ray of its colour straight inward, but STOPS
one cell before it would hit a blocker (an interior non-background cell of a
different colour). If there is no blocker on its path, the ray runs to the edge.

Teaches stop-condition / bounded extent (boundary vs obstacle). The marker is
the border cell; the blocker is interior, so they are never confused.

Tiers: 0 top edge, blocker present, bg 0 | 1 + colour/bg | 2 + any edge/size,
        sometimes no blocker.
"""
import random

FAMILY = "ray_until_blocker"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    r, c = border[0]
    col = g[r][c]
    if r == 0:
        dr, dc = 1, 0
    elif r == H - 1:
        dr, dc = -1, 0
    elif c == 0:
        dr, dc = 0, 1
    else:
        dr, dc = 0, -1
    T = {}
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W and g[rr][cc] == bg:
        T[(rr, cc)] = col
        rr += dr
        cc += dc
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
    return "An edge marker shoots a ray inward, stopping just before any blocker."


def _instance(rng, difficulty, force_blocker=False):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(6, 12); W = rng.randint(6, 12)
    if difficulty == 0:
        bg, color = 0, 2; edge = "top"; has_blocker = True
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg]); edge = "top"; has_blocker = True
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg]); edge = rng.choice(["top", "bottom", "left", "right"]); has_blocker = rng.random() < 0.7
    if force_blocker:
        has_blocker = True
    blk = rng.choice([c for c in range(0, 10) if c not in (bg, color)])

    grid = [[bg] * W for _ in range(H)]
    if edge == "top":
        r, c = 0, rng.randint(1, W - 2); dr, dc = 1, 0
    elif edge == "bottom":
        r, c = H - 1, rng.randint(1, W - 2); dr, dc = -1, 0
    elif edge == "left":
        r, c = rng.randint(1, H - 2), 0; dr, dc = 0, 1
    else:
        r, c = rng.randint(1, H - 2), W - 1; dr, dc = 0, -1

    path = []
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W:
        path.append((rr, cc)); rr += dr; cc += dc

    grid[r][c] = color
    blocker_at = None
    if has_blocker and len(path) >= 4:
        bi = rng.randint(2, len(path) - 2)  # interior only — never the far-edge cell
        blocker_at = path[bi]
        grid[blocker_at[0]][blocker_at[1]] = blk

    inp = [row[:] for row in grid]
    out = [row[:] for row in grid]
    for (pr, pc) in path:
        if (pr, pc) == blocker_at:
            break
        out[pr][pc] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    # guarantee the rule is demonstrated: first train pair + the test pair carry
    # an on-path blocker, so a task is never a degenerate (blocker-free) ray_to_edge.
    pairs = [_instance(rng, difficulty, force_blocker=(k == 0 or k == n_train))
             for k in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
