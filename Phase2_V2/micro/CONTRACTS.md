# Micro-family contracts (explicit, to remove hidden ambiguity)

Each family's exact rule, so there is no inference about marker handling,
connectivity, colour source, or size behaviour. "bg" = background; unless noted
it is the most-common colour (and the structural 0 in tier 0). The acceptance
gate + contract validator enforce these.

Columns:
- **conn** — connectivity the rule uses (4 / 8 / —).
- **seed/marker** — how a seed/marker is identified, whether it is *consumed*
  (erased/overwritten) and whether it is *excluded* from object search.
- **out colour** — where the painted colour comes from: `read` (from the input)
  or `fixed:N` (a constant the family always uses).
- **size** — `same` (output dims == input) or `changes` (different — separate class).

## Rays & lines
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| ray_to_edge | one edge marker shoots a ray to the far edge | — | source = the single edge non-bg cell; stays | read | same |
| ray_until_blocker | ray stops one cell before a non-bg obstacle | — | one edge source; stays; blocker = any non-bg on path | read | same |
| ray_diag_to_edge | corner marker shoots a diagonal ray to far corner | — | one corner source; stays | read | same |
| ray_diag_until_blocker | diagonal ray stops before an obstacle | — | one corner source; stays | read | same |
| complete_line | fill between two same-colour endpoints | — | endpoints are the only non-bg cells; stay | read | same |
| sandwich_fill | fill the gap between every same-colour pair (H/V/diag) | — | none | read | same |

## Enclosure / fill / contour
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| u_cup_fill | fill the open cup to its rim | — | none | read (cup colour) | same |
| fill_enclosed | fill cells sealed inside a closed outline (any shape) | 4 (flood from border) | none | read (outline colour) | same |
| boundary_mask | hollow a solid shape to its 1-cell outline | 4 (interior test) | none | →bg | same |
| fence_4conn | outline the shape, orthogonal neighbours only (open corners) | 4 | none — **fence colour is fixed** | **fixed:8** | same |
| fence_8conn | outline the shape, incl. diagonal corners (square ring) | 8 | none — **fence colour is fixed** | **fixed:8** | same |

## Components / selection (4-vs-8 matched pair)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| component_4conn | keep the largest 4-connected blob, erase the rest | 4 | none | unchanged / →bg | same |
| component_8conn | keep the largest 8-connected blob, erase the rest | 8 | none | unchanged / →bg | same |
| extract_largest_recolor | recolour the largest blob to the marker colour; erase smaller blobs | 4 (blobs) | **marker = rarest non-bg single cell; NOT erased (stays as legend); EXCLUDED from blob search** | read (= marker colour) | same |

## Symmetry (split — each fixed-axis, unambiguous)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| symmetry_complete_vertical | mirror left half into empty right half (vertical axis, fixed) | — | none | read | same |
| symmetry_complete_horizontal | mirror top half into empty bottom half (horizontal axis, fixed) | — | none | read | same |

## Periodicity
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| periodic_extension | **per row**: extend periodic dots across the row (period = gcd of gaps) | — | none | read (per row) | same |
| periodic_repair | restore holes in a 2D periodic tile (smallest period, consensus) | — | bg here = **holes are 0** (not most-common); template from non-0 cells | read (template) | same |

## Simulation / motion
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| gravity_water | loose cells fall & stack at the bottom of each column | — | none | read | same |
| drop_to_floor | a rigid object falls as one piece to the floor | — | none | read; old cells →bg | same |
| ball_roll | seed enters edge, rolls, turns at walls, **leaves a trail** | 4 step + perpendicular turn | source = single border cell; stays; trail = its colour | read | same |
| maze_runner | same physics, **no trail** — ball rests at the dead end | 4 step + perpendicular turn | source = single border cell; **consumed (entrance →bg)**, ball drawn at end | read | same |

## Seed-radiate (4-vs-8 matched pair)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| cross_from_seed | seed radiates 4 orthogonal arms to the edges | 4 dirs | the single non-bg cell; stays | read | same |
| star_from_seed | seed radiates 8 arms (orthogonal + diagonal) to the edges | 8 dirs | the single non-bg cell; stays | read | same |

## Seed-flood (4-vs-8 matched pair)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| flood_from_seed | seed floods the **background cells 4-connected to it**; walls block; seed stays | 4 | seed = rarest non-bg single cell; stays | read (= seed colour) | same |
| flood_from_seed_8 | same, 8-connected (crosses diagonal gaps) | 8 | seed = rarest non-bg single cell; stays | read | same |

## Markers (seed-as-trigger)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| move_to_marker | move object so its bbox top-left lands on the marker | — | **marker = rarest non-bg single cell; it is the destination ANCHOR and is CONSUMED** (covered by the moved object); object = non-bg non-marker cells; old cells →bg | read (object colour) | same |
| copy_to_markers | stamp a copy of the prototype at every marker | — | prototype = the one multi-cell component; markers = single cells of a distinct colour; **anchor = prototype bbox top-left lands on each marker; markers consumed; prototype stays** | read (prototype colour) | same |
| recolor_by_marker | each object takes the colour of the marker touching it | object comps **4**-conn; marker adjacency **8**-conn | object colour = most-common non-bg; markers = other non-bg colours; **marker excluded from object comps; marker not recoloured (stays)** | read (= marker colour) | same |

## Whole-grid geometry (same-size)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| flip_horizontal | mirror the WHOLE grid left<->right: out[r][c]=in[r][W-1-c] | — | none | read | same |
| flip_vertical | mirror the WHOLE grid top<->bottom: out[r][c]=in[H-1-r][c] | — | none | read | same |
| draw_bbox | draw the object's bounding-box rectangle outline (4 edges at min/max row/col) | — | none | read (object colour) | same |

## Diff-size geometry (SEPARATE CLASS — the per-cell T-map does not apply)
| family | rule | conn | seed/marker | out colour | size |
|---|---|---|---|---|---|
| crop_to_bbox | output = tight bounding box of the non-bg content | — | none | gather (copy from input) | **changes** → (bbox h, bbox w) |
| scale_2x | every cell becomes a 2×2 block | — | none | gather: out[r][c]=in[r//2][c//2] | **changes** → (2H, 2W) |
| rotate_90 | rotate the whole grid 90° clockwise: out[i][j]=in[H-1-j][i] | — | none | gather | **changes** → (W, H) |

---

These contracts are the authority. If a generator ever drifts from its contract,
the contract validator (`validate_contracts.py`) catches it (precondition audit +
adversarial probes), independent of how many sample tasks happen to pass.
