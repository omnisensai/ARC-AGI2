"""Micro-primitive family: fit_piece_to_hole.

Input has:
  - Two SOLID rectangular pieces of distinct colours AND distinct dimensions
    (so they're clearly different pieces)
  - One HOLLOW rectangle outline whose interior dimensions match EXACTLY ONE
    of the pieces

Rule: the matching piece "fits into" the outline — its original cells become
bg, and the outline's interior is filled with that piece's colour. The
non-matching piece stays where it is.

This generalises snap_to_outline (which has only one piece, so no matching
decision). Here the model must compute piece dims, compare against the
outline's interior dims, and select.

Tiers: 0 fixed 12x12 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "fit_piece_to_hole"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def _components_by_colour(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True; q.append((ny, nx))
            comps.append((col, cells))
    return comps


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    pieces = []; outline = None
    for col, cells in comps:
        rmin = min(r for r, _ in cells); rmax = max(r for r, _ in cells)
        cmin = min(c for _, c in cells); cmax = max(c for _, c in cells)
        bbox_size = (rmax - rmin + 1) * (cmax - cmin + 1)
        if len(cells) == bbox_size:
            pieces.append((col, cells, (rmin, rmax, cmin, cmax)))
        else:
            boundary = {(r, c) for r in (rmin, rmax) for c in range(cmin, cmax + 1)} \
                     | {(r, c) for c in (cmin, cmax) for r in range(rmin, rmax + 1)}
            if set(cells) == boundary:
                outline = (col, cells, (rmin, rmax, cmin, cmax))
    if outline is None or len(pieces) < 1:
        return {}

    _, _, (hr0, hr1, hc0, hc1) = outline
    inner_h = hr1 - hr0 - 1; inner_w = hc1 - hc0 - 1

    matching = None
    for p in pieces:
        _, _, (pr0, pr1, pc0, pc1) = p
        if (pr1 - pr0 + 1, pc1 - pc0 + 1) == (inner_h, inner_w):
            matching = p; break
    if matching is None:
        return {}
    match_col, match_cells, _ = matching

    T = {}
    for (y, x) in match_cells:
        T[(y, x)] = bg
    for r in range(hr0 + 1, hr1):
        for c in range(hc0 + 1, hc1):
            T[(r, c)] = match_col
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
    return "Of the two solid pieces, the one whose dimensions match the outline's interior moves into it."


def _place_rect(rng, H, W, h, w, occupied):
    """Return (r0, c0) for a non-overlapping rect of size h x w, or None."""
    for _ in range(80):
        r0 = rng.randint(0, H - h); c0 = rng.randint(0, W - w)
        cells = {(r0 + dr, c0 + dc) for dr in range(h) for dc in range(w)}
        margin = {(r + dy, c + dx) for (r, c) in cells
                  for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
        if not (margin & occupied):
            return r0, c0, cells
    return None


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12
    else:
        H = rng.randint(12, 15); W = rng.randint(12, 15)

    if difficulty == 0:
        bg, match_col, other_col, hollow_col = 0, 2, 4, 8
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        match_col, other_col, hollow_col = rng.sample(avail, 3)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        match_col, other_col, hollow_col = rng.sample(avail, 3)

    # Pick two distinct rectangular dimensions for the two pieces
    for _ in range(20):
        ph1, pw1 = rng.randint(1, 3), rng.randint(1, 3)
        ph2, pw2 = rng.randint(1, 3), rng.randint(1, 3)
        if (ph1, pw1) != (ph2, pw2):
            break
    else:
        return _instance(rng, difficulty)

    # Outline interior must match piece 1 dims; outline bbox = (ph1+2, pw1+2)
    out_h, out_w = ph1 + 2, pw1 + 2

    occupied = set()
    res = _place_rect(rng, H, W, ph1, pw1, occupied)
    if res is None: return _instance(rng, difficulty)
    p1_r0, p1_c0, p1_cells = res
    occupied |= p1_cells

    res = _place_rect(rng, H, W, ph2, pw2, occupied)
    if res is None: return _instance(rng, difficulty)
    p2_r0, p2_c0, p2_cells = res
    occupied |= p2_cells

    res = _place_rect(rng, H, W, out_h, out_w, occupied)
    if res is None: return _instance(rng, difficulty)
    out_r0, out_c0, out_cells = res

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in p1_cells:
        inp[y][x] = match_col
    for (y, x) in p2_cells:
        inp[y][x] = other_col
    # Outline boundary only (hollow)
    out_r1 = out_r0 + out_h - 1; out_c1 = out_c0 + out_w - 1
    for r in range(out_r0, out_r1 + 1):
        inp[r][out_c0] = hollow_col; inp[r][out_c1] = hollow_col
    for c in range(out_c0, out_c1 + 1):
        inp[out_r0][c] = hollow_col; inp[out_r1][c] = hollow_col

    out = [row[:] for row in inp]
    for (y, x) in p1_cells:
        out[y][x] = bg
    for r in range(out_r0 + 1, out_r1):
        for c in range(out_c0 + 1, out_c1):
            out[r][c] = match_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
