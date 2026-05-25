import json

def _comps(g, bg=0, diag=True):
    H, W = len(g), len(g[0])
    seen = [[False]*W for _ in range(H)]
    res = []
    nb = [(1,0),(-1,0),(0,1),(0,-1)]
    if diag: nb += [(1,1),(1,-1),(-1,1),(-1,-1)]
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; st=[(r,c)]; cells=[]
                while st:
                    a,b = st.pop()
                    if 0<=a<H and 0<=b<W and not seen[a][b] and g[a][b]==col:
                        seen[a][b]=True; cells.append((a,b))
                        for dr,dc in nb: st.append((a+dr,b+dc))
                res.append((col, cells))
    return res

def _group(cells):
    cells=set(cells); seen=set(); res=[]
    for x in cells:
        if x in seen: continue
        st=[x]; g=[]
        while st:
            a=st.pop()
            if a in seen or a not in cells: continue
            seen.add(a); g.append(a); r,c=a
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                st.append((r+dr,c+dc))
        res.append(frozenset(g))
    return res

def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    comps = _comps(g)
    comps.sort(key=lambda x: -len(x[1]))
    wall = set(comps[0][1])
    rsW = set(r for r,c in wall); csW = set(c for r,c in wall)
    horizontal = (len(csW) == W)
    lo, hi = (min(rsW), max(rsW)) if horizontal else (min(csW), max(csW))
    band_rect = set((r,c) for r in range(lo,hi+1) for c in range(W)) if horizontal \
                else set((r,c) for r in range(H) for c in range(lo,hi+1))
    holes = set(x for x in band_rect if g[x[0]][x[1]] == 0)
    hgs = [set(h) for h in _group(holes)]

    shapes = []  # (color, norm_cells_list)
    orig_cells = set()
    for col, cells in comps[1:]:
        orig_cells |= set(cells)
        rr=[r for r,c in cells]; cc=[c for r,c in cells]
        nr,nc=min(rr),min(cc)
        shapes.append((col, [(r-nr,c-nc) for r,c in cells]))

    def band_coord(x, y):
        return x if horizontal else y

    # find best exact-notch placement for each shape
    def best_notch(norm):
        best=None
        for dr in range(-H, H+1):
            for dc in range(-W, W+1):
                ab=[(r+dr,c+dc) for r,c in norm]
                if any(not(0<=x<H and 0<=y<W) for x,y in ab): continue
                if any((x,y) in wall for x,y in ab): continue
                inband=set((x,y) for x,y in ab if lo<=band_coord(x,y)<=hi)
                if not inband: continue
                if inband in hgs:
                    if best is None or len(inband)>best[0]:
                        best=(len(inband), dr, dc)
        return best

    anchors = []  # (color, norm, dr, dc, pen)
    used = [False]*len(shapes)
    for i,(col,norm) in enumerate(shapes):
        bn = best_notch(norm)
        if bn and bn[0] >= 2:
            anchors.append((i, col, norm, bn[1], bn[2]))

    placements = []  # (color, set of abs cells)  -- including in-wall pokes
    occ = set(wall)

    # which perp direction is "outward" for an anchor placed at (dr,dc)?
    # The shape straddles the wall edge. Outward = side where most shape cells are (outside band).
    for (i, col, norm, dr, dc) in anchors:
        used[i] = True
        ab = set((r+dr,c+dc) for r,c in norm)
        placements.append((col, ab))
        occ |= ab

    # Build chains: from each anchor, grow outward by attaching remaining shapes that nest tightest.
    # We process anchors; for chaining we just greedily, among all remaining shapes & both directions,
    # attach to occ wherever a shape nests with maximal overlap (tightest) and is adjacent.
    # We bias attachment to grow AWAY from wall.

    def perp_outward(ab):
        # determine outward direction (unit vector) for a placed shape relative to wall band
        cells_out = [band_coord(x,y) for x,y in ab]
        # if shape mostly below band (coord>hi) outward is +; if above (<lo) outward is -
        below = sum(1 for v in cells_out if v>hi)
        above = sum(1 for v in cells_out if v<lo)
        return 1 if below>=above else -1

    # For each anchor compute outward dir; assign chains.
    chains = []
    for (i, col, norm, dr, dc) in anchors:
        ab = set((r+dr,c+dc) for r,c in norm)
        d = perp_outward(ab)
        chains.append({'dir': d, 'occ': set(ab)})

    # iteratively attach remaining shapes. Each chain grows strictly outward (perp dir d).
    # For a candidate shape we scan parallel alignments; for each we drop it inward (toward wall)
    # along perp until it just touches occ without overlap -> that's its nested placement.
    # Pick the (shape, alignment) that yields minimal outward extent, tie-break max contact.
    def contact(absc):
        return sum(1 for x,y in absc for a,b in ((1,0),(-1,0),(0,1),(0,-1)) if (x+a,y+b) in occ)

    # parallel-dim size of each chain (fixed by anchor)
    for ch in chains:
        if horizontal:
            ps = set(y for x,y in ch['occ'])
        else:
            ps = set(x for x,y in ch['occ'])
        ch['pmin'] = min(ps); ch['pmax'] = max(ps)

    def best_nest(ch, norm):
        # return (added_extent, abs_cells) for nesting shape (norm) onto chain ch, or None
        d = ch['dir']; pmin = ch['pmin']; pmax = ch['pmax']
        rr=[r for r,c in norm]; cc=[c for r,c in norm]
        sh_par = (max(cc)+1) if horizontal else (max(rr)+1)
        if sh_par != (pmax - pmin + 1):
            return None
        par = pmin
        # slide from far outward inward; stop at first contact (deepest inward reachable from outside)
        # d=1: outward = large coord. start base large, decrease.
        if d==1:
            base_seq = range(H+W, -H-W-1, -1)
        else:
            base_seq = range(-H-W, H+W+1)
        prev_ext = None; prev_cells = None; prev_touch = False
        for base in base_seq:
            if horizontal:
                absc=[(base+r, par+c) for r,c in norm]
            else:
                absc=[(par+r, base+c) for r,c in norm]
            if any(not(0<=x<H and 0<=y<W) for x,y in absc):
                if prev_touch:
                    break
                prev_ext=None; prev_cells=None; prev_touch=False
                continue
            if any((x,y) in occ for x,y in absc):
                if prev_touch:
                    break
                prev_ext=None; prev_cells=None; prev_touch=False
                continue
            touch = any((x+a,y+b) in ch['occ'] for x,y in absc for a,b in ((1,0),(-1,0),(0,1),(0,-1)))
            if horizontal:
                ext = max(x for x,y in absc) if d==1 else -min(x for x,y in absc)
            else:
                ext = max(y for x,y in absc) if d==1 else -min(y for x,y in absc)
            prev_ext = ext; prev_cells = set(absc); prev_touch = touch
        if prev_touch:
            ct = sum(1 for x,y in prev_cells for a,b in ((1,0),(-1,0),(0,1),(0,-1)) if (x+a,y+b) in ch['occ'])
            return prev_ext, ct, prev_cells
        return None

    # global greedy: at each step pick (chain, shape) with min outward extent, max contact
    changed = True
    while changed:
        changed = False
        best = None  # (ext, -contact, shape_idx, chain_idx, abs_cells)
        for ci,ch in enumerate(chains):
            for j,(col,norm) in enumerate(shapes):
                if used[j]: continue
                bn = best_nest(ch, norm)
                if bn is None: continue
                ext, ct, absc = bn
                key=(ext, -ct, j)
                if best is None or key < best[0]:
                    best=(key, ci, absc)
        if best is not None:
            key, ci, absc = best
            j = key[2]
            used[j]=True
            ch=chains[ci]
            placements.append((shapes[j][0], absc))
            occ |= absc
            ch['occ'] |= absc
            changed=True

    T = {}
    # erase original shape positions
    for x,y in orig_cells:
        T[(x,y)] = 0
    for col, cells in placements:
        for x,y in cells:
            T[(x,y)] = col
    return T

def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r,c), v in T.items():
        out[r][c] = v
    return out

def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)

if __name__ == '__main__':
    d = json.load(open('research/agent_corpus_inferT/_tasks/16b78196.json'))
    for split in ('train','test'):
        for i,p in enumerate(d[split]):
            got = solve(p['input'])
            ok = got == p['output']
            print(split, i, 'PASS' if ok else 'FAIL')
            if not ok:
                for r in range(len(got)):
                    if got[r]!=p['output'][r]:
                        diffs=[(c,p['output'][r][c],got[r][c]) for c in range(len(got[r])) if got[r][c]!=p['output'][r][c]]
                        print('  row',r,'diffs(col,exp,got)',diffs[:8])
