import json
from collections import defaultdict
data = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))

def order_ray(cells):
    # order a set of ray cells into a path by nearest-neighbor (diag adjacency)
    cells=set(cells)
    # find an endpoint: a cell with only one diag/orth neighbor in set
    def neigh(c):
        r,cc=c
        out=[]
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if dr==0 and dc==0:continue
                if (r+dr,cc+dc) in cells: out.append((r+dr,cc+dc))
        return out
    ends=[c for c in cells if len(neigh(c))==1]
    if not ends: ends=[min(cells)]
    start=ends[0]
    path=[start]; seen={start}; cur=start
    while True:
        nxt=[n for n in neigh(cur) if n not in seen]
        if not nxt: break
        cur=nxt[0]; path.append(cur); seen.add(cur)
    return path

print("===== train1 ray paths =====")
inp=data['train'][1]['input'];out=data['train'][1]['output']
H=len(inp);W=len(inp[0])
bycol=defaultdict(list)
for r in range(H):
    for c in range(W):
        if inp[r][c]!=out[r][c]: bycol[out[r][c]].append((r,c))
for col in sorted(bycol):
    # separate into connected ray paths (using 8-conn)
    cells=set(bycol[col])
    # 8-conn components
    seen=set();comps=[]
    for s in cells:
        if s in seen:continue
        st=[s];comp=[]
        while st:
            x=st.pop()
            if x in seen or x not in cells:continue
            seen.add(x);comp.append(x);r,c=x
            for dr in(-1,0,1):
                for dc in(-1,0,1):
                    if dr or dc: st.append((r+dr,c+dc))
        comps.append(comp)
    for comp in comps:
        print(f"  color {col} path: {order_ray(comp)}")

print("\n===== train2 ray paths =====")
inp=data['train'][2]['input'];out=data['train'][2]['output']
H=len(inp);W=len(inp[0])
bycol=defaultdict(list)
for r in range(H):
    for c in range(W):
        if inp[r][c]!=out[r][c]: bycol[out[r][c]].append((r,c))
for col in sorted(bycol):
    cells=set(bycol[col])
    seen=set();comps=[]
    for s in cells:
        if s in seen:continue
        st=[s];comp=[]
        while st:
            x=st.pop()
            if x in seen or x not in cells:continue
            seen.add(x);comp.append(x);r,c=x
            for dr in(-1,0,1):
                for dc in(-1,0,1):
                    if dr or dc: st.append((r+dr,c+dc))
        comps.append(comp)
    for comp in comps:
        print(f"  color {col} path: {order_ray(comp)}")
