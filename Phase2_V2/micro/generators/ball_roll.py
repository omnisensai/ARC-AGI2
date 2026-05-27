"""Micro-primitive family: ball_roll (a.k.a. seed snake / maze runner).

A seed enters from an edge and rolls inward, leaving a trail of its colour.
Deterministic rule: step straight ahead; if the cell ahead is a wall, turn into
the single open perpendicular (if exactly one is open) and keep going, otherwise
stop; the ball also stops when it rolls off an edge. Every cell it passes through
is painted the seed's colour — the trailing "snake body".

Teaches stateful path simulation: position + heading, roll, turn at obstacles,
trail. (Distinct from flood_from_seed, which fills a whole region; the ball
leaves a 1-wide path and rolls straight through open space rather than filling it.)

Tiers: 0 fixed-ish, bg 0, wall 5, seed 2 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "ball_roll"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    sr, sc = border[0]; S = g[sr][sc]
    d = (1, 0) if sr == 0 else (-1, 0) if sr == H - 1 else (0, 1) if sc == 0 else (0, -1)
    pos = (sr, sc); visited = [pos]; seen = {pos}
    for _ in range(H * W * 2):
        nr, nc = pos[0] + d[0], pos[1] + d[1]
        if not (0 <= nr < H and 0 <= nc < W):
            break                                       # rolled off the edge
        if g[nr][nc] != bg:                             # wall ahead -> try to turn
            perps = [(1, 0), (-1, 0)] if d[0] == 0 else [(0, 1), (0, -1)]
            opens = [e for e in perps
                     if 0 <= pos[0] + e[0] < H and 0 <= pos[1] + e[1] < W
                     and g[pos[0] + e[0]][pos[1] + e[1]] == bg
                     and (pos[0] + e[0], pos[1] + e[1]) not in seen]
            if len(opens) == 1:
                d = opens[0]; continue
            break                                       # dead end or fork -> stop
        if (nr, nc) in seen:
            break
        pos = (nr, nc); visited.append(pos); seen.add(pos)
    return {(r, c): S for (r, c) in visited if g[r][c] == bg}


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
    return "The seed rolls in from the edge, turning at walls, leaving a trail (snake / maze runner)."


def _simulate(g, bg):
    """Identical to the canonical solver's traversal; returns (visited, turns, S)."""
    H, W = len(g), len(g[0])
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    if len(border) != 1:
        return None, 0, None
    sr, sc = border[0]; S = g[sr][sc]
    d = (1, 0) if sr == 0 else (-1, 0) if sr == H - 1 else (0, 1) if sc == 0 else (0, -1)
    pos = (sr, sc); visited = [pos]; seen = {pos}; turns = 0
    for _ in range(H * W * 2):
        nr, nc = pos[0] + d[0], pos[1] + d[1]
        if not (0 <= nr < H and 0 <= nc < W):
            break
        if g[nr][nc] != bg:
            perps = [(1, 0), (-1, 0)] if d[0] == 0 else [(0, 1), (0, -1)]
            opens = [e for e in perps
                     if 0 <= pos[0] + e[0] < H and 0 <= pos[1] + e[1] < W
                     and g[pos[0] + e[0]][pos[1] + e[1]] == bg
                     and (pos[0] + e[0], pos[1] + e[1]) not in seen]
            if len(opens) == 1:
                d = opens[0]; turns += 1; continue
            break
        if (nr, nc) in seen:
            break
        pos = (nr, nc); visited.append(pos); seen.add(pos)
    return visited, turns, S


def _border_noncorner(rng, H, W):
    side = rng.choice(["top", "bottom", "left", "right"])
    if side == "top":
        return 0, rng.randint(1, W - 2)
    if side == "bottom":
        return H - 1, rng.randint(1, W - 2)
    if side == "left":
        return rng.randint(1, H - 2), 0
    return rng.randint(1, H - 2), W - 1


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 9
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13)
    if difficulty == 0:
        bg, wall, seed = 0, 5, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); wall, seed = rng.sample([c for c in range(1, 10) if c != bg], 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); wall, seed = rng.sample([c for c in range(0, 10) if c != bg], 2)

    interior = [(r, c) for r in range(1, H - 1) for c in range(1, W - 1)]
    for _ in range(120):
        grid = [[bg] * W for _ in range(H)]
        for (r, c) in rng.sample(interior, int(0.16 * len(interior))):
            grid[r][c] = wall
        sr, sc = _border_noncorner(rng, H, W)
        if grid[sr][sc] != bg:
            continue
        grid[sr][sc] = seed
        visited, turns, S = _simulate(grid, bg)
        if visited and len(visited) >= 5 and turns >= 1:   # interesting: rolls a while + turns
            out = [row[:] for row in grid]
            for (r, c) in visited:
                out[r][c] = seed
            return {"input": grid, "output": out}
    return _fallback(bg, wall, seed, H, W)


def _fallback(bg, wall, seed, H, W):
    grid = [[bg] * W for _ in range(H)]
    grid[5][3] = wall; grid[4][2] = wall          # force a right turn at (4,3)
    grid[0][3] = seed
    visited, _, _ = _simulate(grid, bg)
    out = [row[:] for row in grid]
    for (r, c) in visited:
        out[r][c] = seed
    return {"input": grid, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
