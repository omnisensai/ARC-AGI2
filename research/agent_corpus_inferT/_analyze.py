import json
from collections import defaultdict

data = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))

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

def classify(g):
    H=len(g);W=len(g[0])
    by=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: by[g[r][c]].append((r,c))
    objs=[]
    for col,cells in by.items():
        for comp in comps(cells):
            cset=set(comp)
            if len(comp)==1:
                objs.append(('dot',col,comp))
            elif len(comp)==3:
                corner=None
                for (r,c) in comp:
                    h=(r,c-1) in cset or (r,c+1) in cset
                    v=(r-1,c) in cset or (r+1,c) in cset
                    if h and v: corner=(r,c)
                if corner is not None:
                    objs.append(('L',col,comp,corner))
                else:
                    rows=set(r for r,c in comp)
                    orient='H' if len(rows)==1 else 'V'
                    objs.append(('line'+orient,col,comp))
            else:
                objs.append(('other',col,comp))
    return objs,H,W

def diff(inp,out):
    H=len(inp);W=len(inp[0])
    added=[]
    for r in range(H):
        for c in range(W):
            if inp[r][c]!=out[r][c]:
                added.append((r,c,out[r][c]))
    return added

for name,pairs in [('train',data['train']),('test',data['test'])]:
    for i,p in enumerate(pairs):
        inp=p['input'];out=p['output']
        objs,H,W=classify(inp)
        print(f"\n===== {name}{i}  grid {H}x{W} center=({(H-1)/2},{(W-1)/2}) =====")
        for o in objs:
            print("  OBJ",o)
        added=diff(inp,out)
        # group added by color
        bycol=defaultdict(list)
        for r,c,v in added: bycol[v].append((r,c))
        for col in sorted(bycol):
            print(f"  ADDED color {col}: {sorted(bycol[col])}")
