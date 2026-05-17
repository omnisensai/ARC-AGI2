"""
Puzzle: 9caf5b84
Rule name: replace_non_top2_colors_with_seven

Transformation rule:
Keep the two most frequent colors in the grid unchanged and replace every other cell with 7.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: 3/5 LLM judges produced this exact rule name.
"""
from collections import Counter

def solve(input_grid):
    cnt = Counter()
    for row in input_grid:
        for v in row:
            cnt[v] += 1
    top2 = set(v for v, _ in cnt.most_common(2))
    return [[v if v in top2 else 7 for v in row] for row in input_grid]
