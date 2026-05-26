"""Micro-primitive family: ray_to_edge.

A single marker sits on a grid border (never a corner). It emits a ray of its
own color straight inward, perpendicular to that edge, to the far edge. Only
background cells along the ray change.

One family, one canonical solver, many instances. The generator constructs each
(input, output) pair DIRECTLY from the rule definition — independent of the
solver — so the acceptance gate is a genuine cross-check, not circular.

Difficulty tiers (no distractors; the marker is always the unique border cell):
  0  fixed 6x6, bg 0, color 2, marker on the top edge        (position varies)
  1  6x6, varied bg + color, marker on the top edge          (+ color, bg)
  2  varied size 5-12, varied bg + color, marker on any edge (+ size, edge)
  3  reserved: interior distractors (solver already keys off the BORDER cell,
     so it is distractor-ready — left disabled for the reference family)
"""
import random

FAMILY = "ray_to_edge"


def canonical_solver() -> str:
    """The single verified solver for the whole family (returned as source)."""
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
    while 0 <= rr < H and 0 <= cc < W:
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
    """Debug/docs ONLY. Never goes into a training prompt (the model must infer
    the rule from the INPUT/T evidence, not from a natural-language hint)."""
    return ("A single marker on a grid edge shoots a ray of its own colour "
            "straight inward to the opposite edge.")


def _instance(rng: random.Random, difficulty: int):
    """Build ONE (input, output) pair directly from the rule. Independent of
    the solver."""
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(5, 12)
        W = rng.randint(5, 12)

    if difficulty == 0:
        bg, color = 0, 2
        edge = "top"
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(1, 10) if c != bg])
        edge = "top"
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(0, 10) if c != bg])
        edge = rng.choice(["top", "bottom", "left", "right"])

    grid = [[bg] * W for _ in range(H)]
    if edge == "top":
        r, c = 0, rng.randint(1, W - 2); dr, dc = 1, 0
    elif edge == "bottom":
        r, c = H - 1, rng.randint(1, W - 2); dr, dc = -1, 0
    elif edge == "left":
        r, c = rng.randint(1, H - 2), 0; dr, dc = 0, 1
    else:
        r, c = rng.randint(1, H - 2), W - 1; dr, dc = 0, -1

    grid[r][c] = color
    inp = [row[:] for row in grid]
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W:
        grid[rr][cc] = color
        rr += dr; cc += dc
    out = grid
    return {"input": inp, "output": out}


def generate(seed: int, difficulty: int) -> dict:
    """One synthetic task: several pairs sharing the family + solver contract;
    instance parameters vary within the family. The same canonical solver holds
    for every pair."""
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {
        "family": FAMILY,
        "seed": seed,
        "difficulty": difficulty,        # metadata only — never enters the prompt
        "params": {"n_train": n_train},  # metadata only
        "train": pairs[:-1],
        "test": pairs[-1:],
    }
