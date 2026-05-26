"""Micro-primitive family: component_4conn (keep largest, 4-connectivity).

Matched partner of component_8conn. SAME construction — a diagonal staircase
(4-disconnected into singletons) plus a solid 2x2 block — but here connectivity
is 4, so the staircase is NOT one piece; the solid block is the largest
4-connected component and is kept. Everything else is erased.

Side by side with component_8conn (identical-looking inputs, different outputs),
this teaches that connectivity is a rule parameter the model must infer.
"""
import random

CONN = 4
FAMILY = "component_4conn"


def canonical_solver() -> str:
    return '''from collections import Counter, deque

NB = [(1,0),(-1,0),(0,1),(0,-1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False]*W for _ in range(H)]; comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r,c)]); seen[r][c] = True
                while q:
                    y,x = q.popleft(); cells.append((y,x))
                    for dy,dx in NB:
                        ny,nx = y+dy, x+dx
                        if 0<=ny<H and 0<=nx<W and not seen[ny][nx] and g[ny][nx]==col:
                            seen[ny][nx]=True; q.append((ny,nx))
                comps.append(cells)
    if not comps:
        return {}
    largest = max(comps, key=len)
    T = {}
    for cells in comps:
        if cells is largest:
            continue
        for (y,x) in cells:
            T[(y,x)] = bg
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r,c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
'''


def family_prompt_hint() -> str:
    return "Keep the largest 4-connected blob (diagonals do NOT connect); erase the rest."


def _components(grid, H, W, bg, conn):
    from collections import deque
    nb = [(1,0),(-1,0),(0,1),(0,-1)] + ([(1,1),(1,-1),(-1,1),(-1,-1)] if conn == 8 else [])
    seen = [[False]*W for _ in range(H)]; comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                col = grid[r][c]; cells = []; q = deque([(r,c)]); seen[r][c] = True
                while q:
                    y,x = q.popleft(); cells.append((y,x))
                    for dy,dx in nb:
                        ny,nx = y+dy, x+dx
                        if 0<=ny<H and 0<=nx<W and not seen[ny][nx] and grid[ny][nx]==col:
                            seen[ny][nx]=True; q.append((ny,nx))
                comps.append(cells)
    return comps


def _free(occ, cells, H, W):
    halo = set()
    for (r,c) in cells:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                halo.add((r+dr,c+dc))
    return all(0<=r<H and 0<=c<W for (r,c) in cells) and not (halo & occ)


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12
    else:
        H = rng.randint(11, 16); W = rng.randint(11, 16)
    if difficulty == 0:
        bg, color = 0, 2; k = 5
    elif difficulty == 1:
        bg = rng.choice([0,0,rng.randint(0,9)]); color = rng.choice([c for c in range(1,10) if c!=bg]); k = 5
    else:
        bg = rng.choice([0,0,rng.randint(0,9)]); color = rng.choice([c for c in range(0,10) if c!=bg]); k = rng.choice([5,6])

    grid = [[bg]*W for _ in range(H)]; occ = set()
    for _ in range(60):
        sr = rng.randint(0, H-k); sc = rng.randint(0, W-k)
        cells = [(sr+i, sc+i) for i in range(k)]
        if _free(occ, cells, H, W):
            for (r,c) in cells: grid[r][c] = color; occ.add((r,c))
            break
    for _ in range(60):
        br = rng.randint(0, H-2); bc = rng.randint(0, W-2)
        cells = [(br+i, bc+j) for i in range(2) for j in range(2)]
        if _free(occ, cells, H, W):
            for (r,c) in cells: grid[r][c] = color; occ.add((r,c))
            break
    for _ in range(60):
        r = rng.randint(0, H-1); c = rng.randint(0, W-1)
        if _free(occ, [(r,c)], H, W):
            grid[r][c] = color; occ.add((r,c)); break

    inp = [row[:] for row in grid]
    comps = _components(inp, H, W, bg, CONN)
    largest = max(comps, key=len)
    out = [[bg]*W for _ in range(H)]
    for (r,c) in largest: out[r][c] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train, "conn": CONN}, "train": pairs[:-1], "test": pairs[-1:]}
