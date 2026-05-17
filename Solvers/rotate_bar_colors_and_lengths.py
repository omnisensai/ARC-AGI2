"""
Puzzle: 2601afb7
Rule name: rotate_bar_colors_and_lengths

Transformation rule:
For bottom-anchored vertical bars (sorted left to right), each bar takes the color of the previous bar and the length of the next bar, cycling around.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 5/5 LLM judges produced this exact rule name.
"""
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    bg = 7
    bars = []
    for c in range(W):
        col_vals = [input_grid[r][c] for r in range(H)]
        non_bg = [v for v in col_vals if v != bg]
        if non_bg:
            color = non_bg[0]
            length = len(non_bg)
            bars.append((c, color, length))
    bars.sort()
    cols = [b[0] for b in bars]
    colors = [b[1] for b in bars]
    lengths = [b[2] for b in bars]
    n = len(bars)
    new_colors = [colors[(i - 1) % n] for i in range(n)]
    new_lengths = [lengths[(i + 1) % n] for i in range(n)]
    out = [[bg] * W for _ in range(H)]
    for i, c in enumerate(cols):
        color = new_colors[i]
        length = new_lengths[i]
        for k in range(length):
            out[H - 1 - k][c] = color
    return out
