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

def objs(g):
    H=len(g);W=len(g[0]); byc=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: byc[g[r][c]].append((r,c))
    out=[]
    for col,cells in byc.items():
        for comp in comps(cells):
            rows=set(r for r,c in comp);cols=set(c for r,c in comp)
            if len(comp)==3 and len(rows)==1: out.append((col,'H',comp))
            elif len(comp)==3 and len(cols)==1: out.append((col,'V',comp))
            elif len(comp)==3: out.append((col,'L',comp))
            elif len(comp)==1: out.append((col,'dot',comp))
            else: out.append((col,f'sz{len(comp)}',comp))
    return out

# For train2: each line ray. Compute first cell (perp step) and diag dir.
# Then check: does the extended diagonal line (from mid through first cell direction)
# pass through / point at the midpoint of another object?
idx=2
p=pairs[idx]; g=p['input']; o=p['output']
H=len(g);W=len(g[0])
painted=defaultdict(set)
for r in range(H):
    for c in range(W):
        if g[r][c]==0 and o[r][c]!=0: painted[o[r][c]].add((r,c))
O=objs(g)
print("Objects:", [(c,k,comp) for c,k,comp in O])
for col,kind,comp in O:
    if kind not in ('H','V'): continue
    mr,mc=comp[1]; P=painted[col]
    first=[x for x in P if abs(x[0]-mr)+abs(x[1]-mc)==1][0]
    sec=[x for x in P if abs(x[0]-first[0])==1 and abs(x[1]-first[1])==1 and abs(x[0]-mr)+abs(x[1]-mc)>abs(first[0]-mr)+abs(first[1]-mc)]
    dr,dc=(sec[0][0]-first[0],sec[0][1]-first[1])
    # full path cells in P, sorted along dir
    path=sorted(P, key=lambda x:(x[0]*dr, x[1]*dc))
    print(f"col{col}{kind} mid=({mr},{mc}) step={first} dir=({dr},{dc}) endpath={sorted(P)}")
