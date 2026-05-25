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

def get_lines(g):
    H=len(g);W=len(g[0]); byc=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: byc[g[r][c]].append((r,c))
    lines=[]
    for col,cells in byc.items():
        for comp in comps(cells):
            if len(comp)==3:
                rows=set(r for r,c in comp); cols=set(c for r,c in comp)
                if len(rows)==1: lines.append((col,'H',comp))
                elif len(cols)==1: lines.append((col,'V',comp))
    return lines

def trace_painted(idx,col,startcells):
    # given painted cells of a color (excluding the original obj), figure out
    # the step from line middle and the first diagonal
    pass

for idx in [1,2,4]:
    p=pairs[idx]; g=p['input']; o=p['output']
    H=len(g);W=len(g[0])
    print(f"=== {names[idx]} {H}x{W}  center=({(H-1)/2},{(W-1)/2}) ===")
    painted=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 and o[r][c]!=0: painted[o[r][c]].append((r,c))
    for col,kind,comp in get_lines(g):
        mid = comp[1]
        # find painted cells of this color adjacent (orthogonally, perpendicular) to middle
        pc = painted.get(col,[])
        # find the painted cell nearest to mid
        if not pc:
            print(f"  color{col} {kind} mid={mid}: NO PAINT"); continue
        # the first cell of the ray should be orthogonally adjacent to mid
        firsts=[x for x in pc if abs(x[0]-mid[0])+abs(x[1]-mid[1])==1]
        print(f"  color{col} {kind} line={comp} mid={mid} adj_first={firsts} all_painted={sorted(pc)}")
    print()
