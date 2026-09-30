#!/usr/bin/env python3
"""
Draws the before/after figures of the paper's algorithms (TikZ) from real solver states.

state.json comes from dump.cpp, which runs FastBandSolver on a puzzle, traces one band update step by step (checking the
trace against the real call), propagates the root and makes the first branch. `make figs` in the repo root runs both.
"""
import json
import sys

REMOVED = {'band': 'red', 'single': 'orange!90!black', 'stack': 'violet!80!magenta', 'any': 'red'}


def bits(x):
    return [k for k in range(9) if x >> k & 1]


def solved(state, cell):
    return not state['unsolved'][cell] and bin(state['cands'][cell]).count('1') == 1


def cell_marks(x0, y0, size, before, after, cell, only_digit=None, removed_color='red', show='before', focus=None):
    """TikZ for one cell's content. show='before': marks of before, removed ones coloured. show='after': marks of after."""
    out = []
    st = before if show == 'before' else after
    m = st['cands'][cell]
    gone = before['cands'][cell] & ~after['cands'][cell]
    digits = bits(m)
    if only_digit is not None:
        digits = [k for k in digits if k == only_digit]
    if only_digit is None and solved(st, cell):
        k = digits[0]
        newly = show == 'after' and not solved(before, cell)
        colour = 'blue' if newly else 'black'
        out.append(f'\\node[font=\\normalsize{"\\bfseries" if newly else ""},text={colour}] at ({x0 + size / 2:.3f},{y0 + size / 2:.3f}) {{{k + 1}}};')
        return out
    for k in digits:
        cx = x0 + size * (0.2 + 0.3 * (k % 3))
        cy = y0 + size * (0.8 - 0.3 * (k // 3))
        colour = 'black'
        if show == 'before' and gone >> k & 1:
            colour = removed_color
        elif focus is not None and k == focus:
            colour = 'blue'
        weight = '\\bfseries' if (show == 'before' and gone >> k & 1) or (focus is not None and k == focus) else ''
        out.append(f'\\node[font=\\tiny{weight},text={colour},inner sep=0] at ({cx:.3f},{cy:.3f}) {{{k + 1}}};')
        if show == 'before' and gone >> k & 1:
            out.append(f'\\draw[{colour},thin] ({cx - 0.07:.3f},{cy - 0.07:.3f}) -- ({cx + 0.07:.3f},{cy + 0.07:.3f});')
    return out


def grid(before, after, rows, cols, size, show, title, only_digit=None, removed_color=None, highlight=None, focus=None,
         labels=True, scores=None):
    """a block of the grid (rows x cols) as a TikZ picture"""
    removed_color = removed_color or {}
    out = [f'\\begin{{tikzpicture}}[x=1cm,y=1cm]']
    nr, nc = len(rows), len(cols)
    out.append(f'\\node[anchor=south west,font=\\small] at (0,{nr * size + (0.35 if labels else 0.05):.3f}) {{{title}}};')
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            x0, y0 = j * size, (nr - 1 - i) * size
            cell = r * 9 + c
            if highlight and cell in highlight:
                out.append(f'\\fill[{highlight[cell]}] ({x0:.3f},{y0:.3f}) rectangle ({x0 + size:.3f},{y0 + size:.3f});')
            colour = removed_color.get(cell, 'red') if isinstance(removed_color, dict) else removed_color
            gone = before['cands'][cell] & ~after['cands'][cell]
            if only_digit is not None:
                gone &= 1 << only_digit
            if show == 'before' and gone:
                # shade cells that lose a candidate, so the colour of the step shows at a glance
                out.append(f'\\fill[{colour}!18] ({x0:.3f},{y0:.3f}) rectangle ({x0 + size:.3f},{y0 + size:.3f});')
            out += cell_marks(x0, y0, size, before, after, cell, only_digit, colour, show, focus)
            if scores and cell in scores:
                out.append(f'\\node[font=\\tiny\\bfseries,text=teal,fill=white,anchor=north east,inner sep=0.6pt] at ({x0 + size:.3f},{y0 + size:.3f}) {{{scores[cell]}}};')
    out.append(f'\\draw[step={size},gray!50,very thin] (0,0) grid ({nc * size:.3f},{nr * size:.3f});')
    for j, c in enumerate(cols):
        if c % 3 == 0 and j > 0:
            out.append(f'\\draw[thick] ({j * size:.3f},0) -- ({j * size:.3f},{nr * size:.3f});')
    for i, r in enumerate(rows):
        if r % 3 == 0 and i > 0:
            y = (nr - i) * size
            out.append(f'\\draw[thick] (0,{y:.3f}) -- ({nc * size:.3f},{y:.3f});')
    out.append(f'\\draw[thick] (0,0) rectangle ({nc * size:.3f},{nr * size:.3f});')
    if labels:
        for j, c in enumerate(cols):
            out.append(f'\\node[font=\\tiny,text=gray] at ({j * size + size / 2:.3f},{nr * size + 0.15:.3f}) {{{c}}};')
        for i, r in enumerate(rows):
            out.append(f'\\node[font=\\tiny,text=gray,anchor=east] at (-0.05,{(nr - 1 - i) * size + size / 2:.3f}) {{{r}}};')
    out.append('\\end{tikzpicture}')
    return '\n'.join(out)


def removal_colours(steps):
    """cell -> colour of the step that removed something there (first step wins)"""
    col = {}
    for a, b, colour in steps:
        for cell in range(81):
            if a['cands'][cell] & ~b['cands'][cell] and cell not in col:
                col[cell] = colour
    return col


def fig_update_band(j):
    d, b = j['digit'], j['band']
    s0, s1, s2, s3 = j['ub_before'], j['ub_after_bandrule'], j['ub_after_rowsingles'], j['ub_after']
    rows0 = list(range(3 * b, 3 * b + 3))
    colours = removal_colours([(s0, s1, REMOVED['band']), (s1, s2, REMOVED['single']), (s2, s3, REMOVED['stack'])])
    other = [k for k in range(3) if k != b]
    changed = [k for k in other if s2['cells'][d * 3 + k] != s3['cells'][d * 3 + k]]
    ob = changed[0] if changed else other[0]
    rows1 = list(range(3 * ob, 3 * ob + 3))
    size = 0.78
    i = d * 3 + b
    placed = [c for c in range(81) if s0['unsolved'][c] and not s3['unsolved'][c]]
    hl = {c: 'blue!10' for c in placed}
    tex = []
    tex.append('\\begin{figure}[p]\n\\centering')
    tex.append(grid(s0, s3, rows0, range(9), size, 'before', f'(a) band {b}, before: all candidates', removed_color=colours, focus=d))
    tex.append('\\hspace{0.6cm}')
    tex.append(grid(s0, s3, rows0, range(9), size, 'after', f'(b) band {b}, after', highlight=hl, focus=d))
    tex.append('\\\\[0.5cm]')
    tex.append(grid(s0, s3, rows1, range(9), size, 'before', f'(c) digit {d + 1} in band {ob}, before', only_digit=d, removed_color=colours))
    tex.append('\\hspace{0.6cm}')
    tex.append(grid(s0, s3, rows1, range(9), size, 'after', f'(d) digit {d + 1} in band {ob}, after', only_digit=d))
    tex.append('\\\\[0.5cm]')

    def octal(x):
        s = f'{x:09o}'
        return f'\\texttt{{{s[:3]}\\,{s[3:6]}\\,{s[6:]}}}$_8$'

    def rowbits(x):
        s = ''.join(str(x >> k & 1) for k in range(8, -1, -1))
        return f'\\texttt{{{s[:3]}\\,{s[3:6]}\\,{s[6:]}}}'
    un_before = sum(s0['unsolved'][b * 27 + k] << k for k in range(27))
    un_after = sum(s3['unsolved'][b * 27 + k] << k for k in range(27))
    tex.append('{\\small (e) bookkeeping for digit %d, band %d\\\\[2pt]' % (d + 1, b))
    tex.append('\\begin{tabular}{lll}\\toprule field & before & after \\\\ \\midrule')
    tex.append(f'\\texttt{{cells}}$[{d}\\cdot 3+{b}]$ (digit {d + 1}, band {b}) & {octal(s0["cells"][i])} & {octal(s3["cells"][i])} \\\\')
    tex.append(f'\\texttt{{checked}}$[{d}\\cdot 3+{b}]$ & {octal(s0["checked"][i])} & {octal(s3["checked"][i])} \\\\')
    tex.append(f'\\texttt{{openRows}}$[{d}]$ (rows 8\\ldots 0) & {rowbits(s0["openRows"][d])} & {rowbits(s3["openRows"][d])} \\\\')
    tex.append(f'\\texttt{{unsolved}}$[{b}]$ & {octal(un_before)} & {octal(un_after)} \\\\')
    tex.append('\\bottomrule\\end{tabular}}')
    rm_band = [(c // 9, c % 9) for c in range(81) if (s0['cands'][c] & ~s1['cands'][c])]
    rm_single = [(c // 9, c % 9, bits(s1['cands'][c] & ~s2['cands'][c])) for c in range(81) if (s1['cands'][c] & ~s2['cands'][c])]
    rm_stack = [(c // 9, c % 9) for c in range(81) if (s2['cands'][c] & ~s3['cands'][c])]
    pr, pcol = placed[0] // 9, placed[0] % 9
    cap = (f'\\caption{{\\textsc{{UpdateBand}} (\\cref{{alg:band}}) on digit {d + 1} in band {b}, taken from a real run on '
           f'magictour puzzle {j["index"] + 1}. Small digits are candidates, large digits are solved cells, and digit '
           f'{d + 1} is blue. Struck-out candidates are the ones this call removes, coloured by the step that removes them: '
           f'\\textcolor{{red}}{{red}} by the band rule (line 3), \\textcolor{{orange!90!black}}{{orange}} by the row-single '
           f'placement (lines 10--16), \\textcolor{{violet!80!magenta}}{{violet}} by the stack rule (line 7); cells that lose a candidate are shaded in the same colour. The band rule removes '
           f'{d + 1} from row {rm_band[0][0]} at columns {", ".join(str(c) for _, c in rm_band)}, which leaves column {pcol} '
           f'as the only place for {d + 1} in row {pr}; so the row-single step places it there, shaded blue in (b), and '
           f'removes {" and ".join(str(k + 1) for k in rm_single[0][2])} from that cell. Because band {b}\'s set of columns '
           f'for {d + 1} changed, the stack rule runs and removes {d + 1} from {len(rm_stack)} cells of band {ob}, (c) and '
           f'(d); these are in band {ob}, so they appear only in (c). In (e), the mask shrinks, \\texttt{{checked}} records the band-rule result, row {pr} leaves '
           f'\\texttt{{openRows}}, and the placed cell leaves \\texttt{{unsolved}} (its bit {pr * 9 + pcol}).}}')
    tex.append(cap)
    tex.append('\\label{fig:alg-band}\n\\end{figure}')
    return '\n'.join(tex)


def stack_matrix(state, d, s):
    m = []
    for band in range(3):
        mask = state['cells'][d * 3 + band]
        cols = (mask | mask >> 9 | mask >> 18) & 0o777
        m.append([(cols >> (3 * s + jj)) & 1 for jj in range(3)])
    return m


def support(m):
    from itertools import permutations
    sup = [[0] * 3 for _ in range(3)]
    for p in permutations(range(3)):
        if all(m[i][p[i]] for i in range(3)):
            for i in range(3):
                sup[i][p[i]] = 1
    return sup


def fig_stack(j):
    d = j['digit']
    s2, s3 = j['ub_after_rowsingles'], j['ub_after']
    size = 0.5
    tex = ['\\begin{figure}[p]\n\\centering']
    tex.append(grid(s2, s3, range(9), range(9), size, 'before', f'(a) digit {d + 1}, before', only_digit=d, removed_color='violet!80!magenta'))
    tex.append('\\hspace{1cm}')
    tex.append(grid(s2, s3, range(9), range(9), size, 'after', f'(b) digit {d + 1}, after', only_digit=d))
    tex.append('\\\\[0.5cm]')
    cells = []
    for s in range(3):
        m = stack_matrix(s2, d, s)
        sup = support(m)
        entries = []
        for band in range(3):
            row = []
            for jj in range(3):
                if m[band][jj] and not sup[band][jj]:
                    row.append('\\textcolor{violet!80!magenta}{\\mathbf{1}}')
                elif sup[band][jj]:
                    row.append('\\mathbf{1}')
                else:
                    row.append('0')
            entries.append(' & '.join(row))
        cols = ', '.join(str(3 * s + jj) for jj in range(3))
        cells.append(f'$\\begin{{array}}{{c|ccc}} & {" & ".join(str(3 * s + jj) for jj in range(3))} \\\\ \\hline '
                     + ' \\\\ '.join(f'\\text{{band }}{band} & {entries[band]}' for band in range(3))
                     + f'\\end{{array}}$')
    tex.append('{\\small (c) the tables $B^{%d,s}$ (bands $\\times$ columns) for stacks 0, 1, 2, before}\\\\[3pt]' % (d + 1))
    tex.append('\\quad'.join(cells))
    removed = [(c // 9, c % 9) for c in range(81) if s2['cands'][c] & ~s3['cands'][c]]
    reasons = []
    for s in range(3):
        m, sup = stack_matrix(s2, d, s), support(stack_matrix(s2, d, s))
        lost = [(band, 3 * s + jj) for band in range(3) for jj in range(3) if m[band][jj] and not sup[band][jj]]
        if not lost:
            continue
        colsets = {band: [3 * s + jj for jj in range(3) if m[band][jj]] for band in range(3)}
        pair = [(x, y) for x in range(3) for y in range(x + 1, 3) if len(colsets[x]) == 2 and colsets[x] == colsets[y]]
        losers = sorted({band for band, _ in lost})
        if pair and len(losers) == 1:
            x, y = pair[0]
            z = losers[0]
            reasons.append(f'In stack {s}, bands {x} and {y} can only use columns {colsets[x][0]} and {colsets[x][1]}, so '
                           f'between them they take both, and band {z} must use the remaining column: it loses columns '
                           f'{" and ".join(str(col) for b2, col in lost)}.')
        else:
            reasons.append(f'In stack {s}, the pairs ' + ', '.join(f'(band {b2}, column {col})' for b2, col in lost)
                           + ' lie on no perfect matching and are removed.')
    unchanged = [str(s) for s in range(3) if stack_matrix(s2, d, s) == support(stack_matrix(s2, d, s))]
    tex.append(f'\\caption{{\\textsc{{StackRule}} (\\cref{{alg:stack}}) for digit {d + 1}, the call made inside the band '
               f'update of \\cref{{fig:alg-band}}. (a), (b): digit {d + 1}\'s candidates over the whole grid; the violet ones '
               f'are removed. (c): for each stack, a 1 where the band still has digit {d + 1} in that column; entries on '
               f'some perfect matching are bold, and violet entries are on none. ' + ' '.join(reasons)
               + f' That removes {d + 1} from {len(removed)} cells. In stack{"s" if len(unchanged) > 1 else ""} '
               f'{" and ".join(unchanged)} every entry is on a perfect matching, so nothing changes there.}}')
    tex.append('\\label{fig:alg-stack}\n\\end{figure}')
    return '\n'.join(tex)


def fig_propagate(j):
    a, b = j['loaded'], j['root']
    size = 0.72
    tex = ['\\begin{figure}[p]\n\\centering']
    tex.append(grid(a, b, range(9), range(9), size, 'before', '(a) after \\textsc{Load}: clues placed, nothing propagated', removed_color='red'))
    tex.append('\\\\[0.4cm]')
    tex.append(grid(a, b, range(9), range(9), size, 'after', '(b) after \\textsc{Propagate}'))
    removed = sum(bin(a['cands'][c] & ~b['cands'][c]).count('1') for c in range(81))
    newly = sum(1 for c in range(81) if solved(b, c) and not solved(a, c))
    left = sum(bin(x).count('1') for x in b['cands'])
    pair = j['pairs']
    tex.append(f'\\caption{{\\textsc{{Propagate}} (\\cref{{alg:propagate}}) at the root of magictour puzzle {j["index"] + 1} '
               f'({j["puzzle"].count(".")} empty cells). (a) The state right after \\textsc{{Load}}: clues are large, and the '
               f'{removed} red candidates are the ones propagation removes. (b) The fixed point: {newly} more cells are solved '
               f'(blue), {left} candidates remain, and only {len(pair)} cell has exactly two candidates: '
               f'row {pair[0][0] // 9}, column {pair[0][0] % 9}. That is the cell the search branches on (\\cref{{fig:alg-search}}).}}')
    tex.append('\\label{fig:alg-propagate}\n\\end{figure}')
    return '\n'.join(tex)


def fig_search(j):
    root, c1, c2 = j['root'], j['child1'], j['child2']
    cell = j['branchCell']
    r, c = divmod(cell, 9)
    size = 0.72
    peers = [x for x in range(81) if x != cell and (x // 9 == r or x % 9 == c or (x // 27 == cell // 27 and x % 9 // 3 == c // 3))]
    hl = {x: 'yellow!25' for x in peers}
    hl[cell] = 'yellow!70'
    scores = {p[0]: p[1] for p in j['pairs']}
    tex = ['\\begin{figure}[p]\n\\centering']
    tex.append(grid(root, root, range(9), range(9), size, 'after',
                    f'(a) slot $t$: the root after propagation', highlight=hl, scores=scores))
    tex.append('\\\\[0.4cm]')
    tex.append(grid(root, c1, range(9), range(9), size, 'before', f'(b) slot $t+1$: \\textsc{{Place}}({j["d1"] + 1})',
                    removed_color='red'))
    tex.append('\\hspace{0.5cm}')
    tex.append(grid(root, c2, range(9), range(9), size, 'before', f'(c) slot $t$ again: \\textsc{{Place}}({j["d2"] + 1})',
                    removed_color='red'))
    rm1 = [(x // 9, x % 9) for x in range(81) if root['cands'][x] & ~c1['cands'][x]]
    rm2 = [(x // 9, x % 9) for x in range(81) if root['cands'][x] & ~c2['cands'][x]]
    tex.append(f'\\caption{{\\textsc{{Search}} (\\cref{{alg:search}}) at the state of \\cref{{fig:alg-propagate}}(b). (a) The '
               f'two-candidate cells, with their peer scores in teal (the number of unsolved cells among the 20 peers). Here '
               f'there is only one, row {r}, column {c}, with candidates {j["d1"] + 1} and {j["d2"] + 1} and score '
               f'{scores[cell]}; its peers are shaded. (b) The first child is a copy of slot $t$ in slot $t+1$ with '
               f'{j["d1"] + 1} placed: {j["d2"] + 1} leaves the cell and {j["d1"] + 1} leaves its peers, the red candidates '
               f'({len(rm1)} cells change). It is searched completely before (c): the second child reuses slot $t$ with '
               f'{j["d2"] + 1} placed ({len(rm2)} cells change). Each child then runs \\textsc{{Propagate}} before branching again.}}')
    tex.append('\\label{fig:alg-search}\n\\end{figure}')
    return '\n'.join(tex)


def main():
    j = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    for name, fn in [('alg_band', fig_update_band), ('alg_stack', fig_stack), ('alg_propagate', fig_propagate),
                     ('alg_search', fig_search)]:
        with open(f'{outdir}/{name}.tex', 'w') as f:
            f.write('% generated by make_figs.py from a real FastBandSolver run; do not edit by hand\n')
            f.write(fn(j) + '\n')


main()
