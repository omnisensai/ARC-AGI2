from collections import Counter
import copy

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    output_grid = copy.deepcopy(input_grid)

    # 1. Find all bounding boxes
    boxes = []
    for r1 in range(H):
        for r2 in range(r1 + 2, H):
            for c1 in range(W):
                for c2 in range(c1 + 2, W):
                    color = input_grid[r1][c1]

                    # Check top and bottom edges
                    valid = True
                    for c in range(c1, c2 + 1):
                        if input_grid[r1][c] != color or input_grid[r2][c] != color:
                            valid = False
                            break
                    if not valid: continue

                    # Check left and right edges
                    for r in range(r1, r2 + 1):
                        if input_grid[r][c1] != color or input_grid[r][c2] != color:
                            valid = False
                            break
                    if not valid: continue

                    # Check that the inside is not completely filled with the boundary color
                    has_non_boundary = False
                    for r in range(r1 + 1, r2):
                        for c in range(c1 + 1, c2):
                            if input_grid[r][c] != color:
                                has_non_boundary = True
                                break
                        if has_non_boundary: break

                    if has_non_boundary:
                        boxes.append((r1, r2, c1, c2))

    # Filter out nested boxes (keep only the outermost ones)
    final_boxes = []
    for b in boxes:
        is_inside = False
        for other in boxes:
            if b == other: continue
            if other[0] <= b[0] and other[1] >= b[1] and other[2] <= b[2] and other[3] >= b[3]:
                is_inside = True
                break
        if not is_inside:
            final_boxes.append(b)

    # 2. Fix the periodic pattern inside each box
    for (r1, r2, c1, c2) in final_boxes:
        h_box = r2 - r1 - 1
        w_box = c2 - c1 - 1

        # Test row-wise periodicity (pattern of rows repeating vertically)
        best_cost_r = float('inf')
        best_p_r = -1
        fixed_box_r = None

        for p in range(1, h_box // 2 + 1):
            cost = 0
            pattern = []
            for i in range(p):
                elements = []
                for r in range(i, h_box, p):
                    elements.append([input_grid[r1 + 1 + r][c1 + 1 + c] for c in range(w_box)])
                mode_row = []
                for c in range(w_box):
                    scalars = [row[c] for row in elements]
                    mode = Counter(scalars).most_common(1)[0][0]
                    mode_row.append(mode)
                    cost += sum(1 for s in scalars if s != mode)
                pattern.append(mode_row)
            if cost < best_cost_r:
                best_cost_r = cost
                best_p_r = p
                fixed_box_r = []
                for r in range(h_box):
                    fixed_box_r.append(pattern[r % p])

        # Test column-wise periodicity (pattern of columns repeating horizontally)
        best_cost_c = float('inf')
        best_p_c = -1
        fixed_box_c = None

        for p in range(1, w_box // 2 + 1):
            cost = 0
            pattern = []
            for i in range(p):
                elements = []
                for c in range(i, w_box, p):
                    elements.append([input_grid[r1 + 1 + r][c1 + 1 + c] for r in range(h_box)])
                mode_col = []
                for r in range(h_box):
                    scalars = [col[r] for col in elements]
                    mode = Counter(scalars).most_common(1)[0][0]
                    mode_col.append(mode)
                    cost += sum(1 for s in scalars if s != mode)
                pattern.append(mode_col)
            if cost < best_cost_c:
                best_cost_c = cost
                best_p_c = p
                fixed_box_c = [[0] * w_box for _ in range(h_box)]
                for c in range(w_box):
                    col_data = pattern[c % p]
                    for r in range(h_box):
                        fixed_box_c[r][c] = col_data[r]

        # Decide the orientation with the clearest periodic signal
        chosen_box = None
        if best_cost_r < best_cost_c:
            chosen_box = fixed_box_r
        elif best_cost_c < best_cost_r:
            chosen_box = fixed_box_c
        else:
            if best_cost_r != float('inf'):
                # Tiebreaker: pick the orientation that has more observed repetitions
                reps_r = h_box / best_p_r
                reps_c = w_box / best_p_c
                if reps_r >= reps_c:
                    chosen_box = fixed_box_r
                else:
                    chosen_box = fixed_box_c
            else:
                # The box is too small to detect periodicity in either direction
                continue

        # 3. Apply the fixed pattern to the output grid
        for r in range(h_box):
            for c in range(w_box):
                output_grid[r1 + 1 + r][c1 + 1 + c] = chosen_box[r][c]

    return output_grid
