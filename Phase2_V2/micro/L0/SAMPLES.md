# L0 Samples — for validation

Each family has its atom written down, then 3 worked examples generated live from the
generator (so the OUTPUT is exactly what the canonical solver produces and the gate has
accepted). At the end of each section: the canonical solver source.

Background shown as `.` for readability; non-zero digits are real cell values.

Mark colour is **`1`** for single-set atoms, labels **`1..N`** for multi-set atoms (components).

---

## l0_bg_detection
_Mark every non-background cell._

**Contract:** bg = most-common; for each cell != bg, set T[(r,c)] = 1. apply_T = copy input + overwrite. Input palette excludes 1 (the MARK).

**Example 1** (seed=0, tier=0, train pair 0)

```
    INPUT              OUTPUT
    . . 2 . . .      . . 1 . . .
    . . . 2 . .      . . . 1 . .
    . . . 2 2 .      . . . 1 1 .
    . . . . . .  ->  . . . . . .
    . 2 2 . . 2      . 1 1 . . 1
    . 2 2 2 . .      . 1 1 1 . .
```
**Example 2** (seed=5, tier=1, train pair 0)

```
    INPUT              OUTPUT
    6 6 6 . 6 6      6 6 6 1 6 6
    6 . 6 6 . 6      6 1 6 6 1 6
    . 6 6 . 6 .      1 6 6 1 6 1
    6 6 6 6 6 .  ->  6 6 6 6 6 1
    6 6 6 . 6 6      6 6 6 1 6 6
    6 6 . 6 . .      6 6 1 6 1 1
```
**Example 3** (seed=11, tier=2, train pair 0)

```
    INPUT                  OUTPUT
    8 8 8 8 8 4 8 8      8 8 8 8 8 1 8 8
    8 8 8 4 4 8 8 8      8 8 8 1 1 8 8 8
    8 8 4 8 8 8 8 4      8 8 1 8 8 8 8 1
    8 4 8 8 4 8 8 8      8 1 8 8 1 8 8 8
    8 8 8 8 8 8 4 8  ->  8 8 8 8 8 8 1 8
    8 4 8 8 8 8 8 4      8 1 8 8 8 8 8 1
    8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8
    8 4 8 8 4 8 8 8      8 1 8 8 1 8 8 8
    8 4 4 8 8 8 8 8      8 1 1 8 8 8 8 8
```

**Canonical solver** (`solvers/l0_bg_detection.py`):

```python
from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv:
                T[(r, c)] = 1                # MARK
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

---

## l0_corners
_Mark the four grid corner cells._

**Contract:** Cells = {(0,0), (0,W-1), (H-1,0), (H-1,W-1)} → 1. No content dependency. Input palette excludes 1.

**Example 1** (seed=0, tier=0, train pair 0)

```
    INPUT                OUTPUT
    . . . . . . .      1 . . . . . 1
    . . . . . . .      . . . . . . .
    . . . . . . .      . . . . . . .
    . . . . . . .  ->  . . . . . . .
    . . . . . . .      . . . . . . .
    . . . . . . .      . . . . . . .
    . . . . . . .      1 . . . . . 1
```
**Example 2** (seed=5, tier=1, train pair 0)

```
    INPUT              OUTPUT
    9 9 9 9 9 9      1 9 9 9 9 1
    9 9 9 9 9 9      9 9 9 9 9 9
    9 9 9 9 9 9      9 9 9 9 9 9
    9 9 9 9 9 9  ->  9 9 9 9 9 9
    9 9 9 9 9 9      9 9 9 9 9 9
    9 9 9 9 9 9      1 9 9 9 9 1
```
**Example 3** (seed=11, tier=2, train pair 0)

```
    INPUT                        OUTPUT
    8 8 8 8 9 8 8 8 8 8 8      1 8 8 8 9 8 8 8 8 8 1
    2 5 8 8 8 8 7 5 8 8 8      2 5 8 8 8 8 7 5 8 8 8
    8 8 8 4 9 8 8 8 8 8 8      8 8 8 4 9 8 8 8 8 8 8
    8 8 8 8 8 4 8 8 8 2 8      8 8 8 8 8 4 8 8 8 2 8
    8 8 8 8 8 4 4 8 8 8 8      8 8 8 8 8 4 4 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8  ->  8 8 8 8 8 8 8 8 8 8 8
    8 8 9 8 8 8 8 8 8 8 8      8 8 9 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 9 8 8 8 8 8 8      8 8 8 8 9 8 8 8 8 8 8
    8 8 8 8 8 8 6 . 8 8 8      8 8 8 8 8 8 6 . 8 8 8
    8 8 8 . 8 8 8 8 8 8 8      1 8 8 . 8 8 8 8 8 8 1
```

**Canonical solver** (`solvers/l0_corners.py`):

```python
def infer_T(g):
    H, W = len(g), len(g[0])
    T = {}
    for (r, c) in [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]:
        T[(r, c)] = 1                       # MARK
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

---

## l0_bbox
_Mark the perimeter of the non-bg cells' bounding box._

**Contract:** bbox = (min_r, min_c, max_r, max_c) over non-bg cells; perimeter cells (4 edges of the bbox, INCLUDING corners) → 1. Input palette excludes 1.

**Example 1** (seed=0, tier=0, train pair 0)

```
    INPUT                  OUTPUT
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . . 3 . .      . . 1 1 1 1 1 1
    . . 3 . . . . 3  ->  . . 1 . . . . 1
    . . . 3 3 . . .      . . 1 1 1 1 1 1
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
```
**Example 2** (seed=5, tier=1, train pair 0)

```
    INPUT                  OUTPUT
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 . 6 6      6 6 6 6 6 1 1 1
    6 6 6 6 6 . 6 .  ->  6 6 6 6 6 1 6 1
    6 6 6 6 6 . 6 6      6 6 6 6 6 1 1 1
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
```
**Example 3** (seed=11, tier=2, train pair 0)

```
    INPUT                      OUTPUT
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 4 8 8      8 8 8 8 8 8 8 1 1 1
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 8 4      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 8 8  ->  8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 4 8 8      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 1 8 1
    8 8 8 8 8 8 8 8 4 8      8 8 8 8 8 8 8 1 1 1
```

**Canonical solver** (`solvers/l0_bbox.py`):

```python
from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bv]
    T = {}
    if not cells:
        return T
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    for c in range(c0, c1 + 1):
        T[(r0, c)] = 1; T[(r1, c)] = 1        # top + bottom edges
    for r in range(r0, r1 + 1):
        T[(r, c0)] = 1; T[(r, c1)] = 1        # left + right edges
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

---

## l0_components_4
_Label each 4-connected non-bg component (1, 2, 3, ... in row-major canonical order)._

**Contract:** Components are 4-connected same-colour cells. Sort by (min_row, min_col); assign labels starting at 1. Input palette excludes 1..max_components.

**Example 1** (seed=0, tier=0, train pair 0)

```
    INPUT                  OUTPUT
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . 7 . . .      . . . . 1 . . .
    7 7 . . 7 7 . .  ->  2 2 . . 1 1 . .
    . . . . 7 . . .      . . . . 1 . . .
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
```
**Example 2** (seed=5, tier=1, train pair 0)

```
    INPUT                    OUTPUT
    9 9 9 9 9 9 9 9 9      9 9 9 9 9 9 9 9 9
    9 9 9 8 8 8 9 9 9      9 9 9 1 1 1 9 9 9
    9 9 9 9 9 9 9 9 9      9 9 9 9 9 9 9 9 9
    9 9 9 9 9 9 9 9 9      9 9 9 9 9 9 9 9 9
    9 9 9 9 9 9 9 9 9  ->  9 9 9 9 9 9 9 9 9
    9 9 9 9 9 9 9 9 9      9 9 9 9 9 9 9 9 9
    8 9 9 9 9 8 9 9 9      2 9 9 9 9 3 9 9 9
    8 9 9 9 9 8 9 9 9      2 9 9 9 9 3 9 9 9
    9 9 9 9 9 9 9 9 9      9 9 9 9 9 9 9 9 9
```
**Example 3** (seed=11, tier=2, train pair 0)

```
    INPUT                        OUTPUT
    8 8 8 8 8 8 8 8 8 8 9      8 8 8 8 8 8 8 8 8 8 1
    8 8 8 8 8 8 8 9 8 8 9      8 8 8 8 8 8 8 2 8 8 1
    8 8 8 8 8 8 9 9 8 8 8      8 8 8 8 8 8 2 2 8 8 8
    8 8 9 9 8 8 8 9 8 8 8      8 8 3 3 8 8 8 2 8 8 8
    8 8 8 9 8 8 8 8 8 8 8      8 8 8 3 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8  ->  8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
```

**Canonical solver** (`solvers/l0_components_4.py`):

```python
from collections import Counter, deque


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv and not seen[r][c]:
                color = g[r][c]; comp = set(); q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); comp.add((y, x))
                    for (ny, nx) in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == color:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(comp)
    comps.sort(key=lambda s: (min(r for r, _ in s), min(c for _, c in s)))
    T = {}
    for label, comp in enumerate(comps, start=1):
        for (r, c) in comp:
            T[(r, c)] = label
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

---

## l0_boundary
_Mark the 4-connected boundary of the non-bg cells._

**Contract:** Boundary = non-bg cells with at least one 4-neighbour OUTSIDE the non-bg set (out-of-grid counts as outside). Input palette excludes 1.

**Example 1** (seed=0, tier=0, train pair 0)

```
    INPUT                  OUTPUT
    . . . . . . . .      . . . . . . . .
    . 3 3 3 3 . . .      . 1 1 1 1 . . .
    . 3 3 3 . . . .      . 1 3 1 . . . .
    . 3 3 3 . . . .      . 1 3 1 . . . .
    . . 3 . . . . .  ->  . . 1 . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
    . . . . . . . .      . . . . . . . .
```
**Example 2** (seed=5, tier=1, train pair 0)

```
    INPUT                  OUTPUT
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 . . . 6      6 6 6 6 1 1 1 6
    6 6 6 . . . . 6      6 6 6 1 1 1 1 6
    6 6 6 . 6 6 . 6      6 6 6 1 6 6 1 6
    6 6 6 . 6 . . 6  ->  6 6 6 1 6 1 1 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
    6 6 6 6 6 6 6 6      6 6 6 6 6 6 6 6
```
**Example 3** (seed=11, tier=2, train pair 0)

```
    INPUT                        OUTPUT
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8  ->  8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
    8 8 8 8 8 8 8 4 4 4 8      8 8 8 8 8 8 8 1 1 1 8
    8 8 8 8 8 8 4 4 4 4 8      8 8 8 8 8 8 1 1 1 1 8
    8 8 8 8 8 8 8 8 8 8 8      8 8 8 8 8 8 8 8 8 8 8
```

**Canonical solver** (`solvers/l0_boundary.py`):

```python
from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = {(r, c) for r in range(H) for c in range(W) if g[r][c] != bv}
    T = {}
    for (r, c) in cells:
        for (nr, nc) in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in cells:
                T[(r, c)] = 1                # MARK — this cell is on the 4-boundary
                break
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
```

---

## What to look for when validating

1. **Atom correctness** — does the output for each example actually implement what the
   one-line rule says?
2. **Solver match** — does the canonical solver, run on the input, produce the shown
   output? (The gate already verifies this; sanity-check a couple by eye.)
3. **Grammar invariance** — every solver follows `def solve(g): T = infer_T(g); return apply_T(g, T)`.
   apply_T is identical across families: copy input + overwrite cells in T.
4. **Background preservation** — output preserves input bg cells; only cells where the
   atom applies are overwritten to MARK (1) or a label.
5. **Ambiguity** — any case where two different L0 readings produce different outputs?
   (E.g. `l0_components_4` ties on size — does the canonical sort break the tie cleanly?)
