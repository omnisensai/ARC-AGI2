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
| [`chebyshev_room_erosion_fill`](chebyshev_room_erosion_fill.py) | [13e47133](https://arcprize.org/tasks/13e47133) | Wall lines partition the grid into 4-connected non-wall rooms. For each room, every cell's depth = its Chebyshev (8-direction) distance from the room's boundary, where a boundary cell is any room cell on the grid edge or 8-adjacent to a wall / outside the room. The non-backgro... |
| [`complete_partial_shapes_from_templates`](complete_partial_shapes_from_templates.py) | [d6542281](https://arcprize.org/tasks/d6542281) | For each cluster that is a translated subset of a larger complete template cluster, fill in the missing cells using the template's pattern aligned to the partial fragment. |
| [`connect_color_pairs_with_diagonals`](connect_color_pairs_with_diagonals.py) | [1f876c06](https://arcprize.org/tasks/1f876c06) | For each color appearing exactly twice, draw a straight line of that color between its two cells along the axis-aligned or diagonal step direction connecting them. |
| [`draw_crosses_with_intersection_markers`](draw_crosses_with_intersection_markers.py) | [23581191](https://arcprize.org/tasks/23581191) | For each colored pixel, draw a full-row and full-column line of its color through it, and mark the two cross-intersection cells with color 2. |
| [`extend_plus_axes_and_diagonals`](extend_plus_axes_and_diagonals.py) | [fe9372f3](https://arcprize.org/tasks/fe9372f3) | From the plus-shaped 2-cross, extend its horizontal and vertical axes to the grid edges marking every third cell as 4 and the rest as 8, and draw 1s along both diagonals through the cross center. |
| [`extend_scatter_pixels_to_rectangle`](extend_scatter_pixels_to_rectangle.py) | [2c608aff](https://arcprize.org/tasks/2c608aff) | For each scattered pixel that shares a row or column with the solid rectangle, draw a line of that pixel's color from the pixel up to (but not into) the nearest edge of the rectangle. |
| [`extend_zero_markers_across_bands`](extend_zero_markers_across_bands.py) | [855e0971](https://arcprize.org/tasks/855e0971) | Within each uniform-colored band (rows or columns), extend every zero marker into a full perpendicular line spanning that band's width. |
| [`fill_boxes_and_leak_through_gap`](fill_boxes_and_leak_through_gap.py) | [292dd178](https://arcprize.org/tasks/292dd178) | For each rectangular box outlined by 1s, fill its interior with 2s and, if the border has a missing 1, extend a line of 2s outward from that gap to the grid edge. |
| [`fill_inner_gap_between_rectangles`](fill_inner_gap_between_rectangles.py) | [d6ad076f](https://arcprize.org/tasks/d6ad076f) | Between the two non-zero rectangles, fill the rectangular region bounded by their overlapping rows/columns (shrunk by one on each side) with color 8. |
| [`fill_zero_3x3_blocks_with_one`](fill_zero_3x3_blocks_with_one.py) | [6cf79266](https://arcprize.org/tasks/6cf79266) | Find every non-overlapping 3x3 region of all zeros in the grid and recolor those cells to 1. |
| [`mark_2x2_block_diagonal_corners`](mark_2x2_block_diagonal_corners.py) | [95990924](https://arcprize.org/tasks/95990924) | For each 2x2 block of 5s, place 1, 2, 3, 4 at the four diagonally adjacent cells just outside its top-left, top-right, bottom-left, and bottom-right corners. |
| [`mirror_markers_across_box_gap`](mirror_markers_across_box_gap.py) | [18419cfa](https://arcprize.org/tasks/18419cfa) | For each 8-bordered box, reflect the 2-colored markers across the axis perpendicular to the box's open side(s), filling in the missing symmetric half. |
| [`partition_rows_by_markers_into_bordered_bands`](partition_rows_by_markers_into_bordered_bands.py) | [0f63c0b9](https://arcprize.org/tasks/0f63c0b9) | Sort non-zero pixels by row to split the grid into horizontal bands (one per pixel), then paint each band's left/right borders and the pixel's own row in that pixel's color, additionally drawing top/bottom edges for the first and last bands. |
| [`periodic_motif_repair`](periodic_motif_repair.py) | [135a2760](https://arcprize.org/tasks/135a2760) | Decompose the grid into rectangular panels by all-background separator rows/columns; in each panel infer the best-fitting periodic tile (scoring `cost = mismatches + 0.4 × tile_area` so trivial near-full tiles don't win) and reconstruct the panel from that tile. |
| [`recolor_foreground_in_two_clusters`](recolor_foreground_in_two_clusters.py) | [36fdfd69](https://arcprize.org/tasks/36fdfd69) | Within the bounding box of each cluster of 2-cells, recolor every foreground (non-zero, non-2) cell to 4. |
| [`recolor_shapes_by_junction_type`](recolor_shapes_by_junction_type.py) | [e509e548](https://arcprize.org/tasks/e509e548) | Each connected component of 3s is recolored based on its topology: 2 if it has a T-junction or 3+ endpoints, 6 if it has 2+ right-angle corners, otherwise 1. |
| [`replace_non_top2_colors_with_seven`](replace_non_top2_colors_with_seven.py) | [9caf5b84](https://arcprize.org/tasks/9caf5b84) | Keep the two most frequent colors in the grid unchanged and replace every other cell with 7. |
| [`reverse_values_along_path`](reverse_values_along_path.py) | [5792cb4d](https://arcprize.org/tasks/5792cb4d) | Trace the single connected non-background path from one endpoint to the other and write the sequence of cell values back along the path in reverse order. |
| [`rotate_bar_colors_and_lengths`](rotate_bar_colors_and_lengths.py) | [2601afb7](https://arcprize.org/tasks/2601afb7) | For bottom-anchored vertical bars (sorted left to right), each bar takes the color of the previous bar and the length of the next bar, cycling around. |
| [`seeded_reachable_wall_contouring`](seeded_reachable_wall_contouring.py) | [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | From the unique 6 seed, flood-fill through the background to compute the reachable region — only edge-touching 1-clusters act as wall barriers. Contour the reachable region with 7. Preserve walls touching or inside the region; remove unreachable walls. The edge-barrier framing... |
| [`slide_shape_to_edge_by_color`](slide_shape_to_edge_by_color.py) | [f3e62deb](https://arcprize.org/tasks/f3e62deb) | Move the single hollow square to a grid edge chosen by its color (6=top, 4=bottom, 8=right, 3=left), keeping its perpendicular position unchanged. |
| [`stamp_template_on_anchor_singletons`](stamp_template_on_anchor_singletons.py) | [3e980e27](https://arcprize.org/tasks/3e980e27) | For each lone pixel whose color matches an anchor color inside a multi-cell template shape, replicate the rest of that template around the pixel, mirroring horizontally when the anchor color is 2. |
| [`tile_eights_with_colored_2x2_shapes`](tile_eights_with_colored_2x2_shapes.py) | [626c0bcc](https://arcprize.org/tasks/626c0bcc) | Partition all 8-cells into 2x2 blocks where each block is recolored by which of its four cells are filled: full square becomes 1, and the three L-shaped triominoes become 2, 3, or 4 according to which corner is missing. |

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
