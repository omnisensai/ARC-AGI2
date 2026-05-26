# Micro families — one sample task each (for review)

17 synthetic primitive families. For each: one sample task (tier 1) shown as
INPUT / OUTPUT / T per pair, then the ONE canonical solver that solves every
instance of that family. T encoding: `.` = cell unchanged, digit = new colour.
Each task was verified by running the solver vs the OUTPUT on every pair
(fresh subprocess) + an AST hardcoding audit.

## boundary_mask
_Hollow the shape: keep its outline, erase the interior._  (sample: boundary_mask_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000000
000000000
000000000
000000000
000000000
000000000
000555500
000555500
000555500
OUTPUT:
000000000
000000000
000000000
000000000
000000000
000000000
000555500
000500500
000555500
T:
.........
.........
.........
.........
.........
.........
.........
....00...
.........
```
**pair 1 (train 1)**
```
INPUT:
777777777
777777777
777777777
888777777
888777777
888777777
777777777
777777777
777777777
OUTPUT:
777777777
777777777
777777777
888777777
878777777
888777777
777777777
777777777
777777777
T:
.........
.........
.........
.........
.7.......
.........
.........
.........
.........
```
**pair 2 (train 2)**
```
INPUT:
000000000
000000000
000001111
000001111
000001111
000001111
000001111
000000000
000000000
OUTPUT:
000000000
000000000
000001111
000001001
000001001
000001001
000001111
000000000
000000000
T:
.........
.........
.........
......00.
......00.
......00.
.........
.........
.........
```
**pair 3 (test)**
```
INPUT:
222333333
222333333
222333333
222333333
333333333
333333333
333333333
333333333
333333333
OUTPUT:
222333333
232333333
232333333
222333333
333333333
333333333
333333333
333333333
333333333
T:
.........
.3.......
.3.......
.........
.........
.........
.........
.........
.........
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg:
                interior = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < H and 0 <= nc < W and g[nr][nc] != bg):
                        interior = False
                        break
                if interior:
                    T[(r, c)] = bg
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

## complete_line
_Two same-coloured endpoints define a line; fill the cells between them._  (sample: complete_line_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000
000000
000000
000505
000000
000000
OUTPUT:
000000
000000
000000
000555
000000
000000
T:
......
......
......
....5.
......
......
```
**pair 1 (train 1)**
```
INPUT:
000000
000000
000000
200000
000000
200000
OUTPUT:
000000
000000
000000
200000
200000
200000
T:
......
......
......
......
2.....
......
```
**pair 2 (train 2)**
```
INPUT:
000000
000008
000000
000000
000000
000008
OUTPUT:
000000
000008
000008
000008
000008
000008
T:
......
......
.....8
.....8
.....8
......
```
**pair 3 (test)**
```
INPUT:
100001
000000
000000
000000
000000
000000
OUTPUT:
111111
000000
000000
000000
000000
000000
T:
.1111.
......
......
......
......
......
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    pts = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    (r1, c1), (r2, c2) = pts[0], pts[-1]
    col = g[r1][c1]
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    T = {}
    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        T[(r, c)] = col
        r += dr
        c += dc
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

## component_4conn
_Keep the largest 4-connected blob (diagonals do NOT connect); erase the rest._  (sample: component_4conn_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000000000
000000050000
000000005000
000000000500
000000000050
000000000005
000000000000
000000055000
000000055000
000000000000
000000500000
000000000000
OUTPUT:
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000055000
000000055000
000000000000
000000000000
000000000000
T:
............
.......0....
........0...
.........0..
..........0.
...........0
............
............
............
............
......0.....
............
```
**pair 1 (train 1)**
```
INPUT:
000000800008
000000080000
000000008000
000000000800
000000000080
000000000000
000000000880
000000000880
000000000000
000000000000
000000000000
000000000000
OUTPUT:
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000880
000000000880
000000000000
000000000000
000000000000
000000000000
T:
......0....0
.......0....
........0...
.........0..
..........0.
............
............
............
............
............
............
............
```
**pair 2 (train 2)**
```
INPUT:
440000000040
440004000000
000000400000
000000040000
000000004000
000000000400
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
OUTPUT:
440000000000
440000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
T:
..........0.
.....0......
......0.....
.......0....
........0...
.........0..
............
............
............
............
............
............
```
**pair 3 (test)**
```
INPUT:
000000007700
000000007700
000000000000
000000700070
000000070000
000000007000
000000000700
000000000070
000000000000
000000000000
000000000000
000000000000
OUTPUT:
000000007700
000000007700
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
T:
............
............
............
......0...0.
.......0....
........0...
.........0..
..........0.
............
............
............
............
```
**canonical solver:**
```python
from collections import Counter, deque

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
```

## component_8conn
_Keep the largest 8-connected blob (diagonals connect); erase the rest._  (sample: component_8conn_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000000000
000000050000
000000005000
000000000500
000000000050
000000000005
000000000000
000000055000
000000055000
000000000000
000000500000
000000000000
OUTPUT:
000000000000
000000050000
000000005000
000000000500
000000000050
000000000005
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
T:
............
............
............
............
............
............
............
.......00...
.......00...
............
......0.....
............
```
**pair 1 (train 1)**
```
INPUT:
000000800008
000000080000
000000008000
000000000800
000000000080
000000000000
000000000880
000000000880
000000000000
000000000000
000000000000
000000000000
OUTPUT:
000000800000
000000080000
000000008000
000000000800
000000000080
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
T:
...........0
............
............
............
............
............
.........00.
.........00.
............
............
............
............
```
**pair 2 (train 2)**
```
INPUT:
440000000040
440004000000
000000400000
000000040000
000000004000
000000000400
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
OUTPUT:
000000000000
000004000000
000000400000
000000040000
000000004000
000000000400
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
T:
00........0.
00..........
............
............
............
............
............
............
............
............
............
............
```
**pair 3 (test)**
```
INPUT:
000000007700
000000007700
000000000000
000000700070
000000070000
000000007000
000000000700
000000000070
000000000000
000000000000
000000000000
000000000000
OUTPUT:
000000000000
000000000000
000000000000
000000700000
000000070000
000000007000
000000000700
000000000070
000000000000
000000000000
000000000000
000000000000
T:
........00..
........00..
............
..........0.
............
............
............
............
............
............
............
............
```
**canonical solver:**
```python
from collections import Counter, deque

NB = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]


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
```

## component_recolor
_Keep the largest connected blob; erase the smaller ones to background._  (sample: component_recolor_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0005500000
5000000555
0000000555
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000555
0000000555
0000000000
T:
..........
..........
..........
..........
..........
..........
...00.....
0.........
..........
..........
```
**pair 1 (train 1)**
```
INPUT:
0000000000
0000000000
0000000000
0000000001
0000000001
1000000000
0000000000
0000111000
0000111000
0000111000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000111000
0000111000
0000111000
T:
..........
..........
..........
.........0
.........0
0.........
..........
..........
..........
..........
```
**pair 2 (train 2)**
```
INPUT:
0000000099
0000000000
0000000000
0000000000
0000000000
0000000000
0009990000
0009990900
0000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0009990000
0009990000
0000000000
0000000000
T:
........00
..........
..........
..........
..........
..........
..........
.......0..
..........
..........
```
**pair 3 (test)**
```
INPUT:
0000006600
0060000000
0060000000
0000000666
0000000666
0000000000
0000000000
0000000000
0000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000666
0000000666
0000000000
0000000000
0000000000
0000000000
0000000000
T:
......00..
..0.......
..0.......
..........
..........
..........
..........
..........
..........
..........
```
**canonical solver:**
```python
from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    if not comps:
        return {}
    largest = max(comps, key=len)
    T = {}
    for cells in comps:
        if cells is largest:
            continue
        for (y, x) in cells:
            T[(y, x)] = bg
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

## fill_enclosed
_Fill the cells enclosed by the rectangle outline with its colour._  (sample: fill_enclosed_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
00055550
00050050
00050050
00050050
00050050
00055550
00000000
00000000
OUTPUT:
00055550
00055550
00055550
00055550
00055550
00055550
00000000
00000000
T:
........
....55..
....55..
....55..
....55..
........
........
........
```
**pair 1 (train 1)**
```
INPUT:
00000000
00000000
00000000
00022220
00020020
00022220
00000000
00000000
OUTPUT:
00000000
00000000
00000000
00022220
00022220
00022220
00000000
00000000
T:
........
........
........
........
....22..
........
........
........
```
**pair 2 (train 2)**
```
INPUT:
00000000
00000000
00008880
00008080
00008080
00008880
00000000
00000000
OUTPUT:
00000000
00000000
00008880
00008880
00008880
00008880
00000000
00000000
T:
........
........
........
.....8..
.....8..
........
........
........
```
**pair 3 (test)**
```
INPUT:
00001110
00001010
00001010
00001010
00001010
00001010
00001010
00001110
OUTPUT:
00001110
00001110
00001110
00001110
00001110
00001110
00001110
00001110
T:
........
.....1..
.....1..
.....1..
.....1..
.....1..
.....1..
........
```
**canonical solver:**
```python
from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    outside = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and g[r][c] == bg and (r, c) not in outside:
                outside.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in outside:
                outside.add((nr, nc)); q.append((nr, nc))
    fill = next(g[r][c] for r in range(H) for c in range(W) if g[r][c] != bg)
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and (r, c) not in outside:
                T[(r, c)] = fill
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

## gravity_water
_Every loose cell falls down and stacks at the bottom of its column._  (sample: gravity_water_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
500500000
000500000
000000005
000000000
000000000
000550000
050500505
500000000
000000000
OUTPUT:
000000000
000000000
000000000
000000000
000000000
000500000
000500000
500500005
550550505
T:
0..0.....
...0.....
........0
.........
.........
....0....
.0....0.0
...5....5
55.55.5.5
```
**pair 1 (train 1)**
```
INPUT:
661666666
666166166
666661666
611666666
616666161
666666661
161616666
166666611
666616661
OUTPUT:
666666666
666666666
666666666
666666666
666666666
666666661
661666661
111616161
111111111
T:
..6......
...6..6..
.....6...
.66......
.6....6.6
.........
6...6...1
.11.1.16.
1111.111.
```
**pair 2 (train 2)**
```
INPUT:
010001000
000000000
000100010
001000000
000100001
100001100
000000000
011000001
001110100
OUTPUT:
000000000
000000000
000000000
000000000
000000000
000000000
001100000
011101101
111111111
T:
.0...0...
.........
...0...0.
..0......
...0....0
0....00..
..11.....
...1.11..
11...1.11
```
**pair 3 (test)**
```
INPUT:
866668888
666888888
888866888
886886886
888888888
888888888
888688888
888888868
886868886
OUTPUT:
888888888
888888888
888888888
888888888
888888888
886888888
886868888
866666886
666666866
T:
.8888....
888......
....88...
..8..8..8
.........
..6......
..686....
.66666.86
66.6.6.6.
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for c in range(W):
        col_vals = [g[r][c] for r in range(H)]
        items = [v for v in col_vals if v != bg]
        new = [bg] * (H - len(items)) + items
        for r in range(H):
            if new[r] != col_vals[r]:
                T[(r, c)] = new[r]
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

## mirror
_Reflect the left-half shape across the vertical centre into the empty right half._  (sample: mirror_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000
000000
000000
000000
005000
505000
OUTPUT:
000000
000000
000000
000000
005500
505505
T:
......
......
......
......
...5..
...5.5
```
**pair 1 (train 1)**
```
INPUT:
700000
700000
007000
007000
707000
000000
OUTPUT:
700007
700007
007700
007700
707707
000000
T:
.....7
.....7
...7..
...7..
...7.7
......
```
**pair 2 (train 2)**
```
INPUT:
466666
666666
646666
666666
446666
446666
OUTPUT:
466664
666666
646646
666666
446644
446644
T:
.....4
......
....4.
......
....44
....44
```
**pair 3 (test)**
```
INPUT:
000000
909000
000000
900000
000000
000000
OUTPUT:
000000
909909
000000
900009
000000
000000
T:
......
...9.9
......
.....9
......
......
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            mc = W - 1 - c
            if g[r][c] == bg and g[r][mc] != bg:
                T[(r, c)] = g[r][mc]
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

## periodic_extension
_Extend each row's periodic dots across the whole row._  (sample: periodic_extension_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0007070700
0000000000
0000000000
0000000000
0000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0707070707
0000000000
0000000000
0000000000
0000000000
0000000000
T:
..........
..........
..........
..........
.7.......7
..........
..........
..........
..........
..........
```
**pair 1 (train 1)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000010101
0000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0101010101
0000000000
0000000000
T:
..........
..........
..........
..........
..........
..........
..........
.1.1......
..........
..........
```
**pair 2 (train 2)**
```
INPUT:
0000000000
0000000000
0000000000
1000100010
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
1000100010
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
T:
..........
..........
..........
..........
..........
..........
..........
..........
..........
..........
```
**pair 3 (test)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0707070700
0000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0707070707
0000000000
T:
..........
..........
..........
..........
..........
..........
..........
..........
.........7
..........
```
**canonical solver:**
```python
from collections import Counter
from math import gcd


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        pts = [c for c in range(W) if g[r][c] != bg]
        if len(pts) < 2:
            continue
        col = g[r][pts[0]]
        p = 0
        for i in range(len(pts) - 1):
            p = gcd(p, pts[i + 1] - pts[i])
        if p < 1:
            continue
        phase = pts[0] % p
        for c in range(W):
            if c % p == phase and g[r][c] == bg:
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
```

## periodic_repair
_Repair the holes (0) using the repeating tile's consensus value._  (sample: periodic_repair_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
900908988
089989989
988908988
989989989
OUTPUT:
988988988
989989989
988988988
989989989
T:
.88.8....
9........
....8....
.........
```
**pair 1 (train 1)**
```
INPUT:
567507507567
757750757007
567567567567
757750750757
OUTPUT:
567567567567
757757757757
567567567567
757757757757
T:
....6..6....
.....7...75.
............
.....7..7...
```
**pair 2 (train 2)**
```
INPUT:
344344340344
883083883883
344344344344
800883883880
040344344340
083883883880
344344344304
883083803803
OUTPUT:
344344344344
883883883883
344344344344
883883883883
344344344344
883883883883
344344344344
883883883883
T:
........4...
...8........
............
.83........3
3.4........4
8..........3
..........4.
...8...8..8.
```
**pair 3 (test)**
```
INPUT:
404343
505555
454545
434300
555555
454045
OUTPUT:
434343
555555
454545
434343
555555
454545
T:
.3....
.5....
......
....43
......
...5..
```
**canonical solver:**
```python
def infer_T(g):
    H, W = len(g), len(g[0])

    def consistent(pr, pc):
        seen = {}
        for r in range(H):
            for c in range(W):
                v = g[r][c]
                if v == 0:
                    continue
                k = (r % pr, c % pc)
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    pr = pc = None
    for a in range(1, H + 1):
        done = False
        for b in range(1, W + 1):
            if consistent(a, b):
                pr, pc = a, b; done = True; break
        if done:
            break
    template = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                template[(r % pr, c % pc)] = g[r][c]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0:
                k = (r % pr, c % pc)
                if k in template:
                    T[(r, c)] = template[k]
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

## ray_diag_to_edge
_A corner marker shoots a diagonal ray of its colour inward to the edge._  (sample: ray_diag_to_edge_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
500000
000000
000000
000000
000000
000000
OUTPUT:
500000
050000
005000
000500
000050
000005
T:
......
.5....
..5...
...5..
....5.
.....5
```
**pair 1 (train 1)**
```
INPUT:
000000
000000
000000
000000
000000
000008
OUTPUT:
800000
080000
008000
000800
000080
000008
T:
8.....
.8....
..8...
...8..
....8.
......
```
**pair 2 (train 2)**
```
INPUT:
800000
000000
000000
000000
000000
000000
OUTPUT:
800000
080000
008000
000800
000080
000008
T:
......
.8....
..8...
...8..
....8.
.....8
```
**pair 3 (test)**
```
INPUT:
000000
000000
000000
000000
000000
000001
OUTPUT:
100000
010000
001000
000100
000010
000001
T:
1.....
.1....
..1...
...1..
....1.
......
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    dirs = {(0, 0): (1, 1), (0, W - 1): (1, -1),
            (H - 1, 0): (-1, 1), (H - 1, W - 1): (-1, -1)}
    r, c = next((p for p in dirs if g[p[0]][p[1]] != bg))
    col = g[r][c]
    dr, dc = dirs[(r, c)]
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
```

## ray_diag_until_blocker
_A corner marker shoots a diagonal ray inward, stopping just before any blocker._  (sample: ray_diag_until_blocker_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
50000000
00000000
00000000
00000000
00009000
00000000
00000000
00000000
OUTPUT:
50000000
05000000
00500000
00050000
00009000
00000000
00000000
00000000
T:
........
.5......
..5.....
...5....
........
........
........
........
```
**pair 1 (train 1)**
```
INPUT:
77777778
77777777
77777777
77777777
77717777
77777777
77777777
77777777
OUTPUT:
77777778
77777787
77777877
77778777
77717777
77777777
77777777
77777777
T:
........
......8.
.....8..
....8...
........
........
........
........
```
**pair 2 (train 2)**
```
INPUT:
70000000
00000000
00000000
00090000
00000000
00000000
00000000
00000000
OUTPUT:
70000000
07000000
00700000
00090000
00000000
00000000
00000000
00000000
T:
........
.7......
..7.....
........
........
........
........
........
```
**pair 3 (test)**
```
INPUT:
33333333
33333333
33333333
33333333
33333333
33333333
30333333
23333333
OUTPUT:
33333333
33333333
33333333
33333333
33333333
33333333
30333333
23333333
T:
........
........
........
........
........
........
........
........
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    dirs = {(0, 0): (1, 1), (0, W - 1): (1, -1),
            (H - 1, 0): (-1, 1), (H - 1, W - 1): (-1, -1)}
    r, c = next((p for p in dirs if g[p[0]][p[1]] != bg))
    col = g[r][c]
    dr, dc = dirs[(r, c)]
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
```

## ray_to_edge
_A single marker on a grid edge shoots a ray of its own colour straight inward to the opposite edge._  (sample: ray_to_edge_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
050000
000000
000000
000000
000000
000000
OUTPUT:
050000
050000
050000
050000
050000
050000
T:
......
.5....
.5....
.5....
.5....
.5....
```
**pair 1 (train 1)**
```
INPUT:
000080
000000
000000
000000
000000
000000
OUTPUT:
000080
000080
000080
000080
000080
000080
T:
......
....8.
....8.
....8.
....8.
....8.
```
**pair 2 (train 2)**
```
INPUT:
080000
000000
000000
000000
000000
000000
OUTPUT:
080000
080000
080000
080000
080000
080000
T:
......
.8....
.8....
.8....
.8....
.8....
```
**pair 3 (test)**
```
INPUT:
000010
000000
000000
000000
000000
000000
OUTPUT:
000010
000010
000010
000010
000010
000010
T:
......
....1.
....1.
....1.
....1.
....1.
```
**canonical solver:**
```python
from collections import Counter


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
```

## ray_until_blocker
_An edge marker shoots a ray inward, stopping just before any blocker._  (sample: ray_until_blocker_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
00005000
00000000
00000000
00000000
00000000
00000000
00002000
00000000
OUTPUT:
00005000
00005000
00005000
00005000
00005000
00005000
00002000
00000000
T:
........
....5...
....5...
....5...
....5...
....5...
........
........
```
**pair 1 (train 1)**
```
INPUT:
78777777
77777777
77777777
77777777
77777777
77777777
73777777
77777777
OUTPUT:
78777777
78777777
78777777
78777777
78777777
78777777
73777777
77777777
T:
........
.8......
.8......
.8......
.8......
.8......
........
........
```
**pair 2 (train 2)**
```
INPUT:
00000070
00000000
00000000
00000000
00000000
00000000
00000010
00000000
OUTPUT:
00000070
00000070
00000070
00000070
00000070
00000070
00000010
00000000
T:
........
......7.
......7.
......7.
......7.
......7.
........
........
```
**pair 3 (test)**
```
INPUT:
44454444
44444444
44444444
44414444
44444444
44444444
44444444
44444444
OUTPUT:
44454444
44454444
44454444
44414444
44444444
44444444
44444444
44444444
T:
........
...5....
...5....
........
........
........
........
........
```
**canonical solver:**
```python
from collections import Counter


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
```

## rotate_translate
_Drop the whole object straight down until it rests on the floor._  (sample: rotate_translate_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
000000500
000000500
000000000
000000000
000000000
000000000
000000000
000000000
000000000
OUTPUT:
000000000
000000000
000000000
000000000
000000000
000000000
000000000
000000500
000000500
T:
......0..
......0..
.........
.........
.........
.........
.........
......5..
......5..
```
**pair 1 (train 1)**
```
INPUT:
666666666
666666666
666666666
166666666
116666666
116666666
666666666
666666666
666666666
OUTPUT:
666666666
666666666
666666666
666666666
666666666
666666666
166666666
116666666
116666666
T:
.........
.........
.........
6........
66.......
66.......
1........
11.......
11.......
```
**pair 2 (train 2)**
```
INPUT:
000000000
000000000
000000000
088000000
008000000
000000000
000000000
000000000
000000000
OUTPUT:
000000000
000000000
000000000
000000000
000000000
000000000
000000000
088000000
008000000
T:
.........
.........
.........
.00......
..0......
.........
.........
.88......
..8......
```
**pair 3 (test)**
```
INPUT:
222666222
222222222
222222222
222222222
222222222
222222222
222222222
222222222
222222222
OUTPUT:
222222222
222222222
222222222
222222222
222222222
222222222
222222222
222222222
222666222
T:
...222...
.........
.........
.........
.........
.........
.........
.........
...666...
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    delta = (H - 1) - max(r for r, c in cells)
    T = {}
    for (r, c) in cells:
        T[(r, c)] = bg                       # erase old position
    for (r, c) in cells:
        T[(r + delta, c)] = g[r][c]          # draw at new position (overrides erase)
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

## sandwich_fill
_Fill the background between each same-coloured pair (row, column, or diagonal)._  (sample: sandwich_fill_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
9000000000
0000300300
0000000000
9000000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
9000000000
9000333300
9000000000
9000000000
T:
..........
..........
..........
..........
..........
..........
..........
9....33...
9.........
..........
```
**pair 1 (train 1)**
```
INPUT:
0000000000
0000000000
0000000000
3000000040
0000000000
0000000000
0000000000
0000000040
3000000000
0000000000
OUTPUT:
0000000000
0000000000
0000000000
3000000040
3000000040
3000000040
3000000040
3000000040
3000000000
0000000000
T:
..........
..........
..........
..........
3.......4.
3.......4.
3.......4.
3.........
..........
..........
```
**pair 2 (train 2)**
```
INPUT:
3333333333
3333333333
3333333333
3333333333
3333333333
3333338383
3333333333
3333333333
3333333333
3333333333
OUTPUT:
3333333333
3333333333
3333333333
3333333333
3333333333
3333338883
3333333333
3333333333
3333333333
3333333333
T:
..........
..........
..........
..........
..........
.......8..
..........
..........
..........
..........
```
**pair 3 (test)**
```
INPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0060000000
0000000000
0000000000
0000008008
0060000000
OUTPUT:
0000000000
0000000000
0000000000
0000000000
0000000000
0060000000
0060000000
0060000000
0060008888
0060000000
T:
..........
..........
..........
..........
..........
..........
..6.......
..6.......
..6....88.
..........
```
**canonical solver:**
```python
from collections import Counter


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
```

## u_cup_fill
_Fill the open cup (two walls + floor) to the rim with its colour._  (sample: u_cup_fill_00001.json, tier 1, 3 train + 1 test)

**pair 0 (train 0)**
```
INPUT:
00000000
00000000
00000000
50000500
50000500
50000500
55555500
00000000
OUTPUT:
00000000
00000000
00000000
55555500
55555500
55555500
55555500
00000000
T:
........
........
........
.5555...
.5555...
.5555...
........
........
```
**pair 1 (train 1)**
```
INPUT:
00000000
00000000
00000000
00020200
00020200
00020200
00022200
00000000
OUTPUT:
00000000
00000000
00000000
00022200
00022200
00022200
00022200
00000000
T:
........
........
........
....2...
....2...
....2...
........
........
```
**pair 2 (train 2)**
```
INPUT:
00000000
00000000
00000000
00000000
00800800
00800800
00888800
00000000
OUTPUT:
00000000
00000000
00000000
00000000
00888800
00888800
00888800
00000000
T:
........
........
........
........
...88...
...88...
........
........
```
**pair 3 (test)**
```
INPUT:
00000000
00000000
00000000
00000000
10000001
10000001
11111111
00000000
OUTPUT:
00000000
00000000
00000000
00000000
11111111
11111111
11111111
00000000
T:
........
........
........
........
.111111.
.111111.
........
........
```
**canonical solver:**
```python
from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    col = g[cells[0][0]][cells[0][1]]
    top = min(r for r, c in cells); bottom = max(r for r, c in cells)
    left = min(c for r, c in cells); right = max(c for r, c in cells)
    T = {}
    for r in range(top, bottom):              # above the floor row
        for c in range(left + 1, right):      # between the walls
            if g[r][c] == bg:
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
```
