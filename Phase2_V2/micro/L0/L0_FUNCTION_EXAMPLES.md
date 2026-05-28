# L0 Function-Definition Examples (canonical format)

L0 target is **NOT** `solve(input_grid)`.

L0 target is the **ontology function itself**.

The grid is evidence.
The target is the reusable detector / meta-function.

---

## 1. Diagonal

### Example grid
```
0 0 0 0 0
0 7 0 0 0
0 0 7 0 0
0 0 0 7 0
0 0 0 0 0
```

### Target function
```python
def is_diagonal(cells):
    """
    Return True if cells form a contiguous diagonal segment.
    cells: iterable of (r, c)
    """
    cells = sorted(cells)
    if len(cells) < 2:
        return False
    # main diagonal: r-c constant
    same_main = len({r - c for r, c in cells}) == 1
    # anti diagonal: r+c constant
    same_anti = len({r + c for r, c in cells}) == 1
    if not (same_main or same_anti):
        return False
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    # contiguous: no coordinate gaps
    return (
        max(rs) - min(rs) == len(cells) - 1
        and max(cs) - min(cs) == len(cells) - 1
    )
```

---

## 2. U-cup

### Example grid
```
0 0 0 0 0 0
0 4 0 0 4 0
0 4 0 0 4 0
0 4 4 4 4 0
0 0 0 0 0 0
```

### Target function
```python
def find_u_cup(g, bg=0):
    """
    Detect a static U-cup:
    - two vertical walls
    - one bottom floor
    - open top
    - same non-bg colour
    Returns metadata dict or None.
    """
    H, W = len(g), len(g[0])
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return None
    colours = {g[r][c] for r, c in cells}
    if len(colours) != 1:
        return None
    colour = next(iter(colours))
    top = min(r for r, c in cells)
    bottom = max(r for r, c in cells)
    left = min(c for r, c in cells)
    right = max(c for r, c in cells)
    if bottom <= top or right <= left:
        return None
    left_wall = {(r, left) for r in range(top, bottom + 1)}
    right_wall = {(r, right) for r in range(top, bottom + 1)}
    floor = {(bottom, c) for c in range(left, right + 1)}
    expected = left_wall | right_wall | floor
    actual = set(cells)
    if actual != expected:
        return None
    # open top: cells between walls on top row must be background
    for c in range(left + 1, right):
        if g[top][c] != bg:
            return None
    interior = {(r, c) for r in range(top, bottom) for c in range(left + 1, right)}
    return {
        "colour": colour,
        "bbox": (top, left, bottom, right),
        "left_wall": left_wall,
        "right_wall": right_wall,
        "floor": floor,
        "interior": interior,
    }
```

---

## 3. Blob

### Example grid
```
0 0 0 0 0 0
0 5 5 5 0 0
0 5 5 5 5 0
0 5 5 5 0 0
0 0 5 5 0 0
0 0 0 0 0 0
```

### Target function
```python
from collections import deque


def find_blobs(g, bg=0, conn=4):
    """
    Return connected same-colour non-bg blobs.
    A blob is a filled connected mass with no required geometric shape.
    """
    H, W = len(g), len(g[0])
    if conn == 4:
        nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    elif conn == 8:
        nbrs = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]
    else:
        raise ValueError("conn must be 4 or 8")
    seen = [[False] * W for _ in range(H)]
    blobs = []
    for r in range(H):
        for c in range(W):
            if seen[r][c] or g[r][c] == bg:
                continue
            colour = g[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells = set()
            while q:
                y, x = q.popleft()
                cells.add((y, x))
                for dy, dx in nbrs:
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < H
                        and 0 <= nx < W
                        and not seen[ny][nx]
                        and g[ny][nx] == colour
                    ):
                        seen[ny][nx] = True
                        q.append((ny, nx))
            blobs.append({
                "colour": colour,
                "cells": cells,
                "bbox": (
                    min(r for r, c in cells),
                    min(c for r, c in cells),
                    max(r for r, c in cells),
                    max(c for r, c in cells),
                ),
            })
    return blobs
```

---

## Format rules (drawn from these examples)

- **Target = a named ontology function** (`is_diagonal`, `find_u_cup`, `find_blobs`, …). Never `def solve(...)`.
- **Function signature varies by atom** — some take `cells`, some take a `g` grid plus optional parameters (`bg=0`, `conn=4`). The name and signature are part of the contract.
- **Return type varies** — bool, dict-or-None, list-of-dicts. Whatever is natural for the atom.
- **The grid in the prompt is evidence**, not a transformation input/output pair.
- **No `solve` wrapper. No `infer_T`/`apply_T` scaffold.** L0 has its own SFT grammar, distinct from L1/L2.
