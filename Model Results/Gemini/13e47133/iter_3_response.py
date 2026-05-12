import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output = grid.copy()

    # 1. Identify Divider Lines
    row_divs = []
    for r in range(rows):
        unique, counts = np.unique(grid[r, :], return_counts=True)
        # A divider row is mostly one color and spans the width
        if counts.max() >= cols * 0.7:
            row_divs.append(r)
            
    col_divs = []
    for c in range(cols):
        unique, counts = np.unique(grid[:, c], return_counts=True)
        # A divider col is mostly one color and spans the height
        if counts.max() >= rows * 0.7:
            col_divs.append(c)

    # 2. Define Regions (Cells)
    r_bounds = sorted(list(set([0, rows] + row_divs + [r + 1 for r in row_divs])))
    c_bounds = sorted(list(set([0, cols] + col_divs + [c + 1 for c in col_divs])))
    
    # Filter bounds to only include the starts and ends of open regions
    regions_r = []
    for i in range(len(r_bounds)-1):
        if r_bounds[i] not in row_divs:
            regions_r.append((r_bounds[i], r_bounds[i+1]))
            
    regions_c = []
    for i in range(len(c_bounds)-1):
        if c_bounds[i] not in col_divs:
            regions_c.append((c_bounds[i], c_bounds[i+1]))

    # 3. Process each Cell
    for (r1, r2) in regions_r:
        for (c1, c2) in regions_c:
            region = grid[r1:r2, c1:c2]
            if region.size == 0: continue
            
            # Find background (most common color in the original region)
            bg_color = np.bincount(region.flatten()).argmax()
            
            # Map seeds to their ring depth
            ring_colors = {}
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    val = grid[rr, cc]
                    if val != bg_color:
                        # Depth is distance to nearest edge of the cell
                        depth = min(rr - r1, r2 - 1 - rr, cc - c1, c2 - 1 - cc)
                        ring_colors[depth] = val
            
            # Corner defines the initial/outermost color if no depth-0 seed
            current_color = grid[r1, c1]
            
            h, w = r2 - r1, c2 - c1
            max_depth = (min(h, w) + 1) // 2
            
            for d in range(max_depth):
                if d in ring_colors:
                    current_color = ring_colors[d]
                
                # Apply color to the ring at depth d
                for rr in range(r1 + d, r2 - d):
                    for cc in range(c1 + d, c2 - d):
                        if rr == r1 + d or rr == r2 - 1 - d or \
                           cc == c1 + d or cc == c2 - 1 - d:
                            output[rr, cc] = current_color
                            
    return output.tolist()