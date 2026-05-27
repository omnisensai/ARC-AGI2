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


def _carve(rng, H, W):
    """A self-avoiding corridor path: enter from an edge, run straight, turn at
    bends, exit off an edge. The ball will travel exactly this path."""
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
    for _ in range(H * W):
        if since >= rng.randint(2, 4) and len(path) >= 2:        # consider a 90-deg bend
            perps = [(0, 1), (0, -1)] if d[0] != 0 else [(1, 0), (-1, 0)]
            rng.shuffle(perps)
            for e in perps:
                nxt = (pos[0] + e[0], pos[1] + e[1])
                if 0 <= nxt[0] < H and 0 <= nxt[1] < W and nxt not in pathset:
                    d = e; since = 0; break
        nxt = (pos[0] + d[0], pos[1] + d[1])
        if not (0 <= nxt[0] < H and 0 <= nxt[1] < W):
            break                                                # rolled off an edge -> exit
        if nxt in pathset:
            break
        pos = nxt; path.append(pos); pathset.add(pos); since += 1
    return path


def _build_from_path(path, H, W, bg, wall, seed):
    """Wrap the path in a 1-thick wall tube (skipping border cells so the seed
    stays the unique border marker), drop the seed at the entrance, and produce
    the output by running the canonical simulation — so the solver matches by
    construction. Returns (instance, (turns, length, followed_whole_path))."""
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
    visited, turns, _ = _simulate(grid, bg)
    if not visited:
        return None, (0, 0, False)
    out = [row[:] for row in grid]
    for (r, c) in visited:
        out[r][c] = seed
    return {"input": grid, "output": out}, (turns, len(visited), set(visited) == pathset)


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
        inst, (turns, length, full) = _build_from_path(path, H, W, bg, wall, seed)
        if inst is not None and turns >= 1 and length >= 6 and full:   # full corridor, >=1 real turn
            return inst
    return _fallback(bg, wall, seed, H, W)


def _fallback(bg, wall, seed, H, W):
    rr = H // 2
    path = [(r, 3) for r in range(0, rr + 1)] + [(rr, c) for c in range(4, W)]  # down then turn right
    inst, _ = _build_from_path(path, H, W, bg, wall, seed)
    return inst if inst is not None else {"input": [[bg] * W for _ in range(H)],
                                          "output": [[bg] * W for _ in range(H)]}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
