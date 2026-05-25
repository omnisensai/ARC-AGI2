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

def lines(g):
    H=len(g);W=len(g[0]); byc=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]: byc[g[r][c]].append((r,c))
    L=[]
    for col,cells in byc.items():
        for comp in comps(cells):
            if len(comp)==3:
                rows=set(r for r,c in comp);cols=set(c for r,c in comp)
                if len(rows)==1: L.append((col,'H',comp))
                elif len(cols)==1: L.append((col,'V',comp))
    return L

data=[]
for idx in [1,2,4]:
    p=pairs[idx]; g=p['input']; o=p['output']
    H=len(g);W=len(g[0]); cr=(H-1)/2; cc=(W-1)/2
    painted=defaultdict(set)
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 and o[r][c]!=0: painted[o[r][c]].add((r,c))
    for col,kind,comp in lines(g):
        mr,mc=comp[1]
        P=painted[col]
        first=[x for x in P if abs(x[0]-mr)+abs(x[1]-mc)==1]
        if not first: continue
        f=first[0]; step=(f[0]-mr,f[1]-mc)
        if kind=='V':
            stepdir=step[1] # dc
            toward_center = 1 if cc>mc else (-1 if cc<mc else 0)
            axispos = mc; axislen=W
        else:
            stepdir=step[0] # dr
            toward_center = 1 if cr>mr else (-1 if cr<mr else 0)
            axispos = mr; axislen=H
        print(f"{names[idx]} col{col}{kind} mid=({mr},{mc}) step={stepdir} towardCenter={toward_center} match={'YES' if stepdir==toward_center else 'NO'} axispos={axispos}/{axislen}")
    print()
