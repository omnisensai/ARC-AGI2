import json
from collections import defaultdict
D = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))
pairs = D['train'] + D['test']
names = ['train0','train1','train2','test0','test1']

def show(idx):
    p=pairs[idx]; g=p['input']; o=p['output']
    H=len(g); W=len(g[0])
    print(f"=== {names[idx]} ===")
    # painted cells grouped by color
    bycol=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 and o[r][c]!=0:
                bycol[o[r][c]].append((r,c))
    for col in sorted(bycol):
        cells=sorted(bycol[col])
        print(f" color {col}: {cells}")
    # also print full output as grid for visual
    print(" OUTPUT:")
    for r in range(H):
        print("  "+"".join(str(o[r][c]) if o[r][c] else '.' for c in range(W)))
    print()

import sys
for i in [int(x) for x in sys.argv[1:]] or range(5):
    show(i)
