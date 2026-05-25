import json
from collections import Counter

def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]
    # foreground = non-bg, non-4
    fg = None
    for v, _ in cnt.most_common():
        if v != bg and v != 4:
            fg = v
            break
    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    if not fours:
        return {}, bg
    rows = set(r for r, c in fours)
    cols = set(c for r, c in fours)
    horizontal = len(rows) == 1  # marker is a horizontal line
    T = {}  # (r,c) -> color
    if horizontal:
        mr = next(iter(rows))
        band = sorted(cols)               # the columns of the band
        scan_down = mr == 0               # if at top -> scan down, else up
        order = range(mr, H) if scan_down else range(mr, -1, -1)
        k = 0
        for r in order:
            if (r - mr) % 2 != 0 and not (r == mr):
                pass
            step = abs(r - mr)
            if step % 2 == 0:
                color = 3 if k % 3 == 2 else 4
                # set band cells to color
                for c in band:
                    T[(r, c)] = color
                if color == 3:
                    # recolor foreground cells in this whole row to 3
                    for c in range(W):
                        if input_grid[r][c] == fg:
                            T[(r, c)] = 3
                k += 1
            else:
                # non-stamp line: clear band to bg
                for c in band:
                    T[(r, c)] = bg
    else:
        mc = next(iter(cols))
        band = sorted(rows)
        scan_right = mc == 0
        order = range(mc, W) if scan_right else range(mc, -1, -1)
        k = 0
        for c in order:
            step = abs(c - mc)
            if step % 2 == 0:
                color = 3 if k % 3 == 2 else 4
                for r in band:
                    T[(r, c)] = color
                if color == 3:
                    for r in range(H):
                        if input_grid[r][c] == fg:
                            T[(r, c)] = 3
                k += 1
            else:
                for r in band:
                    T[(r, c)] = bg
    return T, bg

def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out

def solve(input_grid):
    T, bg = infer_T(input_grid)
    return apply_T(input_grid, T)

if __name__ == '__main__':
    d = json.load(open('research/agent_corpus_inferT/_tasks/221dfab4.json'))
    allp = [('train', i, p) for i, p in enumerate(d['train'])] + [('test', i, p) for i, p in enumerate(d['test'])]
    ok = True
    for split, i, p in allp:
        got = solve(p['input'])
        exp = p['output']
        if got == exp:
            print(f'{split}[{i}] PASS')
        else:
            ok = False
            diffs = [(r, c, got[r][c], exp[r][c]) for r in range(len(exp)) for c in range(len(exp[0])) if got[r][c] != exp[r][c]]
            print(f'{split}[{i}] FAIL  {len(diffs)} diffs, first: {diffs[:8]}')
    print('ALL-PASS' if ok else 'NOT ALL PASS')
