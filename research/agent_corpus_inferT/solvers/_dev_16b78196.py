import json

def _comps(g, bg, diag=True):
    H, W = len(g), len(g[0])
    seen = [[False]*W for _ in range(H)]
    res = []
    nbrs = [(1,0),(-1,0),(0,1),(0,-1)]
    if diag: nbrs += [(1,1),(1,-1),(-1,1),(-1,-1)]
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; st=[(r,c)]; cells=[]
                while st:
                    a,b = st.pop()
                    if 0<=a<H and 0<=b<W and not seen[a][b] and g[a][b]==col:
                        seen[a][b]=True; cells.append((a,b))
                        for dr,dc in nbrs: st.append((a+dr,b+dc))
                res.append((col, cells))
    return res

def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    bg = 0
    comps = _comps(g, bg, diag=True)
    # wall = largest
    comps.sort(key=lambda x: -len(x[1]))
    wall_col, wall_cells = comps[0]
    wall = set(wall_cells)
    shapes = [(col, set(cells)) for col, cells in comps[1:]]
    rs = set(r for r,c in wall_cells); cs = set(c for r,c in wall_cells)
    horizontal = (len(cs) == W)  # spans full width -> horizontal wall

    # occupancy of all non-bg (wall + shapes) for collision, but we will rebuild
    # We'll place shapes by nesting. Build T as dict cell->color.
    occ = set(wall)  # wall cells block

    # helper: given a set of cells, can we place at translation (dr,dc) without overlapping occ?
    def conflict(cells, dr, dc):
        for r,c in cells:
            if (r+dr, c+dc) in occ:
                return True
        return False
    def touches(cells, dr, dc, target):
        # does shifted cells have any 4-neighbor in target
        for r,c in cells:
            rr,cc = r+dr, c+dc
            for a,b in ((1,0),(-1,0),(0,1),(0,-1)):
                if (rr+a, cc+b) in target:
                    return True
        return False

    placements = []  # list of (color, set_of_abs_cells)

    # Determine perpendicular "into wall" directions
    if horizontal:
        wall_lo = min(rs); wall_hi = max(rs)
        # side candidates: above (push down into wall) and below (push up)
        sides = [('above', (1,0)), ('below', (-1,0))]
    else:
        wall_lo = min(cs); wall_hi = max(cs)
        sides = [('left', (0,1)), ('right', (0,-1))]

    # We process: repeatedly try to attach a shape to wall (penetrating a notch) -> start chain.
    # For chaining, attach further shapes nesting against current occ.

    remaining = list(shapes)

    def shape_dims(cells):
        rr=[r for r,c in cells]; cc=[c for r,c in cells]
        return min(rr),max(rr),min(cc),max(cc)

    # Function: best placement of a shape against current occ, given a fixed "approach" axis & direction.
    # Slide shape from far away toward wall along perp direction, scanning all parallel offsets;
    # choose the placement that maximizes penetration (number of shape cells that are within wall band rows/cols)
    # while not overlapping occ, and touching occ.

    def best_wall_attach(cells):
        c0 = list(cells)
        best = None
        rr=[r for r,c in c0]; cc=[c for r,c in c0]
        sh_h = max(rr)-min(rr)+1; sh_w = max(cc)-min(cc)+1
        # normalize to origin
        nr,nc = min(rr),min(cc)
        norm = [(r-nr,c-nc) for r,c in c0]
        if horizontal:
            for side,(pdr,pdc) in sides:
                for par in range(-sh_w, W):  # column offset
                    # try all row positions; we want to press into wall
                    if side=='above':
                        # shape below moving up? above means shape sits above wall, bottom pokes into wall (downwards)
                        # place so shape bottom near wall top, then push down (increase base row) until conflict
                        rng = range(wall_lo - sh_h, wall_hi+2)
                    else:
                        rng = range(wall_lo - sh_h, wall_hi+2)
                    for base in rng:
                        abs_cells = [(base+r, par+c) for r,c in norm]
                        if any(not(0<=x<H and 0<=y<W) for x,y in abs_cells): continue
                        if any((x,y) in occ for x,y in abs_cells): continue
                        # penetration = cells whose row in wall band
                        pen = sum(1 for x,y in abs_cells if wall_lo<=x<=wall_hi)
                        if pen==0: continue
                        # must be adjacent to wall (touching)
                        if not touches(norm, base, par, wall): continue
                        score = pen
                        if best is None or score>best[0]:
                            best=(score, side, abs_cells)
        else:
            for side,(pdr,pdc) in sides:
                for par in range(-sh_h, H):
                    rng = range(wall_lo - sh_w, wall_hi+2)
                    for base in rng:
                        abs_cells = [(par+r, base+c) for r,c in norm]
                        if any(not(0<=x<H and 0<=y<W) for x,y in abs_cells): continue
                        if any((x,y) in occ for x,y in abs_cells): continue
                        pen = sum(1 for x,y in abs_cells if wall_lo<=y<=wall_hi)
                        if pen==0: continue
                        if not touches(norm, par, base, wall): continue
                        score = pen
                        if best is None or score>best[0]:
                            best=(score, side, abs_cells)
        return best

    # Build mask T
    T = {}
    for (col, cells), abs_cells in []:
        pass

    return None
