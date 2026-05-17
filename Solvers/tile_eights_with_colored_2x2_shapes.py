"""
Puzzle: 626c0bcc
Rule name: tile_eights_with_colored_2x2_shapes

Transformation rule:
Partition all 8-cells into 2x2 blocks where each block is recolored by which of its four cells are filled: full square becomes 1, and the three L-shaped triominoes become 2, 3, or 4 according to which corner is missing.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: Claude agent R1 (v2 full-puzzle prompt — agent saw all pairs including
test answer and wrote code from the full spec).
Judge consensus: 5/5 tiebreaker.
"""
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    output = [[0]*cols for _ in range(rows)]

    eights = set()
    for r in range(rows):
        for c in range(cols):
            if input_grid[r][c] == 8:
                eights.add((r, c))

    shapes = {
        1: [(0,0),(0,1),(1,0),(1,1)],
        2: [(0,1),(1,0),(1,1)],
        4: [(0,0),(1,0),(1,1)],
        3: [(0,0),(0,1),(1,1)],
    }

    def backtrack(remaining, assignments):
        if not remaining:
            return assignments
        cell = min(remaining)
        r, c = cell
        for dr, dc in [(0,0),(0,-1),(-1,0),(-1,-1)]:
            br, bc = r+dr, c+dc
            if br < 0 or bc < 0 or br+1 >= rows or bc+1 >= cols:
                continue
            for color, offsets in shapes.items():
                cells = set((br+or_, bc+oc_) for or_, oc_ in offsets)
                if cell not in cells:
                    continue
                if cells.issubset(remaining):
                    result = backtrack(remaining - cells, assignments + [(color, cells)])
                    if result is not None:
                        return result
        return None

    result = backtrack(eights, [])
    if result is None:
        return output
    for color, cells in result:
        for r, c in cells:
            output[r][c] = color
    return output
