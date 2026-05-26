from collections import Counter, deque

def get_bg(g): return Counter(v for row in g for v in row).most_common(1)[0][0]

def frame_mask(gi,bg):
    H=len(gi);W=len(gi[0]);mask=[[False]*W for _ in range(H)]
    rowband,colband,_=band_lines(gi,bg)
    for r in rowband:
        for c in range(W): mask[r][c]=True
    for c in colband:
        for r in range(H): mask[r][c]=True
    return mask

def comps(gi, bg, fm):
    H=len(gi);W=len(gi[0]);seen=[[False]*W for _ in range(H)];res=[]
    dirs=[(dy,dx) for dy in(-1,0,1) for dx in(-1,0,1) if (dy,dx)!=(0,0)]
    for r in range(H):
        for c in range(W):
            if seen[r][c] or gi[r][c]==bg or fm[r][c]: continue
            q=deque([(r,c)]);seen[r][c]=True;cur=[]
            while q:
                y,x=q.popleft();cur.append((y,x,gi[y][x]))
                for dy,dx in dirs:
                    ny,nx=y+dy,x+dx
                    if 0<=ny<H and 0<=nx<W and not seen[ny][nx] and gi[ny][nx]!=bg and not fm[ny][nx]:
                        seen[ny][nx]=True;q.append((ny,nx))
            res.append(cur)
    return res

def is_creature(cur): return any(v==8 for y,x,v in cur)
def is_marker(cur): return all(v==9 for y,x,v in cur)

def band_lines(gi,bg):
    # return rowbands: dict row->color, colbands: dict col->color, and dir map color->set(dirs)
    H=len(gi);W=len(gi[0])
    rowband={};colband={};dirs={}
    for r in range(H):
        cnt=Counter(gi[r]);mc,n=cnt.most_common(1)[0]
        if mc!=bg and n>=W-8:
            rowband[r]=mc
            dirs.setdefault(mc,set()).add('top' if r<H/2 else 'bottom')
    for c in range(W):
        col=[gi[r][c] for r in range(H)];cnt=Counter(col);mc,n=cnt.most_common(1)[0]
        if mc!=bg and n>=H-8:
            colband[c]=mc
            dirs.setdefault(mc,set()).add('left' if c<W/2 else 'right')
    return rowband,colband,dirs

def band_positions(gi,bg):
    # color -> list of ('row',index) or ('col',index)
    H=len(gi);W=len(gi[0]);res={}
    for r in range(H):
        cnt=Counter(gi[r]);mc,n=cnt.most_common(1)[0]
        if mc!=bg and n>=W-8: res.setdefault(mc,[]).append(('row',r))
    for c in range(W):
        col=[gi[r][c] for r in range(H)];cnt=Counter(col);mc,n=cnt.most_common(1)[0]
        if mc!=bg and n>=H-8: res.setdefault(mc,[]).append(('col',c))
    return res

def band_dirs_at(bp,pr,pc):
    # color -> set of directions of that band relative to destination point (pr,pc)
    out={}
    for col,lst in bp.items():
        s=set()
        for orient,idx in lst:
            if orient=='row': s.add('top' if idx<pr else 'bottom')
            else: s.add('left' if idx<pc else 'right')
        out[col]=s
    return out

def grid_of(cur):
    rs=[y for y,x,v in cur];cs=[x for y,x,v in cur]
    r0,r1=min(rs),max(rs);c0,c1=min(cs),max(cs)
    g=[['.']*(c1-c0+1) for _ in range(r1-r0+1)]
    for y,x,v in cur: g[y-r0][x-c0]=v
    return g,r0,c0

def rot90(g): return [list(r) for r in zip(*g[::-1])]
def fliph(g): return [row[::-1] for row in g]
def variants(g):
    res=[];cur=[row[:] for row in g]
    for k in range(4):
        res.append((k,0,[row[:] for row in cur]));res.append((k,1,fliph(cur)));cur=rot90(cur)
    return res

def marker_dirs(g):
    H=len(g);W=len(g[0])
    body=[(r,c) for r in range(H) for c in range(W) if g[r][c]==8]
    br=[r for r,c in body];bc=[c for r,c in body]
    rmin,rmax,cmin,cmax=min(br),max(br),min(bc),max(bc)
    res={}
    for r in range(H):
        for c in range(W):
            v=g[r][c]
            if v in ('.',8,9): continue
            d=set()
            if r<rmin: d.add('top')
            if r>rmax: d.add('bottom')
            if c<cmin: d.add('left')
            if c>cmax: d.add('right')
            res.setdefault(v,set()).update(d)
    return res

def pupil_pts(g):
    return [(r,c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]==9]

def normset(pts):
    r0=min(r for r,c in pts);c0=min(c for r,c in pts)
    return frozenset((r-r0,c-c0) for r,c in pts)

def infer_T(input_grid):
    gi=input_grid
    H=len(gi);W=len(gi[0])
    bg=get_bg(gi);fm=frame_mask(gi,bg)
    rowband,colband,_=band_lines(gi,bg)
    bp=band_positions(gi,bg)
    cs=comps(gi,bg,fm)
    creatures=[c for c in cs if is_creature(c)]
    markers=[c for c in cs if is_marker(c)]
    place={}
    clear=set()
    used=set()
    for cr in creatures:
        for y,x,v in cr: clear.add((y,x))
    for cr in creatures:
        g,_,_=grid_of(cr)
        # try every dihedral transform; keep those where:
        #  (a) the transformed pupil (9s) matches an unused marker's 9-shape exactly,
        #  (b) each colored marker faces its band as seen from the destination (marker centroid).
        valid=[]
        for k,f,vg in variants(g):
            vp=pupil_pts(vg)
            vpn=normset(vp)
            for m in markers:
                if id(m) in used: continue
                mpts=[(y,x) for y,x,v in m]
                if normset(mpts)!=vpn: continue
                pr=sum(y for y,x in mpts)/len(mpts)
                pc=sum(x for y,x in mpts)/len(mpts)
                bdir=band_dirs_at(bp,pr,pc)
                md=marker_dirs(vg)
                if all(col in bdir and (d & bdir[col]) for col,d in md.items()):
                    valid.append((f,k,vg,m,vp,mpts))
        if not valid: continue
        # tie-break: prefer a pure rotation (f=0) over a reflection (f=1)
        valid.sort(key=lambda t:(t[0],t[1]))
        f,k,vg,m,vp,mpts=valid[0]
        chosen=(k,f,vg,m,vp,mpts)
        k,f,vg,m,vp,mpts=chosen
        used.add(id(m))
        mr0=min(r for r,c in mpts);mc0=min(c for r,c in mpts)
        vpr0=min(r for r,c in vp);vpc0=min(c for r,c in vp)
        dr=mr0-vpr0;dc=mc0-vpc0
        for y,x,v in m: clear.add((y,x))
        for r in range(len(vg)):
            for c in range(len(vg[0])):
                v=vg[r][c]
                if v=='.': continue
                place[(r+dr,c+dc)]=v
    return (place, clear, bg, rowband, colband)

def apply_T(input_grid, T):
    place, clear, bg, rowband, colband = T
    out=[row[:] for row in input_grid]
    H=len(out);W=len(out[0])
    for (r,c) in clear:
        if r in rowband: out[r][c]=rowband[r]
        elif c in colband: out[r][c]=colband[c]
        else: out[r][c]=bg
    for (r,c),v in place.items():
        if 0<=r<H and 0<=c<W:
            out[r][c]=v
    return out

def solve(input_grid):
    T=infer_T(input_grid)
    return apply_T(input_grid,T)
