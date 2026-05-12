import numpy as np

def solve(input_grid):
    grid = np.array(input_grid)
    rows, cols = grid.shape
    output = grid.copy()

    # 1. Identify Divider Lines
    # Dividers are rows/cols that are mostly the same color (not the background)
    def find_dividers(arr):
        divs = []
        for i, line in enumerate(arr):
            unique, counts = np.unique(line, return_counts=True)
            if len(unique) > 1:
                # If a line has a dominant color that isn't the background (found via mode)
                mode_color = unique[np.argmax(counts)]
                if counts[np.argmax(counts)] > len(line) * 0.5:
                    # Check if this color is consistent across the grid as a divider
                    divs.append((i, mode_color))
        return divs

    row_divs = []
    # Identify horizontal dividers
    for r in range(rows):
        unique, counts = np.unique(grid[r, :], return_counts=True)
        if len(unique) <= 3 and counts.max() > cols * 0.6:
            row_divs.append(r)
            
    col_divs = []
    # Identify vertical dividers
    for c in range(cols):
        unique, counts = np.unique(grid[:, c], return_counts=True)
        if len(unique) <= 3 and counts.max() > rows * 0.6:
            col_divs.append(c)

    # 2. Define Regions
    r_bounds = [0] + row_divs + [rows]
    c_bounds = [0] + col_divs + [cols]

    for i in range(len(r_bounds)-1):
        for j in range(len(c_bounds)-1):
            r1, r2 = r_bounds[i], r_bounds[i+1]
            c1, c2 = c_bounds[j], c_bounds[j+1]
            
            # Adjust to exclude divider lines
            sub_r1 = r1 + (1 if i > 0 else 0)
            sub_r2 = r2 - (1 if i < len(r_bounds)-2 else 0)
            sub_c1 = c1 + (1 if j > 0 else 0)
            sub_c2 = c2 - (1 if j < len(c_bounds)-2 else 0)
            
            # Find seeds in this region
            region = grid[r1:r2, c1:c2]
            bg_color = np.bincount(region.flatten()).argmax()
            seeds = []
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    if grid[rr, cc] != bg_color and (rr not in row_divs) and (cc not in col_divs):
                        seeds.append(((rr, cc), grid[rr, cc]))
            
            if not seeds:
                # Fill with background or corner color if logic dictates
                output[r1:r2, c1:c2] = grid[r1, c1]
                continue

            # Expansion Logic: Concentric rings
            # Determine rings based on distance from region boundary
            h = r2 - r1
            w = c2 - c1
            num_rings = (min(h, w) + 1) // 2
            
            # Map seeds to rings
            ring_colors = {}
            for (sr, sc), sc_val in seeds:
                dist = min(sr - r1, r2 - 1 - sr, sc - c1, c2 - 1 - sc)
                ring_colors[dist] = sc_val
            
            # Determine outer color (corner seed or existing)
            outer_color = grid[r1, c1]
            
            current_color = outer_color
            for dist in range(num_rings):
                if dist in ring_colors:
                    current_color = ring_colors[dist]
                
                # Fill the ring
                for rr in range(r1 + dist, r2 - dist):
                    for cc in range(c1 + dist, c2 - dist):
                        # Only fill the "border" of the current inner rectangle
                        if rr == r1 + dist or rr == r2 - 1 - dist or \
                           cc == c1 + dist or cc == c2 - 1 - dist:
                            output[rr, cc] = current_color

    return output.tolist()