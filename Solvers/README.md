# Solvers

Deterministic Python solvers for ARC-AGI-2 puzzles, organized by transformation rule.

Each solver is named after the rule it encodes (not the puzzle ID), so the
library grows as a catalog of generalizable transformations. The puzzle ID it
was derived from is recorded in the module docstring.

**Validation gate:** every solver here passes **all training pairs and the test
pair** of its source puzzle, verified by `run_feedback.py`.

## Index

| Rule | Source | One-line description |
|---|---|---|
| [`chebyshev_room_erosion_fill`](chebyshev_room_erosion_fill.py) | [13e47133](https://arcprize.org/tasks/13e47133) | Partition the grid into 4-connected non-wall rooms; fill each cell with a repeating cycle of the room's seed colors indexed by its Chebyshev depth from the room's actual perimeter (so non-rectangular rooms work the same as rectangular ones); preserve walls. |
| [`complete_partial_shapes_from_templates`](complete_partial_shapes_from_templates.py) | [d6542281](https://arcprize.org/tasks/d6542281) | For each cluster that is a translated subset of a larger complete template cluster, fill in the missing cells using the template's pattern aligned to the partial fragment. |
| [`connect_color_pairs_with_diagonals`](connect_color_pairs_with_diagonals.py) | [1f876c06](https://arcprize.org/tasks/1f876c06) | For each color appearing exactly twice, draw a straight line of that color between its two cells along the axis-aligned or diagonal step direction connecting them. |
| [`extend_plus_axes_and_diagonals`](extend_plus_axes_and_diagonals.py) | [fe9372f3](https://arcprize.org/tasks/fe9372f3) | From the plus-shaped 2-cross, extend its horizontal and vertical axes to the grid edges marking every third cell as 4 and the rest as 8, and draw 1s along both diagonals through the cross center. |
| [`extend_zero_markers_across_bands`](extend_zero_markers_across_bands.py) | [855e0971](https://arcprize.org/tasks/855e0971) | Within each uniform-colored band (rows or columns), extend every zero marker into a full perpendicular line spanning that band's width. |
| [`mark_2x2_block_diagonal_corners`](mark_2x2_block_diagonal_corners.py) | [95990924](https://arcprize.org/tasks/95990924) | For each 2x2 block of 5s, place 1, 2, 3, 4 at the four diagonally adjacent cells just outside its top-left, top-right, bottom-left, and bottom-right corners. |
| [`mirror_markers_across_box_gap`](mirror_markers_across_box_gap.py) | [18419cfa](https://arcprize.org/tasks/18419cfa) | For each 8-bordered box, reflect the 2-colored markers across the axis perpendicular to the box's open side(s), filling in the missing symmetric half. |
| [`periodic_motif_repair`](periodic_motif_repair.py) | [135a2760](https://arcprize.org/tasks/135a2760) | Decompose the grid into rectangular panels by all-background separator rows/columns; in each panel infer the best-fitting periodic tile (scoring `cost = mismatches + 0.4 × tile_area` so trivial near-full tiles don't win) and reconstruct the panel from that tile. |
| [`recolor_shapes_by_junction_type`](recolor_shapes_by_junction_type.py) | [e509e548](https://arcprize.org/tasks/e509e548) | Each connected component of 3s is recolored based on its topology: 2 if it has a T-junction or 3+ endpoints, 6 if it has 2+ right-angle corners, otherwise 1. |
| [`replace_non_top2_colors_with_seven`](replace_non_top2_colors_with_seven.py) | [9caf5b84](https://arcprize.org/tasks/9caf5b84) | Keep the two most frequent colors in the grid unchanged and replace every other cell with 7. |
| [`rotate_bar_colors_and_lengths`](rotate_bar_colors_and_lengths.py) | [2601afb7](https://arcprize.org/tasks/2601afb7) | For bottom-anchored vertical bars (sorted left to right), each bar takes the color of the previous bar and the length of the next bar, cycling around. |
| [`seeded_reachable_wall_contouring`](seeded_reachable_wall_contouring.py) | [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | From a unique seed, flood-fill the reachable region; only edge-touching 1-clusters act as wall barriers; draw the contour in 7; preserve walls adjacent to or inside the region, remove unreachable walls. |
| [`stamp_template_on_anchor_singletons`](stamp_template_on_anchor_singletons.py) | [3e980e27](https://arcprize.org/tasks/3e980e27) | For each lone pixel whose color matches an anchor color inside a multi-cell template shape, replicate the rest of that template around the pixel (mirroring horizontally when the anchor color is 2). |

## Solver structure

Every solver file follows the same shape:

```python
"""
Puzzle: <id>
Rule name: <snake_case_name>

Transformation rule:
<plain-English statement of what the algorithm does, including every case
the rule must handle. This is the LLM-readable specification of the rule.>

Validation: training N/N + test pass on the official puzzle JSON.
"""

# Named color constants (no magic numbers).
# Helper functions (BFS, etc.) shared across solvers when useful.

def solve(input_grid):
    ...
    return output_grid
```

## Why a catalog

This directory is the foundation for fine-tuning a small model on the
transformation algebra (`+ = - .` plus `~`). Each solver is a worked example
of how a substrate-encoded rule maps to executable Python. The set grows
incrementally; we don't add a solver until it clears the validator on its
source puzzle.
