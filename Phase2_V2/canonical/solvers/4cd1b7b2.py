def infer_T(input_grid):
    # The grid is a partially-filled Latin square: each row and each column must
    # contain every non-zero symbol exactly once. 0 marks a cell to be filled.
    # infer_T computes the fill values via constrained backtracking over blanks.
    H, W = len(input_grid), len(input_grid[0])
    full = set(v for row in input_grid for v in row if v != 0)
    grid = [row[:] for row in input_grid]
    blanks = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 0]

    def candidates(r, c):
        used = set()
        for cc in range(W):
            if grid[r][cc] != 0:
                used.add(grid[r][cc])
        for rr in range(H):
            if grid[rr][c] != 0:
                used.add(grid[rr][c])
        return [v for v in full if v not in used]

    def backtrack(i):
        if i == len(blanks):
            return True
        # Most-constrained-variable heuristic: choose the blank with fewest options.
        best = None
        best_cands = None
        best_j = i
        for j in range(i, len(blanks)):
            r, c = blanks[j]
            cands = candidates(r, c)
            if best_cands is None or len(cands) < len(best_cands):
                best, best_cands, best_j = (r, c), cands, j
                if len(cands) <= 1:
                    break
        r, c = best
        blanks[i], blanks[best_j] = blanks[best_j], blanks[i]
        for v in best_cands:
            grid[r][c] = v
            if backtrack(i + 1):
                return True
        grid[r][c] = 0
        blanks[i], blanks[best_j] = blanks[best_j], blanks[i]
        return False

    backtrack(0)

    T = [[None] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0:
                T[r][c] = grid[r][c]
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
