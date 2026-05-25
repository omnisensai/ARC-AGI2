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

def objects(g):
    H=len(g); W=len(g[0])
    byc=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: byc[g[r][c]].append((r,c))
    objs=[]
    for col,cells in byc.items():
        for comp in comps(cells):
            cset=set(comp)
            if len(comp)==1: kind='dot'
            elif len(comp)==3:
                rows=set(r for r,c in comp); cols=set(c for r,c in comp)
                if len(rows)==1: kind='Hline'
                elif len(cols)==1: kind='Vline'
                else: kind='Lcorner'
            elif len(comp)==2: kind='domino'
            else: kind=f'sz{len(comp)}'
            objs.append((col,kind,comp))
    return objs

for idx,p in enumerate(pairs):
    g=p['input']; o=p['output']
    H=len(g); W=len(g[0])
    print(f"=== {names[idx]} ({H}x{W}) ===")
    for col,kind,comp in objects(g):
        print(f"  color={col} {kind} cells={comp}")
    print()
