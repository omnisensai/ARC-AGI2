# Tabulate all line emissions: orientation, mid (r,c), step vector, diagonal vector
# grid centers
rows=[]
# (gridH,gridW, orient, midr, midc, stepr,stepc, diagr,diagc, label)
def add(H,W,orient,midr,midc,near,diag,label):
    cr,cc=(H-1)/2,(W-1)/2
    sr=near[0]-midr; sc=near[1]-midc
    rows.append((orient,midr,midc,cr,cc,sr,sc,diag[0],diag[1],label))

# train1 18x18
add(18,18,'V',15,8,(15,7),(1,-1),"t1 lineV5 bottom-center c8")
add(18,18,'V',2,9,(2,10),(-1,1),"t1 lineV5 top-center c9")
add(18,18,'H',4,5,(5,5),(1,-1),"t1 lineH4 top r4")
add(18,18,'H',13,12,(12,12),(-1,1),"t1 lineH4 bottom r13")
add(18,18,'V',9,0,(9,1),(1,1),"t1 lineV6 left c0")
add(18,18,'V',8,17,(8,16),(-1,-1),"t1 lineV6 right c17")
# train2 20x20
add(20,20,'V',6,7,(6,6),(1,-1),"t2 lineV1 c7 (r5-7)")
add(20,20,'H',7,12,(8,12),(1,1),"t2 lineH2 r7 c11-13")
add(20,20,'V',10,1,(10,2),(1,1),"t2 lineV7 c1 r9-11")
add(20,20,'H',15,6,(14,6),(-1,1),"t2 lineH5 r15 c5-7")

print(f"{'label':28} orient mid    cen     step   diag  | sideR sideC(rel center)")
for orient,mr,mc,cr,cc,sr,sc,dr,dc,label in rows:
    relr = '+' if mr>cr else '-'  # below/above center
    relc = '+' if mc>cc else '-'  # right/left of center
    print(f"{label:28} {orient}   ({mr:2d},{mc:2d}) ({cr:.1f},{cc:.1f}) ({sr:+d},{sc:+d}) ({dr:+d},{dc:+d}) | rowrel={relr} colrel={relc}")
