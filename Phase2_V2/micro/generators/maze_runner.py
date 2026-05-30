"""Micro-primitive family: maze_runner (ball roll, NO trail).

Same physics as ball_roll, but the ball leaves NO trail: it rolls in from an
edge, turns at the corridor bends, and comes to rest at the dead end — and the
output shows ONLY the ball at its final cell (the entrance is cleared, the path
stays background). ball_roll is the "snake" (trail); maze_runner is the rolling
ball that ends where it stops.

Deterministic rule: enter from the edge heading inward; step straight; at a wall,
turn into the single open perpendicular (if exactly one), else stop; the ball
ends at the last cell it reaches. T moves the ball: start -> background, end ->
seed colour.

Tiers: 0 fixed-ish, bg 0, wall 5, seed 2 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "maze_runner"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    sr, sc = border[0]; S = g[sr][sc]
    d = (1, 0) if sr == 0 else (-1, 0) if sr == H - 1 else (0, 1) if sc == 0 else (0, -1)
    pos = (sr, sc); seen = {pos}; last = pos
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
                d = opens[0]; continue
            break
        if (nr, nc) in seen:
            break
        pos = (nr, nc); seen.add(pos); last = pos
    T = {}
    if last != (sr, sc):
        T[(sr, sc)] = bg          # the ball leaves the entrance (no trail)
        T[last] = S               # and comes to rest at the dead end
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
    return "The ball rolls in from the edge, turning at walls, and stops at the dead end — no trail, only the final position."


def _simulate(g, bg):
    H, W = len(g), len(g[0])
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    if len(border) != 1:
        return None, 0, None
    sr, sc = border[0]; S = g[sr][sc]
    d = (1, 0) if sr == 0 else (-1, 0) if sr == H - 1 else (0, 1) if sc == 0 else (0, -1)
    pos = (sr, sc); seen = {pos}; last = pos; turns = 0
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
        pos = (nr, nc); seen.add(pos); last = pos
    return last, turns, (sr, sc)


def _carve(rng, H, W):
    """Corridor that enters from an edge and DEAD-ENDS in the interior (so the
    ball has a resting cell)."""
    side = rng.choice(["top", "bottom", "left", "right"])
    if side == "top":
        pos = (0, rng.randint(2, W - 3)); d = (1, 0)
    elif side == "bottom":
        pos = (H - 1, rng.randint(2, W - 3)); d = (-1, 0)
    elif side == "left":
        pos = (rng.randint(2, H - 3), 0); d = (0, 1)
    else:
        pos = (rng.randint(2, H - 3), W - 1); d = (0, -1)
    path = [pos]; pathset = {pos}; since = 0
    target = rng.randint(6, max(7, (H + W)))
    while len(path) < target:
        if since >= rng.randint(2, 4) and len(path) >= 2:
            perps = [(0, 1), (0, -1)] if d[0] != 0 else [(1, 0), (-1, 0)]
            rng.shuffle(perps)
            for e in perps:
                nxt = (pos[0] + e[0], pos[1] + e[1])
                if 1 <= nxt[0] <= H - 2 and 1 <= nxt[1] <= W - 2 and nxt not in pathset:
                    d = e; since = 0; break
        nxt = (pos[0] + d[0], pos[1] + d[1])
        if not (1 <= nxt[0] <= H - 2 and 1 <= nxt[1] <= W - 2):   # keep the end interior
            break
        if nxt in pathset:
            break
        pos = nxt; path.append(pos); pathset.add(pos); since += 1
    return path


def _build_from_path(path, H, W, bg, wall, seed):
    pathset = set(path)
    grid = [[bg] * W for _ in range(H)]
    for (r, c) in path:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nr, nc = r + dy, c + dx
                if (0 <= nr < H and 0 <= nc < W and (nr, nc) not in pathset
                        and not (nr in (0, H - 1) or nc in (0, W - 1))):
                    grid[nr][nc] = wall
    sr, sc = path[0]
    grid[sr][sc] = seed
    last, turns, start = _simulate(grid, bg)
    if last is None:
        return None, (0, False)
    out = [row[:] for row in grid]
    if last != start:
        out[start[0]][start[1]] = bg
        out[last[0]][last[1]] = seed
    reached_end = (last == path[-1] and last != start)
    return {"input": grid, "output": out}, (turns, reached_end)


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(10, 15); W = rng.randint(10, 15)
    if difficulty == 0:
        bg, wall, seed = 0, 5, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); wall, seed = rng.sample([c for c in range(1, 10) if c != bg], 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); wall, seed = rng.sample([c for c in range(0, 10) if c != bg], 2)

    for _ in range(80):
        path = _carve(rng, H, W)
        if len(path) < 6:
            continue
        inst, (turns, reached_end) = _build_from_path(path, H, W, bg, wall, seed)
        if inst is not None and turns >= 1 and reached_end:
            return inst
    return _fallback(bg, wall, seed, H, W)


def _fallback(bg, wall, seed, H, W):
    rr = H // 2
    path = [(r, 3) for r in range(0, rr + 1)] + [(rr, c) for c in range(4, W - 2)]  # down then right, dead-end interior
    inst, _ = _build_from_path(path, H, W, bg, wall, seed)
    return inst if inst is not None else {"input": [[bg] * W for _ in range(H)],
                                          "output": [[bg] * W for _ in range(H)]}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
