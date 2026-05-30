recs = [json.loads(l) for l in open('Phase2_V2/run1/eval/baseline_qwen2.5-coder-7b-instruct.jsonl')][:10]
for r in recs:
    print(f'\n========== {r[\"puzzle\"]}  [{r[\"failure_mode\"]}] ==========\n')
    print(r['model_output_raw'])
"

========== 00d62c1b  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == '3':
                # Check up
                if i > 0 and input_grid[i-1][j] == '3':
                    input_grid[i][j] = '4'
                # Check down
                if i < rows - 1 and input_grid[i+1][j] == '3':
                    input_grid[i][j] = '4'
                # Check left
                if j > 0 and input_grid[i][j-1] == '3':
                    input_grid[i][j] = '4'
                # Check right
                if j < cols - 1 and input_grid[i][j+1] == '3':
                    input_grid[i][j] = '4'
    
    return input_grid
```

========== 09629e4f  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Create a new grid with the same dimensions as the input grid
    output_grid = [[0] * cols for _ in range(rows)]
    
    # Iterate over each cell in the input grid
    for i in range(rows):
        for j in range(cols):
            # If the cell is '5', set it to '3' if it's not already '3'
            if input_grid[i][j] == '5':
                output_grid[i][j] = '3'
            # If the cell is '0', set it to '2' if it's not already '2'
            elif input_grid[i][j] == '0':
                output_grid[i][j] = '2'
            # Otherwise, keep the value unchanged
            else:
                output_grid[i][j] = input_grid[i][j]
    
    return output_grid
```

This function iterates through each cell in the input grid and applies the specified transformations:
- Cells containing '5' are changed to '3'.
- Cells containing '0' are changed to '2'.
- All other cells remain unchanged.

========== 12422b43  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Create a copy of the input grid to store the result
    result_grid = [row[:] for row in input_grid]
    
    # Iterate through each cell in the grid
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != 0:
                # Find the last non-zero value in the current column
                for k in range(i, -1, -1):
                    if input_grid[k][j] != 0:
                        result_grid[i][j] = input_grid[k][j]
                        break
    
    return result_grid
```

========== 13f06aa5  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for r in range(rows):
        for c in range(cols):
            if input_grid[r][c] == 0:
                input_grid[r][c] = 1
            elif input_grid[r][c] == 1:
                input_grid[r][c] = 2
            elif input_grid[r][c] == 2:
                input_grid[r][c] = 3
            elif input_grid[r][c] == 3:
                input_grid[r][c] = 4
            elif input_grid[r][c] == 4:
                input_grid[r][c] = 5
            elif input_grid[r][c] == 5:
                input_grid[r][c] = 6
            elif input_grid[r][c] == 6:
                input_grid[r][c] = 7
            elif input_grid[r][c] == 7:
                input_grid[r][c] = 8
            elif input_grid[r][c] == 8:
                input_grid[r][c] = 9
            elif input_grid[r][c] == 9:
                input_grid[r][c] = 0
    
    return input_grid
```

========== 142ca369  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != 0:
                count = 0
                for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < rows and 0 <= nj < cols and input_grid[ni][nj] == 0:
                        count += 1
                input_grid[i][j] += count
    
    return input_grid
```

========== 1acc24af  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == '5':
                # Check the four possible directions (up, down, left, right)
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    while 0 <= ni < rows and 0 <= nj < cols and input_grid[ni][nj] != '5':
                        input_grid[ni][nj] = str(int(input_grid[ni][nj]) + 1)
                        ni += di
                        nj += dj
    
    return input_grid
```

========== 1b59e163  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    output_grid = []
    for row in input_grid:
        new_row = []
        for i in range(len(row)):
            if row[i] == 1:
                count = 0
                while i + 1 < len(row) and row[i + 1] == 1:
                    count += 1
                    i += 1
                if count > 0:
                    new_row.append(1)
                    new_row.extend([count + 1] * count)
                else:
                    new_row.append(1)
            else:
                new_row.append(row[i])
        output_grid.append(new_row)
    return output_grid
```

========== 1c56ad9f  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    output_grid = [list(row) for row in input_grid]
    
    for i in range(len(output_grid)):
        for j in range(len(output_grid[i])):
            if output_grid[i][j] != '0':
                if i > 0 and output_grid[i-1][j] == '0':
                    output_grid[i-1][j] = output_grid[i][j]
                if i < len(output_grid) - 1 and output_grid[i+1][j] == '0':
                    output_grid[i+1][j] = output_grid[i][j]
                if j > 0 and output_grid[i][j-1] == '0':
                    output_grid[i][j-1] = output_grid[i][j]
                if j < len(output_grid[i]) - 1 and output_grid[i][j+1] == '0':
                    output_grid[i][j+1] = output_grid[i][j]
    
    return output_grid
```

========== 1da012fc  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == '8':
                input_grid[i][j] = '2'
            elif input_grid[i][j] == '5':
                input_grid[i][j] = '3'
            elif input_grid[i][j] == '6':
                input_grid[i][j] = '4'
            elif input_grid[i][j] == '7':
                input_grid[i][j] = '5'
            elif input_grid[i][j] == '9':
                input_grid[i][j] = '6'
    
    return input_grid
```

========== 1f0c79e5  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != 0:
                value = input_grid[i][j]
                for x in range(max(0, i-1), min(rows, i+2)):
                    for y in range(max(0, j-1), min(cols, j+2)):
                        input_grid[x][y] = value
    
    return input_grid
```
root@e3241538a7a6:/workspace/ARC-AGI2# # === CODER puzzles 11-20 ===
python3 -c "
import json
recs = [json.loads(l) for l in open('Phase2_V2/run1/eval/baseline_qwen2.5-coder-7b-instruct.jsonl')][10:20]
for r in recs:
    print(f'\n========== {r[\"puzzle\"]}  [{r[\"failure_mode\"]}] ==========\n')
    print(r['model_output_raw'])
"

========== 22233c11  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Find the top-left corner of the region to be replaced
    start_row, start_col = None, None
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != 0:
                start_row, start_col = i, j
                break
        if start_row is not None:
            break
    
    # If no non-zero element found, return the original grid
    if start_row is None:
        return input_grid
    
    # Replace the region with 8s
    for i in range(start_row, rows):
        for j in range(start_col, cols):
            if input_grid[i][j] == 0:
                input_grid[i][j] = 8
    
    return input_grid
```

========== 2281f1f4  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    n = len(input_grid)
    for i in range(n):
        for j in range(n):
            if input_grid[i][j] == 5:
                # Check if it's the first occurrence of 5 in this row
                if sum(1 for k in range(j) if input_grid[i][k] == 5) == 0:
                    input_grid[i][j] = 2
    return input_grid
```

========== 22a4bbc2  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Create a copy of the input grid to store the result
    output_grid = [row[:] for row in input_grid]
    
    # Define the mapping from old values to new values
    value_map = {
        0: 0,
        1: 2,
        2: 1,
        8: 8
    }
    
    # Iterate over each cell in the grid and apply the transformation
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] in value_map:
                output_grid[i][j] = value_map[input_grid[i][j]]
    
    return output_grid
```

========== 230f2e48  [EMPTY_OR_INVALID] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == 2:
                # Check up
                if i >  and input_grid[i-1][j] != 2:
                    input_grid[i-1][j] = 7
                # Check down
                if i < rows - 1 and input_grid[i+1][j] != 2:
                    input_grid[i+1][j] = 7
                # Check left
                if j >  and input_grid[i][j-1] != 2:
                    input_grid[i][j-1] = 7
                # Check right
                if j < cols - 1 and input_grid[i][j+1] != 2:
                    input_grid[i][j+1] = 7
    
    return input_grid
```

========== 253bf280  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == 8:
                input_grid[i][j] = 3
                if i > 0:
                    input_grid[i - 1][j] = 3
                if i < rows - 1:
                    input_grid[i + 1][j] = 3
                if j > 0:
                    input_grid[i][j - 1] = 3
                if j < cols - 1:
                    input_grid[i][j + 1] = 3
    
    return input_grid
```

========== 256b0a75  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Create a copy of the input grid to store the result
    output_grid = [row[:] for row in input_grid]
    
    # Define the directions for movement (up, down, left, right)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Iterate over each cell in the grid
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] != 0:
                # Find the color of the current cell
                color = input_grid[i][j]
                
                # Initialize the count of the same color in adjacent cells
                count_same_color = 1
                
                # Check all four directions for the same color
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    while 0 <= ni < rows and 0 <= nj < cols and input_grid[ni][nj] == color:
                        count_same_color += 1
                        ni += di
                        nj += dj
                
                # If there are more than one adjacent cells with the same color
                if count_same_color > 1:
                    # Replace the current cell with the count of adjacent cells
                    output_grid[i][j] = count_same_color
    
    return output_grid
```

========== 27a77e38  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == 4:
                if i > 0 and input_grid[i-1][j] != 4:
                    input_grid[i-1][j] = 4
                if i < rows - 1 and input_grid[i+1][j] != 4:
                    input_grid[i+1][j] = 4
                if j > 0 and input_grid[i][j-1] != 4:
                    input_grid[i][j-1] = 4
                if j < cols - 1 and input_grid[i][j+1] != 4:
                    input_grid[i][j+1] = 4
    
    return input_grid
```

========== 2dd70a9a  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    for i in range(rows):
        for j in range(cols):
            if input_grid[i][j] == 0:
                continue
            
            # Check the current cell and its neighbors
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            changed = False
            
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols and input_grid[ni][nj] != 0:
                    input_grid[i][j] += 1
                    changed = True
            
            if changed:
                input_grid[i][j] -= 1
    
    return input_grid
```

========== 30f42897  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    
    # Create a copy of the input grid to store the result
    output_grid = [row[:] for row in input_grid]
    
    # Iterate through each cell in the grid
    for i in range(rows):
        for j in range(cols):
            # If the current cell is not 8, skip it
            if input_grid[i][j] != 8:
                continue
            
            # Check the top and bottom neighbors
            if i > 0 and input_grid[i-1][j] == 8:
                output_grid[i-1][j] = 4
            if i < rows - 1 and input_grid[i+1][j] == 8:
                output_grid[i+1][j] = 4
            
            # Check the left and right neighbors
            if j > 0 and input_grid[i][j-1] == 8:
                output_grid[i][j-1] = 4
            if j < cols - 1 and input_grid[i][j+1] == 8:
                output_grid[i][j+1] = 4
    
    return output_grid
```

========== 332202d5  [WRONG_OUTPUT] ==========

```python
def solve(input_grid):
    n = len(input_grid)
    output_grid = [[0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if input_grid[i][j] == 8:
                output_grid[i][j] = 8
            elif input_grid[i][j] == 1:
                output_grid[i][j] = 1
            else:
                count_ones = 0
                count_eights = 0
                
                # Check left neighbors
                if j > 0 and input_grid[i][j - 1] == 1:
                    count_ones += 1
                if j > 0 and input_grid[i][j - 1] == 8:
                    count_eights += 1
                    
                # Check right neighbors
                if j < n - 1 and input_grid[i][j + 1] == 1:
                    count_ones += 1
                if j < n - 1 and input_grid[i][j + 1] == 8:
                    count_eights += 1
                    
                # Check top neighbors
                if i > 0 and input_grid[i - 1][j] == 1:
                    count_ones += 1
                if i > 0 and input_grid[i - 1][j] == 8:
                    count_eights += 1
                    
                # Check bottom neighbors
                if i < n - 1 and input_grid[i + 1][j] == 1:
                    count_ones += 1
                if i < n - 1 and input_grid[i + 1][j] == 8:
                    count_eights += 1
                    
                if count_ones >= 2:
                    output_grid[i][j] = 1
                elif count_eights >= 2:
                    output_grid[i][j] = 8
                else:
                    output_grid[i][j] = input_grid[i][j]
                    
    return output_grid
```
root@e3241538a7a6:/workspace/ARC-AGI2# 
