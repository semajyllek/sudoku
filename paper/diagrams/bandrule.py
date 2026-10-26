#!/usr/bin/env python3
# Band rule, traced line by line through updateBand, every value drawn as its full bit string (high bit on the left,
# exactly as a C++ binary literal is written), every 0 shown, every 1 labelled with the cell it stands for.
import subprocess, os, shutil, tempfile

PERMS = [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]
M9 = 0b111_111_111

def permutation_union(m):
    t = 0
    for p in PERMS:
        e = 1 << p[0] | 1 << (3 + p[1]) | 1 << (6 + p[2])
        if m & e == e: t |= e
    return t

def boxes_of_row(r): return (1 if r & 0b111 else 0) | (2 if r & 0b111_000 else 0) | (4 if r & 0b111_000_000 else 0)

def possible(m):
    ok, t = permutation_union(m), 0
    for row in range(3):
        for b in range(3):
            if ok >> (row * 3 + b) & 1: t |= 0b111 << (row * 9 + b * 3)
    return t

# rows 0 and 1 can each only use boxes 0 and 1, so two pairings fit and row 2 is forced into box 2
CANDS = [(0, 1), (0, 4), (1, 0), (1, 5), (2, 2), (2, 3), (2, 8)]
cells = sum(1 << (9 * r + c) for r, c in CANDS)
rows = [cells & M9, (cells >> 9) & M9, cells >> 18]
bx = [boxes_of_row(r) for r in rows]
mr = bx[0] | bx[1] << 3 | bx[2] << 6
ok = permutation_union(mr)
pc = possible(mr)
after = cells & pc
assert mr == 0b111_011_011 and ok == 0b100_011_011 and after == cells & ~(1 << 20 | 1 << 21)

ROWC = ['blue!25', 'orange!35', 'teal!30']      # fill of a 1 by the row it came from
BOXC = ['red!7', 'yellow!18', 'violet!8']       # faint background by box
W, G3, G9 = 0.52, 0.14, 0.42                    # box width, gap every 3 bits, gap every 9 bits

L = []
w = L.append

def lit(x, n):
    """C++ literal, groups of 3 separated by '."""
    s = format(x, f'0{n}b')
    return '0b' + r'\textquotesingle{}'.join(s[k:k + 3] for k in range(0, n, 3))

def xpos(X, i):  # i = position from the left (0 = high bit)
    return X + i * W + (i // 3) * G3 + (i // 9) * G9

def strip(X, Y, val, n, labels=None, fills=None, top=True, red=0, green=0, newzero=0, boxbg=None, bold=None, all_labels=False):
    """n bits of val, high bit on the left. labels[bit] under each box; fills[bit] colour of a 1.
    red: bits drawn as a removed 1 (red, struck). green: 1s drawn as kept-by-the-rule. newzero: 0s that a shift
    brought in (hatched)."""
    for i in range(n):
        bit = n - 1 - i
        x = xpos(X, i)
        bg = boxbg(bit) if boxbg else 'white'
        w(rf"\fill[{bg}] ({x:.3f},{Y}) rectangle ++({W},{W});")
        if newzero >> bit & 1:
            w(rf"\fill[pattern=north east lines,pattern color=gray!45] ({x:.3f},{Y}) rectangle ++({W},{W});")
        if red >> bit & 1:
            w(rf"\fill[red!22] ({x:.3f},{Y}) rectangle ++({W},{W});")
            w(rf"\node[font=\footnotesize\bfseries,text=red!75!black] at ({x + W / 2:.3f},{Y + W / 2}) {{0}};")
        elif val >> bit & 1:
            f = 'green!40' if green >> bit & 1 else (fills(bit) if fills else 'blue!25')
            w(rf"\fill[{f}] ({x:.3f},{Y}) rectangle ++({W},{W});")
            w(rf"\node[font=\footnotesize\bfseries] at ({x + W / 2:.3f},{Y + W / 2}) {{1}};")
        else:
            w(rf"\node[font=\footnotesize,text=gray!75] at ({x + W / 2:.3f},{Y + W / 2}) {{0}};")
        w(rf"\draw[gray!55] ({x:.3f},{Y}) rectangle ++({W},{W});")
        if top:
            w(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont,text=gray] at ({x + W / 2:.3f},{Y + W + 0.13}) {{{bit}}};")
        if labels:
            lab = labels(bit)
            if lab and (all_labels or (val | red) >> bit & 1):
                w(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont,text=black!70] at ({x + W / 2:.3f},{Y - 0.13}) {{{lab}}};")

def strip_end(X, n): return xpos(X, n - 1) + W

def cell_label(bit): return f"r{bit // 9}c{bit % 9}"
def cell_bg(bit): return BOXC[(bit % 9) // 3]
def cell_fill(bit): return ROWC[bit // 9]

def lab(X, Y, text, anchor='east', font=r'\footnotesize'):
    w(rf"\node[font={font},anchor={anchor}] at ({X},{Y}) {{{text}}};")

def title(Y, t):
    w(rf"\node[font=\bfseries\large,anchor=west] at (-0.5,{Y}) {{{t}}};")
    w(rf"\draw[gray!40] (-0.5,{Y - 0.35}) -- (31,{Y - 0.35});")

def note(X, Y, t, width=None):
    wd = f",text width={width}cm" if width else ""
    w(rf"\node[font=\footnotesize,anchor=north west,align=left{wd}] at ({X},{Y}) {{{t}}};")

w(r"""\documentclass[border=12pt]{standalone}
\usepackage{tikz}\usetikzlibrary{patterns,decorations.pathreplacing}\usepackage{amsmath}
\usepackage{textcomp}
\begin{document}
\begin{tikzpicture}
""")

# ---------------------------------------------------------------- 0. the board
Y = 2.9
title(Y, r"The band rule, line by line: the value 5 in band 0. \ Every value is drawn as its full bit string, high bit on the left, as in C++")
w(r"""\node[draw=blue!50!black,fill=blue!4,rounded corners=3pt,inner sep=7pt,anchor=north west,align=left,text width=29.2cm,font=\normalsize] at (-0.5,2.2) {
\textbf{What the band rule is for.} A band is three rows and three boxes, and each value must appear exactly once in every row and exactly once in every box.
So within a band, the value's three rows must be paired one-to-one with its three boxes: each row gets the box its value will sit in, and no two rows get the same box.
\textbf{The rule removes every candidate that could not be part of any such pairing}, because filling it in would leave some other row or box with nowhere for the value.
If no pairing is possible at all, the puzzle cannot be finished from here, and the solver backtracks.
Below, this is done for one value in one band with a few table lookups and one AND on a single 27-bit integer.};""")
GX, GY, CS = 0.8, -3.0, 0.62
for r in range(3):
    for c in range(9):
        x, y = GX + c * CS, GY + (2 - r) * CS
        w(rf"\fill[{BOXC[c // 3]}] ({x},{y}) rectangle ++({CS},{CS});")
        w(rf"\node[font=\fontsize{{5}}{{6}}\selectfont,text=gray] at ({x + CS - 0.14},{y + CS - 0.12}) {{{9 * r + c}}};")
        if (r, c) in CANDS:
            w(rf"\node[font=\small\bfseries] at ({x + CS / 2 - 0.05},{y + CS / 2 - 0.05}) {{5}};")
w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={CS}] (0,0) grid ({9 * CS},{3 * CS});\end{{scope}}")
w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * CS},{3 * CS});")
for q in (3, 6): w(rf"\draw[thick] ({GX + q * CS},{GY}) -- ++(0,{3 * CS});")
for c in range(9): lab(GX + c * CS + CS / 2, GY + 3 * CS + 0.2, f"c{c}", 'center', r'\scriptsize')
for b in range(3): lab(GX + (3 * b + 1.5) * CS, GY + 3 * CS + 0.6, f"box {b}", 'center', r'\scriptsize')
for r in range(3): lab(GX - 0.08, GY + (2.5 - r) * CS, f"r{r}", 'east', r'\scriptsize')
note(GX + 9 * CS + 0.6, GY + 3 * CS + 0.75,
     r"Band 0 is rows 0--2 of the grid. The value 5 can still go in the 7 cells marked 5.\\"
     r"Small gray number = the cell's bit in \texttt{bandCells}: \ bit $= 9\times\text{row} + \text{column}$.\\"
     r"So row 0 is bits 0--8, row 1 is bits 9--17, row 2 is bits 18--26, and bits 27--31 of the \texttt{uint32\_t} are always 0.\\[3pt]"
     r"\textbf{How to read the strips below.} Each box is one bit. The tiny gray number above it is the bit's position;\\"
     r"bit 26 (or bit 8) is on the \emph{left} and bit 0 on the right, exactly the order you type a C++ binary literal.\\"
     r"Small gaps separate groups of 3 bits (one triad), wider gaps separate groups of 9 (one row).\\"
     r"A 1 is bold and coloured by the row it belongs to: \colorbox{blue!25}{row 0}\ \colorbox{orange!35}{row 1}\ \colorbox{teal!30}{row 2}. A 0 is gray. Every 0 is drawn.\\"
     r"The label under a 1 says which cell it is: r1c2 = row 1, column 2. The faint background marks the box: \colorbox{red!7}{box 0}\ \colorbox{yellow!18}{box 1}\ \colorbox{violet!8}{box 2}.",
     19.5)

# ---------------------------------------------------------------- 1. load
Y = -4.6
title(Y, r"1. \ \texttt{Mask bandCells = state.valueToBand[value - 1][band];} \quad the value 5 in band 0: \texttt{state.valueToBand[5 - 1][0]} (arrays count from 0)")
X = 8.2
SY = Y - 1.6
strip(X, SY, cells, 27, labels=lambda b: cell_label(b) if cells >> b & 1 else '', fills=cell_fill, boxbg=cell_bg)
lab(X - 0.25, SY + W / 2, r"\texttt{bandCells}")
for k, t in enumerate(["row 2 \\ (bits 26--18)", "row 1 \\ (bits 17--9)", "row 0 \\ (bits 8--0)"]):
    x0, x1 = xpos(X, 9 * k), xpos(X, 9 * k + 8) + W
    w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({x0},{SY + W + 0.3}) -- ({x1},{SY + W + 0.3}) node[midway,above=2pt,font=\scriptsize] {{{t}}};")
note(X, SY - 0.35, rf"$= \texttt{{{lit(cells, 27)}}} = {cells}$. \ Columns inside each row also run high to low: c8 c7 \ldots\ c0. The 1s at r0c1, r0c4 are bits 1 and 4; r1c0, r1c5 are bits 9, 14; r2c2, r2c3, r2c8 are bits 20, 21, 26.", 22)

# ---------------------------------------------------------------- 2. split rows
Y = -9.2
title(Y, r"2. \ Split into three 9-bit rows: \ \texttt{bandCells \& 0b111\textquotesingle{}111\textquotesingle{}111}, \ \texttt{(bandCells >> 9) \& 0b111\textquotesingle{}111\textquotesingle{}111}, \ \texttt{bandCells >> 18}")
X = 8.2
mask_lab = lambda b: ''
def shifted_labels(sh):
    return lambda b: cell_label(b + sh) if (cells >> (b + sh)) & 1 and b + sh < 27 else ''
def shifted_fill(sh): return lambda b: cell_fill(b + sh)
nz = lambda sh: ((1 << sh) - 1) << (27 - sh) if sh else 0
yy = Y - 1.3
blocks = [
    (0, r"\texttt{bandCells}", r"row 0 is already in bits 0--8, so no shift is needed"),
    (9, r"\texttt{bandCells >> 9}", r"every bit moves 9 places right: row 1 lands in bits 0--8, row 2 in bits 9--17; row 0 falls off the end. The hatched 0s are new zeros that came in on the left"),
    (18, r"\texttt{bandCells >> 18}", r"row 2 lands in bits 0--8; rows 0 and 1 fall off; bits 9--26 are all new zeros"),
]
for k, (sh, name, why) in enumerate(blocks):
    v = cells >> sh
    strip(X, yy, v, 27, labels=shifted_labels(sh), fills=shifted_fill(sh), newzero=nz(sh), boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, name)
    if sh < 18:
        strip(X, yy - 0.75, M9, 27, top=False, fills=lambda b: 'gray!30')
        lab(X - 0.25, yy - 0.75 + W / 2, r"\texttt{\& 0b111\textquotesingle{}111\textquotesingle{}111}")
        res = v & M9
        strip(X, yy - 1.75, res, 27, labels=shifted_labels(sh), fills=shifted_fill(sh), top=False, boxbg=cell_bg)
        w(rf"\draw[thick] ({X - 2.6},{yy - 1.0}) -- ({strip_end(X, 27)},{yy - 1.0});")
        lab(X - 0.25, yy - 1.75 + W / 2, rf"\texttt{{= row {sh // 9}}}")
        note(strip_end(X, 27) + 0.3, yy + 0.55, why + rf".\\ The mask is 9 ones in bits 0--8 (511): it keeps bits 0--8 and clears 9--26.", 6.8)
        lab(strip_end(X, 27) + 0.3, yy - 1.75 + W / 2, rf"$= \texttt{{{lit(res, 9)}}} = {res}$", 'west')
        yy -= 3.25
    else:
        note(strip_end(X, 27) + 0.3, yy + 0.55, why + r". No mask needed: there is nothing above bit 8 any more.\\[2pt]" + rf"$= \texttt{{{lit(v, 9)}}} = {v}$ \ (row 2)", 6.8)
        yy -= 2.0

# ---------------------------------------------------------------- 3. BOXES_OF_ROW
Y = yy - 0.6
title(Y, r"3. \ \texttt{BOXES\_OF\_ROW[row]}: \ for each box, is any of its 3 cells a 1? \ (one table load per row; the table holds this for all 512 rows)")
RX = [2.6, 13.0, 23.4]
tests = [(2, 0b111_000_000, r"0b111\textquotesingle{}000\textquotesingle{}000"), (1, 0b111_000, r"0b000\textquotesingle{}111\textquotesingle{}000"), (0, 0b111, r"0b000\textquotesingle{}000\textquotesingle{}111")]
for r in range(3):
    X = RX[r] + 2.4
    yy = Y - 1.4
    row = rows[r]
    strip(X, yy, row, 9, labels=lambda b: f"c{b}", fills=lambda b, r=r: ROWC[r], boxbg=lambda b: BOXC[b // 3], all_labels=True)
    lab(X - 0.2, yy + W / 2, rf"\texttt{{row {r}}}", font=r'\scriptsize')
    yy -= 0.95
    for box, m, ml in tests:
        v = row & m
        strip(X, yy, v, 9, fills=lambda b, r=r: ROWC[r], top=False, boxbg=lambda b, box=box: BOXC[box] if b // 3 == box else 'white')
        lab(X - 0.2, yy + W / 2, rf"\texttt{{row {r} \& {ml}}}", font=r'\scriptsize')
        res = 1 if v else 0
        lab(strip_end(X, 9) + 0.15, yy + W / 2, (rf"$\neq 0 \Rightarrow$ \texttt{{\textbf{{{lit(1 << box, 3)}}}}}" if res else rf"$= 0 \Rightarrow$ \texttt{{0b000}}"), 'west', r'\scriptsize')
        yy -= 0.72
    yy -= 0.2
    strip(X + 3 * W + G3, yy, bx[r], 3, labels=lambda b: f"b{b}", fills=lambda b, r=r: ROWC[r], boxbg=lambda b: BOXC[b], all_labels=True)
    lab(X + 3 * W + G3 - 0.2, yy + W / 2, rf"\texttt{{BOXES\_OF\_ROW[{lit(row, 9)}]}} =", font=r'\scriptsize')
    lab(strip_end(X + 3 * W + G3, 3) + 0.15, yy + W / 2, rf"$= \texttt{{{lit(bx[r], 3)}}} = {bx[r]}$", 'west', r'\scriptsize')
note(0.2, yy - 0.55,
     r"Built at compile time by this loop, exactly the three tests above, each giving its box's bit or 0, ORed together:\\ \texttt{t[r] = (r \& 0b000\textquotesingle{}000\textquotesingle{}111 ? 0b001 : 0) | (r \& 0b000\textquotesingle{}111\textquotesingle{}000 ? 0b010 : 0) | (r \& 0b111\textquotesingle{}000\textquotesingle{}000 ? 0b100 : 0);}", 30)

# ---------------------------------------------------------------- 4. triads
Y = yy - 2.0
title(Y, r"4. \ \texttt{int boxCandidates = b0 | b1 << 3 | b2 << 6;} \quad stack the three 3-bit box sets into one 9-bit table $A$")
X = 8.2
yy = Y - 1.3
mr_lab = lambda b: f"r{b // 3}b{b % 3}"
mr_fill = lambda b: ROWC[b // 3]
mr_bg = lambda b: BOXC[b % 3]
parts = [(bx[0], 0, r"\texttt{BOXES\_OF\_ROW[row 0]}"), (bx[1] << 3, 1, r"\texttt{BOXES\_OF\_ROW[row 1] << 3}"), (bx[2] << 6, 2, r"\texttt{BOXES\_OF\_ROW[row 2] << 6}")]
for k, (v, r, name) in enumerate(parts):
    strip(X, yy, v, 9, labels=lambda b, v=v: mr_lab(b) if v >> b & 1 else '', fills=mr_fill, boxbg=mr_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, name)
    lab(strip_end(X, 9) + 0.2, yy + W / 2, rf"$\texttt{{{lit(v, 9)}}}$ \ row {r}'s boxes moved to bits {3 * r}--{3 * r + 2}", 'west', r'\scriptsize')
    yy -= 0.8
w(rf"\draw[thick] ({X - 4.4},{yy + 0.62}) -- ({strip_end(X, 9)},{yy + 0.62});")
strip(X, yy - 0.05, mr, 9, labels=lambda b: mr_lab(b) if mr >> b & 1 else '', fills=mr_fill, boxbg=mr_bg, top=False)
lab(X - 0.25, yy - 0.05 + W / 2, r"OR: \texttt{boxCandidates}")
lab(strip_end(X, 9) + 0.2, yy - 0.05 + W / 2, rf"$= \texttt{{{lit(mr, 9)}}} = {mr}$", 'west')
# matrix view
MX, MY, MS = 24.0, Y - 3.35, 0.6
w(rf"\node[font=\footnotesize\bfseries] at ({MX + 1.5 * MS},{MY + 3 * MS + 0.75}) {{the same 9 bits as a table $A$}};")
for r in range(3):
    for b in range(3):
        x, y = MX + (2 - b) * MS, MY + r * MS  # row 2 on top, box 2 on the left: the strip's order
        bit = 3 * r + b
        w(rf"\fill[{ROWC[r] if mr >> bit & 1 else 'white'}] ({x},{y}) rectangle ++({MS},{MS});")
        w(rf"\node[font=\footnotesize{'\\bfseries' if mr >> bit & 1 else ''},text={'black' if mr >> bit & 1 else 'gray!75'}] at ({x + MS / 2},{y + MS / 2}) {{{mr >> bit & 1}}};")
        w(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont,text=gray] at ({x + MS - 0.1},{y + MS - 0.09}) {{{bit}}};")
    lab(MX - 0.08, MY + (r + 0.5) * MS, f"row {r}", 'east', r'\scriptsize')
for b in range(3): lab(MX + (2.5 - b) * MS, MY + 3 * MS + 0.2, f"b{b}", 'center', r'\scriptsize')
w(rf"\begin{{scope}}[shift={{({MX},{MY})}}]\draw[gray!55,step={MS}] (0,0) grid ({3 * MS},{3 * MS});\end{{scope}} \draw[thick] ({MX},{MY}) rectangle ++({3 * MS},{3 * MS});")
note(MX + 3 * MS + 0.3, MY + 3 * MS + 0.2, r"entry (row $i$, box $j$) is bit $3i + j$\\(small gray number).\\[2pt]Drawn in the strip's order:\\row 2 on top, box 2 on the\\left. Read it row by row\\from the top and you get\\\texttt{111\textquotesingle{}011\textquotesingle{}011}.", 4.6)

# ---------------------------------------------------------------- 5. PERMUTATION_UNION
Y = yy - 1.55
title(Y, rf"5. \ \texttt{{PERMUTATION\_UNION[{lit(mr, 9)}]}}: \ which 1s of $A$ lie on some permutation (one 1 per row and per box)? \ Built at compile time by this loop:")
note(-0.3, Y - 0.45, r"\texttt{for (auto const \&p : perms) \{ int permutation = 1 << p[0] | 1 << (3 + p[1]) | 1 << (6 + p[2]); \ if ((candidates \& permutation) == permutation) permutationUnion[candidates] |= permutation; \}}\\ \texttt{p[i]} is the box that row $i$ gets. The table is shared with the stack rule, so its index is just \texttt{candidates} (a 3 $\times$ 3 table of which entries have candidates); here it is \texttt{boxCandidates}.", 30)
X = 8.2
yy = Y - 2.6
strip(X, yy, mr, 9, labels=lambda b: mr_lab(b) if mr >> b & 1 else '', fills=mr_fill, boxbg=mr_bg)
lab(X - 0.25, yy + W / 2, rf"\texttt{{candidates = boxCandidates = {lit(mr, 9)}}}")
lab(strip_end(X, 9) + 0.25, yy + W / 2 + 0.55, r"\texttt{permutation}: the 3 bits of this pairing", 'west', r'\scriptsize')
lab(strip_end(X, 9) + 0.25 + 6.3, yy + W / 2 + 0.55, r"\texttt{candidates \& permutation}", 'west', r'\scriptsize')
lab(strip_end(X, 9) + 0.25 + 12.2, yy + W / 2 + 0.55, r"\texttt{(candidates \& permutation) == permutation}?", 'west', r'\scriptsize')
yy -= 0.85
total = 0
for p in PERMS:
    e = 1 << p[0] | 1 << (3 + p[1]) | 1 << (6 + p[2])
    good = mr & e == e
    if good: total |= e
    desc = rf"\texttt{{p = \{{{p[0]},{p[1]},{p[2]}\}}}}: r0$\to$b{p[0]}, r1$\to$b{p[1]}, r2$\to$b{p[2]}"
    lab(X - 0.25, yy + W / 2, desc, 'east', r'\scriptsize')
    EX = strip_end(X, 9) + 0.25
    strip(EX, yy, e, 9, labels=lambda b, e=e: (mr_lab(b) if e >> b & 1 else ''), fills=lambda b, e=e: 'gray!35', top=False, boxbg=mr_bg)
    AX = EX + 6.3
    strip(AX, yy, mr & e, 9, fills=mr_fill, top=False, red=e & ~mr, boxbg=mr_bg)
    verdict = (r"\textcolor{green!50!black}{\textbf{yes}}: all 3 are 1s, so it is ORed in" if good
               else rf"\textcolor{{red!70!black}}{{no}}: $A$ has a 0 at {', '.join(mr_lab(b) for b in range(9) if (e & ~mr) >> b & 1)} (red)")
    lab(AX + 6.0, yy + W / 2, verdict, 'west', r'\scriptsize')
    yy -= 0.85
w(rf"\draw[thick] ({X - 5.2},{yy + 0.6}) -- ({strip_end(X, 9)},{yy + 0.6});")
strip(X, yy - 0.05, ok, 9, labels=lambda b: mr_lab(b) if ok >> b & 1 else '', green=ok, red=0, boxbg=mr_bg, top=False)
lab(X - 0.25, yy - 0.05 + W / 2, rf"OR of the yes rows: \texttt{{PERMUTATION\_UNION[{lit(mr, 9)}]}}")
lab(strip_end(X, 9) + 0.25, yy - 0.05 + W / 2,
    rf"$= \texttt{{{lit(ok, 9)}}} = {ok}$", 'west', r'\scriptsize')
yy -= 0.9
note(X - 5.2, yy, r"Two pairings fit, so the entry is the OR of their bits. Rows 0 and 1 can only use boxes 0 and 1, so between them they take both, and row 2 must take box 2.\\ Compare with \texttt{candidates}: a 1 is kept if it is on \emph{either} pairing, so r0b0, r0b1, r1b0, r1b1 all stay, each on one of the two. The 1s at r2b0 (bit 6) and r2b1 (bit 7) of $A$ are on \emph{neither}, so they are not in the entry: those two triads are on no permutation, and step 6 deletes every candidate in them.", 26)

# ---------------------------------------------------------------- 6. POSSIBLE_CELLS
Y = yy - 1.6
title(Y, r"6. \ \texttt{POSSIBLE\_CELLS[boxCandidates]}: \ the cells of the triads in \texttt{kept = PERMUTATION\_UNION[boxCandidates]}, each widened to its 3 cells")
note(-0.3, Y - 0.45, r"Built at compile time, for each of the 512 values of \texttt{boxCandidates}: \quad \texttt{int kept = PERMUTATION\_UNION[boxCandidates];}\\ "
     r"\texttt{for (row) for (box) if (kept >> (row * 3 + box) \& 1) possibleCells[boxCandidates] |= Mask(0b111) << (row * 9 + box * 3);}\\"
     r"So \texttt{boxCandidates} only picks the slot; which cells get \texttt{111} is decided by \texttt{kept}, not by \texttt{boxCandidates}. Below, the loop for this band's \texttt{boxCandidates}.", 30)
KX, CX = 5.6, 13.7          # the 9-bit kept strips, the 27-bit cell strips
yy = Y - 2.8
strip(KX, yy, ok, 9, labels=lambda b: mr_lab(b) if ok >> b & 1 else '', green=ok, boxbg=mr_bg)
lab(KX - 0.25, yy + W / 2, rf"\texttt{{kept = PERMUTATION\_UNION[{lit(mr, 9)}]}} $=$", font=r'\scriptsize')
lab(strip_end(KX, 9) + 0.2, yy + W / 2, rf"\texttt{{{lit(ok, 9)}}}: from step 5", 'west', r'\scriptsize')
yy -= 1.6
lab((KX + strip_end(KX, 9)) / 2 - 0.3, yy + W + 0.42, r"\texttt{kept >> (row * 3 + box)}: triad's bit lands in bit 0", 'center', r'\scriptsize')
lab(strip_end(KX, 9) + 0.6, yy + W + 0.42, r"\texttt{\& 1}", 'west', r'\scriptsize')
lab((CX + strip_end(CX, 27)) / 2, yy + W + 0.42, r"\texttt{Mask(0b111) << (row * 9 + box * 3)}: the triad's 3 cells in the band", 'center', r'\scriptsize')
first = True
for row in range(3):
    for box in range(3):
        k = row * 3 + box
        sh = ok >> k
        on = sh & 1
        strip(KX, yy, sh, 9, fills=lambda b: 'green!40', newzero=((1 << k) - 1) << (9 - k), boxbg=mr_bg, top=first)
        x0 = xpos(KX, 8)
        w(rf"\draw[very thick,{'green!50!black' if on else 'black!70'}] ({x0 - 0.03:.3f},{yy - 0.03}) rectangle ++({W + 0.06},{W + 0.06});")
        lab(KX - 0.25, yy + W / 2, rf"row {row}, box {box}: \ kept bit {k}" + (rf" $\to$ cells {row * 9 + box * 3}--{row * 9 + box * 3 + 2}" if on else ""), font=r'\scriptsize')
        if on:
            lab(strip_end(KX, 9) + 0.2, yy + W / 2, r"$= \mathbf{1} \Rightarrow$ OR in", 'west', r'\scriptsize')
            cc = 0b111 << (row * 9 + box * 3)
            strip(CX, yy, cc, 27, green=cc, boxbg=cell_bg, top=first, labels=cell_label)
        else:
            lab(strip_end(KX, 9) + 0.2, yy + W / 2, r"$= 0 \Rightarrow$ skip", 'west', r'\scriptsize')
            if first:
                strip(CX, yy, 0, 27, boxbg=cell_bg, top=True)
                lab(CX + 0.1, yy - 0.18, r"(nothing ORed in)", 'west', r'\fontsize{5}{6}\selectfont')
        first = False
        yy -= 0.82
w(rf"\draw[thick] ({CX - 0.2},{yy + 0.5}) -- ({strip_end(CX, 27)},{yy + 0.5});")
yy -= 0.2
strip(CX, yy, pc, 27, green=pc, boxbg=cell_bg, top=False, labels=lambda b: cell_label(b), all_labels=True)
lab(CX - 0.25, yy + W / 2, rf"OR of the {bin(ok).count(chr(49))} rows that said 1: \ \texttt{{POSSIBLE\_CELLS[{lit(mr, 9)}]}} $=$", font=r'\scriptsize')
lab(CX, yy - 0.5, rf"$= \texttt{{{lit(pc, 27)}}} = {pc}$", 'west', r'\scriptsize')
yy -= 1.1
note(X - 5.2, yy, r"Every label under this strip is shown, because these are the cells that are \emph{allowed} to keep the digit: (row 0, boxes 0 and 1) = r0c0--5, (row 1, boxes 0 and 1) = r1c0--5, (row 2, box 2) = r2c6--8. "
     r"Row 2's boxes 0 and 1 had candidates (they are 1s in \texttt{boxCandidates}), but they are 0 in \texttt{kept}, so their cells stay 0 here. "
     r"This is also a table of 512 precomputed entries, so step 7 is one load and one AND. (The stack rule cannot do this, because its answer lands in three different integers.)", 26)

# ---------------------------------------------------------------- 7. AND
Y = yy - 1.9
title(Y, rf"7. \ \texttt{{bandCells \&= POSSIBLE\_CELLS[boxCandidates];}} \quad \texttt{{if (!bandCells) return false;}}")
X = 8.2
yy = Y - 1.6
strip(X, yy, cells, 27, labels=lambda b: cell_label(b) if cells >> b & 1 else '', fills=cell_fill, boxbg=cell_bg)
lab(X - 0.25, yy + W / 2, r"\texttt{bandCells}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(cells, 27)}}}$", 'west', r'\scriptsize')
yy -= 0.8
strip(X, yy, pc, 27, green=pc, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, rf"\texttt{{\& POSSIBLE\_CELLS[{lit(mr, 9)}]}}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(pc, 27)}}}$", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 4.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 1.0
strip(X, yy, after, 27, labels=lambda b: cell_label(b) if cells >> b & 1 else '', fills=cell_fill, red=cells & ~pc, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"new \texttt{bandCells}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(after, 27)}}} = {after}$", 'west', r'\scriptsize')
yy -= 0.75
note(X - 5.2, yy, rf"A bit survives only where both are 1. The two \textcolor{{red!75!black}}{{red 0s}} were 1s in \texttt{{bandCells}} that fell outside the allowed cells: r2c2 (bit 20) and r2c3 (bit 21). They are the candidates removed. "
     rf"\texttt{{bandCells}} is {after}, not 0, so the band is still solvable and \texttt{{updateBand}} goes on. Had $A$ had no perfect matching, \texttt{{PERMUTATION\_UNION}} and \texttt{{POSSIBLE\_CELLS}} would be 0, the AND would give 0, and \texttt{{return false}} would make the solver backtrack.", 20.5)
# after board
GX, GY = 23.4, yy - 2.0
for r in range(3):
    for c in range(9):
        x, y = GX + c * CS * 0.8, GY + (2 - r) * CS * 0.8
        s = CS * 0.8
        w(rf"\fill[{BOXC[c // 3]}] ({x},{y}) rectangle ++({s},{s});")
        bit = 9 * r + c
        if after >> bit & 1:
            w(rf"\node[font=\small\bfseries] at ({x + s / 2},{y + s / 2}) {{5}};")
        elif cells >> bit & 1:
            w(rf"\node[font=\small\bfseries,text=red!75!black] at ({x + s / 2},{y + s / 2}) {{5}}; \draw[red!75!black,thick] ({x + 0.08},{y + 0.08}) -- ++({s - 0.16},{s - 0.16});")
s = CS * 0.8
w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={s}] (0,0) grid ({9 * s},{3 * s});\end{{scope}} \draw[thick] ({GX},{GY}) rectangle ++({9 * s},{3 * s});")
for q in (3, 6): w(rf"\draw[thick] ({GX + q * s},{GY}) -- ++(0,{3 * s});")
for r in range(3): lab(GX - 0.08, GY + (2.5 - r) * s, f"r{r}", 'east', r'\scriptsize')
for c in range(9): lab(GX + (c + 0.5) * s, GY + 3 * s + 0.18, f"c{c}", 'center', r'\tiny')
lab(GX + 4.5 * s, GY - 0.3, r"the band after: 2 candidates struck", 'center', r'\scriptsize')

w(r"\end{tikzpicture}\end{document}")
# build in a temporary directory, keep only the PNG, next to this script
here = os.path.dirname(os.path.abspath(__file__))
with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, 'bandrule.tex'), 'w').write('\n'.join(L))
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'bandrule.tex'], cwd=tmp, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['pdftoppm', '-r', '170', '-png', '-singlefile', 'bandrule.pdf', 'bandrule'], cwd=tmp, check=True)
    shutil.copy(os.path.join(tmp, 'bandrule.png'), os.path.join(here, 'bandrule.png'))
