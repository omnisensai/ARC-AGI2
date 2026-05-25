import json
from collections import defaultdict
D = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))
pairs = D['train'] + D['test']
names = ['train0','train1','train2','test0','test1']

# For each color's painted cells in train1, reconstruct ray as ordered path
def ordered_path(painted_set, start):
    # greedily build a diagonal-with-bends path from start
    pass

# Just print, per color, the painted cells sorted by row to read paths.
for idx in [1]:
    p=pairs[idx]; g=p['input']; o=p['output']
    H=len(g);W=len(g[0])
    print(names[idx])
    painted=defaultdict(list)
    for r in range(H):
        for c in range(W):
            if g[r][c]==0 and o[r][c]!=0: painted[o[r][c]].append((r,c))
    for col in sorted(painted):
        print(f" {col}: {sorted(painted[col])}")
