import json
from collections import defaultdict
D = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))
pairs = D['train'] + D['test']
names = ['train0','train1','train2','test0','test1']

def comps(cells):
    cells=set(cells); seen=set(); out=[]
    for s in cells:
        if s in seen: continue
        st=[s]; comp=[]
        while st:
            x=st.pop()
            if x in seen or x not in cells: continue
            seen.add(x); comp.append(x); r,c=x
            for dr,dc in((1,0),(-1,0),(0,1),(0,-1)): st.append((r+dr,c+dc))
        out.append(sorted(comp))
    return out

# For each painted color, reconstruct the ordered ray path(s) from the input objects.
# Lcorner: start at corner, dir away from arms (diag).
# Line: start = perpendicular step from mid, then diagonal. Need to find which diag.
# We'll reconstruct by matching painted cells.

def analyze(idx):
    p=pairs[idx]; g=p['input']; o=p['output']
    H=len(g);W=len(g[0])
    byc=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: byc[g[r][c]].append((r,c))
    painted=defaultdict(set)
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 and o[r][c]!=0: painted[o[r][c]].add((r,c))
    print(f"=== {names[idx]} {H}x{W} ===")
    for col,cells in byc.items():
        for comp in comps(cells):
            cset=set(comp)
            P=painted.get(col,set())
            if len(comp)==3:
                rows=set(r for r,c in comp); cols=set(c for r,c in comp)
                if len(rows)==1 or len(cols)==1:
                    kind='V' if len(cols)==1 else 'H'
                    mid=comp[1]
                    # find start: painted cell orthogonally adjacent to mid (perp dir)
                    starts=[x for x in P if abs(x[0]-mid[0])+abs(x[1]-mid[1])==1]
                    print(f" col{col} {kind}line mid={mid} start={starts}")
                else:
                    # Lcorner
                    corner=None
                    for (r,c) in comp:
                        h=(r,c-1) in cset or (r,c+1) in cset
                        v=(r-1,c) in cset or (r+1,c) in cset
                        if h and v: corner=(r,c)
                    up=(corner[0]-1,corner[1]) in cset
                    left=(corner[0],corner[1]-1) in cset
                    dr=1 if up else -1; dc=1 if left else -1
                    # trace from corner unobstructed
                    print(f" col{col} Lcorner corner={corner} dir=({dr},{dc})")
            elif len(comp)==1:
                print(f" col{col} dot at {comp[0]}")
            else:
                print(f" col{col} size{len(comp)} {comp}")
    print()

for i in [0,1,2,3,4]:
    analyze(i)
