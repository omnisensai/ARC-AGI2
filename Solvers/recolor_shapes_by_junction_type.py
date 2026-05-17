"""
Puzzle: e509e548
Rule name: recolor_shapes_by_junction_type

Transformation rule:
Each connected component of 3s is recolored based on its topology: 2 if it has a T-junction or 3+ endpoints, 6 if it has 2+ right-angle corners, otherwise 1.

Validation: all 4/4 pairs (training + test) of the source puzzle pass.
Source: agent-generated R1 code (Claude general-purpose, seed prompt v1).
Judge consensus: initial 5-judge round produced no strict 3+ match;
tiebreaker round (5 new judges picking from 5 prior candidates) produced
5/5 unanimous on this name.
"""
def solve(input_grid):
    from collections import deque
    H = len(input_grid)
    W = len(input_grid[0])
    visited = [[False]*W for _ in range(H)]
    out = [[0]*W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 3 and not visited[r][c]:
                comp = []
                q = deque([(r, c)])
                visited[r][c] = True
                while q:
                    cr, cc = q.popleft()
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < H and 0 <= nc < W and not visited[nr][nc] and input_grid[nr][nc] == 3:
                                visited[nr][nc] = True
                                q.append((nr, nc))

                cells = set(comp)
                endpoints = 0
                corners = 0
                tjunc = 0
                for cr, cc in cells:
                    nbrs = []
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if (cr + dr, cc + dc) in cells:
                            nbrs.append((dr, dc))
                    if len(nbrs) == 1:
                        endpoints += 1
                    elif len(nbrs) == 2:
                        (a, b), (c2, d) = nbrs
                        if a * c2 + b * d == 0:
                            corners += 1
                    elif len(nbrs) >= 3:
                        tjunc += 1

                if tjunc >= 1 or endpoints >= 3:
                    color = 2
                elif corners >= 2:
                    color = 6
                else:
                    color = 1

                for cr, cc in cells:
                    out[cr][cc] = color

    return out
