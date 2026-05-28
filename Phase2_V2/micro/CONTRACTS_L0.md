# L0 Atom Ontology — Locked Definitions

L0 contains **static grid atoms only**.

No transformations.
No movement.
No filling.
No drawing.
No propagation.
No puzzle solving.

L0 teaches coordinate ontology:

> grid reality = coloured cells + coordinate relations + static structures

All atoms must be definable as sets of `(r, c)` cells plus colour/value relations.

---

## Canonical L0 atom list

### 1. cell / point
A single coordinate-value pair: `(r, c, value)`. A point occupies exactly one grid cell.

### 2. background
The empty/default colour of the grid. Usually the most frequent colour, but the detector must not assume this unless the contract says so.

### 3. colour
A cell value. ARC colours are integers, usually `0–9`.

### 4. colour_class
All cells in the grid with the same colour. Connectivity does not matter.
```python
cells = {(r, c) for g[r][c] == colour}
```

### 5. object
A selected set of non-background cells treated as one entity. Object identity is defined by the current contract. An object may be:
- one connected component
- one shape
- one colour class
- one bounded structure

**Do not assume object = component unless stated.**

### 6. component
A connected set of same-colour cells under a declared neighborhood. Must specify **4-connected OR 8-connected**. No default ambiguity.

### 7. blob
An irregular connected component. A blob has no required geometric shape beyond connectivity.

### 8. line
A contiguous same-colour segment in one row or one column. A line is either horizontal or vertical.

### 9. horizontal_line
A contiguous same-colour segment with constant row.
```python
all(r == r0 for r, c in cells)
```

### 10. vertical_line
A contiguous same-colour segment with constant column.
```python
all(c == c0 for r, c in cells)
```

### 11. diagonal
A contiguous same-colour segment where cells advance by one row and one column. Valid diagonals satisfy one of:
```python
r - c == constant
r + c == constant
```

### 12. bbox
The minimal axis-aligned rectangle containing a set of cells.
```python
top    = min(r)
bottom = max(r)
left   = min(c)
right  = max(c)
```
Bbox is metadata, not a drawn object.

### 13. anchor
A reference coordinate for an object. Default anchor is bbox top-left: `(top, left)`. Other anchors must be explicitly declared. Anchor is static metadata, not movement.

### 14. edge
A grid boundary row or column.
```
top row:    r = 0
bottom row: r = H-1
left edge:  c = 0
right edge: c = W-1
```

### 15. corner
One of the four grid corner cells: `(0,0), (0,W-1), (H-1,0), (H-1,W-1)`.

### 16. neighborhood_4
Orthogonal adjacency only: `(r+1,c), (r-1,c), (r,c+1), (r,c-1)`.

### 17. neighborhood_8
Orthogonal + diagonal adjacency: all 8 surrounding cells.

### 18. boundary
Cells of an object that touch background or outside-grid under 4-neighborhood. For an object cell `(r,c)`, it is boundary if at least one 4-neighbor is outside the object.

### 19. interior
Static interior has TWO allowed meanings. The contract must declare which one:
- **object_interior** — object cells that are not boundary cells.
- **enclosed_region** — background cells enclosed by a container/ring.

**Do not mix these silently.**

### 20. hole
A background region fully enclosed by non-background cells. A region of background cells not connected to the outer border through background cells.

### 21. region
A connected set of cells, usually background cells, under declared connectivity. Must specify 4-connected or 8-connected.

### 22. container
A closed boundary plus the region it encloses. A container is static. It does not imply filling.

### 23. hollow_rectangle
A rectangle outline:
- top edge present
- bottom edge present
- left edge present
- right edge present
- interior not part of the rectangle object

### 24. filled_rectangle
A solid axis-aligned rectangle where every cell inside bbox has the same object colour.

### 25. square
A filled or hollow rectangle with equal height and width. Must declare filled or hollow.

### 26. u_cup
A static U-shaped structure:
- left vertical wall
- right vertical wall
- bottom horizontal floor
- open top
- interior gap between walls

A U-cup does not imply fill.

### 27. ring / outline
A closed 1-cell-thick boundary around an interior region. Ring/outline is **static**. Do not use this term for the *operation* of drawing an outline.

### 28. gap
Background cells between two aligned same-colour endpoints. Alignment must be row, column, or diagonal. Gap is static empty space, not the act of filling it.

### 29. seed
A single cell that marks a source coordinate for a later operation. Static meaning:
```
seed = source/origin cell
```
A seed does not itself propagate or transform anything in L0.

### 30. marker
A single cell that carries metadata about another object or location. Static meaning:
```
marker = label/reference/instruction cell
```
Marker does not transform anything in L0.

### 31. axis
A static reference line for symmetry. Allowed axes:
```
vertical
horizontal
main diagonal
anti-diagonal
```
Axis is metadata, not a transformation.

### 32. periodic_tile
A repeating local pattern defined by period height and period width. Static object:
```python
period = (pr, pc)
template[(r % pr, c % pc)] = value
```
No repair implied.

### 33. pattern
A recurring arrangement of colours/cells. More general than periodic_tile. A pattern must be represented as coordinates and values relative to an anchor.

---

## Explicitly excluded from L0

These are NOT L0 atoms because they imply transformation or action. They belong to L1+ operator layers:

```
ray, blocker, frame, draw_bbox, fill, flood, move, drop,
rotate, flip, scale, repair, extend, copy, recolor, delete, select, sort
```

---

## Seed vs Marker vs Anchor (do not collapse)

### seed
Answers: **Where does an operation start?**
Examples: flood source, ray source, growth origin.

### marker
Answers: **What metadata/reference does this cell provide?**
Examples: target location, recolour value, object label, legend cell.

### anchor
Answers: **Which coordinate represents this object?**
Examples: bbox top-left, centroid-like reference, seed coordinate if explicitly declared.

**Do not collapse seed, marker, and anchor into one concept.**

---

## L0 rule

Every L0 record must teach one or more static coordinate concepts. It must not require the model to infer or perform a transformation.

Preferred L0 training targets:
```
grid → detector code
grid → object mask
grid → coordinate metadata
grid → classification + bbox/cells
```

Avoid identity-only targets except as auxiliary examples.

---

## Output grammar pin (Claude's addition)

To preserve the locked LoRA grammar (playbook principle #1: `solve(input_grid) → output_grid`), all L0 training records emit a **grid output**. Coordinate structures (cell sets, bboxes, predicates) returned by library functions are *rendered* into the output grid by the solver — the library returns the structure; the solver renders it.

Concretely, every L0 solver follows the same shape:

```python
def solve(input_grid):
    result = LIBRARY_CALL(input_grid)         # the L0 atom: returns set/struct/bool
    H, W = len(input_grid), len(input_grid[0])
    out = [[0] * W for _ in range(H)]          # blank canvas
    for (r, c) in result:                      # render the structure as a mask
        out[r][c] = MARK                       # marker colour signals "this is in the set"
    return out
```

This keeps `solve: grid → grid` uniform across L0, L1, L2 — the LoRA learns one top-level grammar; only the body varies.
