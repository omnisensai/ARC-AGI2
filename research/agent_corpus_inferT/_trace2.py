import json
from collections import defaultdict
data = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))

# Map each ray to its source object (line) and analyze step+chirality
# train1 lines:
# lineV 5 r14-16 c8 (mid (15,8))  -> color5 path [(17,5),(16,6),(15,7)]
# lineV 5 r1-3 c9 (mid (2,9))     -> color5 path [(2,10),(1,11),(0,12)]
# lineH 4 r4 c4-6 (mid (4,5))     -> color4 path [(8,2),(7,3),(6,4),(5,5)]
# lineH 4 r13 c11-13 (mid (13,12))-> color4 path [(9,15),(10,14),(11,13),(12,12)]
# lineV 6 r8-10 c0 (mid (9,0))    -> color6 path [(14,6)...(9,1)] hmm that's far
# lineV 6 r7-9 c17 (mid (8,17))   -> color6 path [(8,16)...(3,11)]

print("train1 grid 18x18 center=8.5,8.5")
print("""
lineV5 mid(15,8) [bottom,right-of-c? c8<8.5 left]   ray ends near (15,7): start(17,5)->(15,7). first cell adjacent to mid?
   (15,7) is left of mid(15,8). step LEFT (toward center c8.5? no, left is away). Actually c8<center8.5 so center is to RIGHT. step LEFT = away.
   Hmm. ray: (15,7),(16,6),(17,5) going down-left from (15,7).
""")
# Let me just print for each: midpoint, the ray cell closest to mid, the step dir, then diagonal dir
def analyze(midr,midc,path,H,W,label):
    cr,cc=(H-1)/2,(W-1)/2
    # find ray endpoint closest to mid
    near=min(path,key=lambda p:abs(p[0]-midr)+abs(p[1]-midc))
    far=max(path,key=lambda p:abs(p[0]-midr)+abs(p[1]-midc))
    stepr=near[0]-midr; stepc=near[1]-midc
    print(f"{label}: mid({midr},{midc}) centerdir=({'D' if cr>midr else 'U'},{'R' if cc>midc else 'L'}) nearcell={near} step=({stepr},{stepc}) far={far}")
    # diagonal dir from near to next
    if len(path)>=2:
        # path ordered; figure direction from near
        idx=path.index(near)
        if idx==0: nxt=path[1]
        else: nxt=path[idx-1]
        dd=(nxt[0]-near[0],nxt[1]-near[1])
        print(f"     diag dir from near = {dd}")

H,W=18,18
analyze(15,8,[(17,5),(16,6),(15,7)],H,W,"lineV5 bottom c8")
analyze(2,9,[(2,10),(1,11),(0,12)],H,W,"lineV5 top c9")
analyze(4,5,[(8,2),(7,3),(6,4),(5,5)],H,W,"lineH4 top r4")
analyze(13,12,[(9,15),(10,14),(11,13),(12,12)],H,W,"lineH4 bottom r13")
analyze(9,0,[(14,6),(13,5),(12,4),(11,3),(10,2),(9,1)],H,W,"lineV6 left c0")
analyze(8,17,[(8,16),(7,15),(6,14),(5,13),(4,12),(3,11)],H,W,"lineV6 right c17")
print()
print("train2 grid 20x20 center=9.5,9.5")
H,W=20,20
analyze(6,7,[(6,6),(7,5),(8,4),(9,3)],H,W,"lineV1 c7 r5-7 mid(6,7)")
analyze(7,12,[(15,19),(14,18),(13,17),(12,16),(11,15),(10,14),(9,13),(8,12)],H,W,"lineH2 r7 c11-13 mid(7,12)")
analyze(10,1,[(13,5),(12,4),(11,3),(10,2)],H,W,"lineV7 c1 r9-11 mid(10,1)")
analyze(15,6,[(14,6),(13,7),(12,8),(11,9),(10,10),(9,11)],H,W,"lineH5 r15 c5-7 mid(15,6)")
