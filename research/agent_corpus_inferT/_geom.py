import json
data = json.load(open('/home/user/ARC-AGI2/research/agent_corpus_inferT/_tasks/142ca369.json'))

def show(inp,out,label):
    H=len(inp);W=len(inp[0])
    print(f"\n===== {label} ({H}x{W}) =====")
    sym="0123456789"
    for r in range(H):
        line=""
        for c in range(W):
            i=inp[r][c];o=out[r][c]
            if i!=0:
                line+=str(i)  # original object
            elif o!=0:
                line+=chr(ord('a')+o)  # added ray lowercase
            else:
                line+="."
        print(f"{r:2d} {line}")

show(data['train'][1]['input'],data['train'][1]['output'],"train1")
show(data['train'][2]['input'],data['train'][2]['output'],"train2")
