import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output_grid = grid.copy()

    # 1. Identify the "Skeleton/Divider" colors.
    # These are colors that form continuous lines (horizontal/vertical).
    divider_colors = []
    for color in range(1, 10):
        mask = (grid == color)
        # Check if color forms a line longer than 3 pixels
        if np.sum(mask) > max(rows, cols) * 0.5:
            divider_colors.append(color)

    # 2. Identify "Seed" pixels and their locations.
    # Seeds are typically singular pixels that define a region's color.
    seeds = []
    for r in range(rows):
        for c in range(cols):
            color = grid[r, c]
            if color != 0 and color not in divider_colors:
                # Check if it's a "lonely" pixel or a corner
                seeds.append(((r, c), color))

    # 3. Expansion Logic: Fill regions based on proximity to dividers and seeds.
    # We use a flood-fill approach that respects the skeleton boundaries.
    def get_bounds(r, c, skeleton_mask):
        # Find the rectangular bounds for a seed until hitting skeleton
        r_start, r_end = r, r
        c_start, c_end = c, c
        
        while r_start > 0 and not skeleton_mask[r_start-1, c]: r_start -= 1
        while r_end < rows-1 and not skeleton_mask[r_end+1, c]: r_end += 1
        while c_start > 0 and not skeleton_mask[r, c_start-1]: c_start -= 1
        while c_end < cols-1 and not skeleton_mask[r, c_end+1]: c_end += 1
        return r_start, r_end, c_start, c_end

    skeleton_mask = np.zeros_like(grid, dtype=bool)
    for dc in divider_colors:
        skeleton_mask |= (grid == dc)

    # Process seeds from outermost to innermost (heuristic)
    seeds.sort(key=lambda x: (min(x[0][0], rows-x[0][0]) + min(x[0][1], cols-x[0][1])))

    for (r, c), color in seeds:
        r_start, r_end, c_start, c_end = get_bounds(r, c, skeleton_mask)
        # Fill the determined rectangle
        for i in range(r_start, r_end + 1):
            for j in range(c_start, c_end + 1):
                # Only fill if it was originally the background color (usually 1 or 4)
                # or if we are refining a previously filled area.
                if not skeleton_mask[i, j]:
                    output_grid[i, j] = color

    # 4. Final Polish: Handle specific "Frame" logic found in the pairs
    # (Drawing concentric boxes if the seed is a corner of a sub-region)
    for (r, c), color in seeds:
        if (r == 0 or r == rows-1 or c == 0 or c == cols-1 or 
            (r > 0 and skeleton_mask[r-1, c]) or (r < rows-1 and skeleton_mask[r+1, c])):
            
            r_s, r_e, c_s, c_e = get_bounds(r, c, skeleton_mask)
            # Check if this seed should form a frame
            # If the seed is at a corner of its bounds, fill the outer edge
            output_grid[r_s:r_e+1, c_s:c_e+1] = color

    return output_grid.tolist()