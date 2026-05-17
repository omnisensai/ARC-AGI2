"""
Puzzle: 18419cfa
Rule name: mirror_markers_across_box_gap

Transformation rule:
For each 8-bordered box, reflect the 2-colored markers across the axis perpendicular to the box's open side(s), filling in the missing symmetric half.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: initial 5-judge round produced no strict 3+ match;
tiebreaker round (5 new judges picking from 5 prior candidates) produced
5/5 unanimous on this name.
"""
import numpy as np
from scipy.ndimage import label

def solve(input_grid):
    G = np.array(input_grid)
    out = G.copy()

    eights_mask = (G == 8).astype(int)
    lbl, n = label(eights_mask, structure=np.ones((3, 3)))

    for i in range(1, n + 1):
        comp = (lbl == i)
        ey, ex = np.where(comp)
        if len(ey) == 0:
            continue
        y0, y1 = ey.min(), ey.max()
        x0, x1 = ex.min(), ex.max()

        ty_list = []
        tx_list = []
        for r in range(y0, y1 + 1):
            for c in range(x0, x1 + 1):
                if G[r, c] == 2:
                    ty_list.append(r)
                    tx_list.append(c)

        if not ty_list:
            continue

        height = y1 - y0 + 1
        width = x1 - x0 + 1

        top_count = int(comp[y0, x0:x1 + 1].sum())
        bot_count = int(comp[y1, x0:x1 + 1].sum())
        left_count = int(comp[y0:y1 + 1, x0].sum())
        right_count = int(comp[y0:y1 + 1, x1].sum())

        horizontal_mirror = (left_count < height / 2) and (right_count < height / 2)
        vertical_mirror = (top_count < width / 2) and (bot_count < width / 2)

        if horizontal_mirror:
            cx = (x0 + x1) / 2.0
            for y, x in zip(ty_list, tx_list):
                nx = int(round(2 * cx - x))
                if 0 <= nx < G.shape[1]:
                    out[y, nx] = 2
        elif vertical_mirror:
            cy = (y0 + y1) / 2.0
            for y, x in zip(ty_list, tx_list):
                ny = int(round(2 * cy - y))
                if 0 <= ny < G.shape[0]:
                    out[ny, x] = 2

    return out.tolist()
