#!/usr/bin/env python3
# Stack rule, traced line by line through stackRule, in the same style as bandrule.py: every value drawn as its
# full bit string (high bit on the left), every 0 shown, every 1 labelled with its cell. The call is the real one from
# updateband.py: stackRule(state, 5) (the value 6), made by updateBand<0>(state, 5) while solving magictour puzzle 96,
# right after the band rule shrank band 0. The masks are the real ones from paper/figs/dump.cpp.
import subprocess, os, shutil, tempfile

# shared helpers (strip, lab, title, note, lit, colours, preamble) from the band rule diagram
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bandrule.py')).read()
exec(src.split('# ---------------------------------------------------------------- 0. the board')[0])

DIGIT, VALUE = 5, 6
# state.valueToBand[5] when stackRule is called: band 0 as the band rule just left it, bands 1 and 2 unchanged
digitBands = [0b011_000_110_000_001_000_011_000_010, 0b000_100_111_000_100_111_100_000_000, 0b011_000_110_010_000_110_000_010_000]
# what the real call left behind, to check the Python below against
EXPECTED = [0b011_000_110_000_001_000_011_000_010, 0b000_100_001_000_100_001_100_000_000, 0b011_000_110_010_000_110_000_010_000]
CANDS = [(3 * b + bit // 9, bit % 9) for b in range(3) for bit in range(27) if digitBands[b] >> bit & 1]
nz = lambda sh: ((1 << sh) - 1) << (27 - sh) if sh else 0
bandColumns = lambda m: (m | m >> 9 | m >> 18) & M9
column_cells = lambda x: x | x << 9 | x << 18
p = [bandColumns(x) for x in digitBands]
keep = [0, 0, 0]
iters = []
for shift in (0, 3, 6):
    sl = [p[b] >> shift & 0b111 for b in range(3)]
    m = sl[0] | sl[1] << 3 | sl[2] << 6
    ok = permutation_union(m)
    before = keep[:]
    for b in range(3): keep[b] |= (ok >> (3 * b) & 0b111) << shift
    iters.append((shift, sl, m, ok, before, keep[:]))
after = [digitBands[b] & column_cells(keep[b]) for b in range(3)]
assert after == EXPECTED

BANDC = ['blue!25', 'orange!35', 'teal!30']     # fill of a 1 by its band
STACKC = BOXC                                    # faint background by stack (= box column within a band)
glab = lambda b: (lambda bit: f"r{3 * b + bit // 9}c{bit % 9}")
gfill = lambda b: (lambda bit: BANDC[b])
stack_bg = lambda bit: STACKC[(bit % 9) // 3]
col_bg = lambda bit: STACKC[bit // 3]            # for 9-bit column sets

# ---------------------------------------------------------------- 0. purpose and board
Y = 2.9
title(Y, r"The stack rule, line by line: \texttt{stackRule(state, 5)} (the value 6), a real call on magictour puzzle 96. \ Every value is drawn as its full bit string, high bit on the left, as in C++")
w(r"""\node[draw=blue!50!black,fill=blue!4,rounded corners=3pt,inner sep=7pt,anchor=north west,align=left,text width=29.2cm,font=\normalsize] at (-0.5,2.2) {
\textbf{What the stack rule is for.} It is the band rule turned sideways. A stack is three boxes stacked on top of each other, one in each band, so it spans three columns of the grid. Each value must appear exactly once in every column and exactly once in every box.
So within a stack, the value's three columns must be paired one-to-one with the three bands: each band gets the column its value will sit in, and no two bands get the same column.
\textbf{The rule removes every candidate that could not be part of any such pairing}, because filling it in would leave some other column or band with nowhere for the value.
If a stack has no pairing at all, the bands lose that stack entirely, and the band rule then finds the dead end.
Below, this is done for one digit with three table lookups (one per stack) and one AND per band. \texttt{updateBand<0>} called it here because band 0's set of columns no longer matches its set at the last check (\texttt{lastChecked}): columns 0 and 5 are gone.};""")

GX, GY, CS = 0.8, -7.4, 0.62
def board(GX, GY, CS, show):
    for r in range(9):
        for c in range(9):
            x, y = GX + c * CS, GY + (8 - r) * CS
            w(rf"\fill[{STACKC[c // 3]}] ({x},{y}) rectangle ++({CS},{CS});")
            show(r, c, x, y)
    w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={CS}] (0,0) grid ({9 * CS},{9 * CS});\end{{scope}}")
    w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * CS},{9 * CS});")
    for q in (3, 6):
        w(rf"\draw[thick] ({GX + q * CS},{GY}) -- ++(0,{9 * CS});")
        w(rf"\draw[very thick] ({GX},{GY + q * CS}) -- ++({9 * CS},0);")
    for c in range(9): lab(GX + c * CS + CS / 2, GY + 9 * CS + 0.2, f"c{c}", 'center', r'\scriptsize')
    for k in range(3): lab(GX + (3 * k + 1.5) * CS, GY + 9 * CS + 0.6, f"stack {k}", 'center', r'\scriptsize')
    for r in range(9): lab(GX - 0.08, GY + (8.5 - r) * CS, f"r{r}", 'east', r'\scriptsize')
    for b in range(3):
        w(rf"\draw[decorate,decoration={{brace,amplitude=4pt,mirror}}] ({GX - 0.55},{GY + (9 - 3 * b) * CS - 0.05}) -- ({GX - 0.55},{GY + (6 - 3 * b) * CS + 0.05}) node[midway,left=4pt,font=\scriptsize] {{band {b}}};")
def show_before(r, c, x, y):
    w(rf"\node[font=\fontsize{{5}}{{6}}\selectfont,text=gray] at ({x + CS - 0.14},{y + CS - 0.12}) {{{9 * (r % 3) + c}}};")
    if (r, c) in CANDS: w(rf"\node[font=\small\bfseries] at ({x + CS / 2 - 0.05},{y + CS / 2 - 0.05}) {{{VALUE}}};")
board(GX, GY, CS, show_before)
note(GX + 9 * CS + 0.6, GY + 9 * CS + 0.75,
     rf"The value 6 (\texttt{{digit}} 5) can still go in the {len(CANDS)} cells marked 6. The small gray number is the cell's bit in its band's integer (bit $= 9\times$ row within the band $+$ column),"
     r" so the three bands use the same bit numbers 0--26. Cells already solved, and cells where 6 was removed earlier, are blank.\\[3pt]"
     r"\textbf{How to read the strips below.} The same as the band rule picture: each box is one bit, its position in tiny gray above it, high bit on the left;"
     r" small gaps every 3 bits, wider gaps every 9.\\"
     r"A 1 is bold and coloured by its \emph{band}: \colorbox{blue!25}{band 0}\ \colorbox{orange!35}{band 1}\ \colorbox{teal!30}{band 2}. A 0 is gray. Every 0 is drawn.\\"
     r"The label under a 1 is its cell on the board (r4c6 = row 4, column 6). The faint background marks the \emph{stack}: \colorbox{red!7}{stack 0}\ \colorbox{yellow!18}{stack 1}\ \colorbox{violet!8}{stack 2}.\\[3pt]"
     r"The band rule worked inside one band (rows $\leftrightarrow$ boxes). The stack rule needs all three bands of the digit at once (bands $\leftrightarrow$ columns),"
     r" so it reads three integers and writes three.", 19.5)

# ---------------------------------------------------------------- 1. load
Y = GY - 1.4
title(Y, r"1. \ \texttt{Mask *digitBands = state.valueToBand[digit];} \quad \texttt{digit} $=5$ (the value 6): its three band integers \texttt{digitBands[0]}, \texttt{digitBands[1]}, \texttt{digitBands[2]}")
X = 8.2
yy = Y - 1.6
for b in range(3):
    strip(X, yy, digitBands[b], 27, labels=glab(b), fills=gfill(b), boxbg=stack_bg, top=(b == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{digitBands[{b}]}} (rows {3 * b}--{3 * b + 2})")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(digitBands[b], 27)}}}$", 'west', r'\scriptsize')
    yy -= 0.85
for k, t in enumerate(["row 2 of the band (bits 26--18)", "row 1 (bits 17--9)", "row 0 (bits 8--0)"]):
    x0, x1 = xpos(X, 9 * k), xpos(X, 9 * k + 8) + W
    w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({x0},{Y - 1.6 + W + 0.3}) -- ({x1},{Y - 1.6 + W + 0.3}) node[midway,above=2pt,font=\scriptsize] {{{t}}};")

# ---------------------------------------------------------------- 2. bandColumns
Y = yy - 0.7
title(Y, r"2. \ \texttt{Mask columns0 = bandColumns(digitBands[0]), columns1 = \ldots, columns2 = \ldots;} \quad each band's set of columns")
note(-0.3, Y - 0.45, r"\texttt{bandColumns(bandCells) = (bandCells | bandCells >> 9 | bandCells >> 18) \& 0b111\textquotesingle{}111\textquotesingle{}111}. "
     r"The stack rule only needs to know which \emph{columns} a band can put the digit in, not which row, so the band's 3 rows are ORed on top of each other: "
     r"\texttt{>> 9} and \texttt{>> 18} slide rows 1 and 2 down onto row 0 (hatched 0s are new zeros that come in on the left), and the mask keeps bits 0--8.", 30)
yy = Y - 2.5
def shl(b, sh): return lambda bit: glab(b)(bit + sh) if bit + sh < 27 else ''
for b in range(3):
    m = digitBands[b]
    lab(X - 4.6, yy + 0.95, rf"\textbf{{band {b}}}", 'west', r'\small')
    for k, sh in enumerate((0, 9, 18)):
        strip(X, yy, m >> sh, 27, labels=shl(b, sh), fills=gfill(b), newzero=nz(sh), boxbg=stack_bg, top=(b == 0 and k == 0))
        lab(X - 0.25, yy + W / 2, [rf"\texttt{{digitBands[{b}]}}", rf"\texttt{{digitBands[{b}] >> 9}}", rf"\texttt{{digitBands[{b}] >> 18}}"][k])
        yy -= 0.72
    yy -= 0.2
    w(rf"\draw[thick] ({X - 2.4},{yy + 0.62}) -- ({strip_end(X, 27)},{yy + 0.62});")
    orv = m | m >> 9 | m >> 18
    strip(X, yy - 0.05, orv, 27, fills=gfill(b), top=False, boxbg=stack_bg)
    lab(X - 0.25, yy - 0.05 + W / 2, r"OR")
    lab(strip_end(X, 27) + 0.25, yy - 0.05 + W / 2, r"bits 9--26 are leftover partial ORs with no meaning", 'west', r'\scriptsize')
    yy -= 0.8
    strip(X, yy, p[b], 27, fills=gfill(b), top=False, boxbg=stack_bg, labels=lambda bit: f"c{bit}" if bit < 9 else '', all_labels=True)
    lab(X - 0.25, yy + W / 2, rf"\texttt{{\& 0b111\textquotesingle{{}}111\textquotesingle{{}}111}} $=$ \texttt{{columns{b}}}")
    cols = [c for c in range(9) if p[b] >> c & 1]
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$= \texttt{{{lit(p[b], 9)}}} = {p[b]}$: \ columns $\{{{','.join(map(str, cols))}\}}$", 'west', r'\scriptsize')
    yy -= 1.25

# ---------------------------------------------------------------- 3. the loop
Y = yy - 0.2
title(Y, r"3. \ \texttt{for (int shift = 0; shift < 9; shift += 3)}: \ one pass per stack; \texttt{shift} is the stack's first column (0, 3, 6)")
note(-0.3, Y - 0.45,
     r"\texttt{Mask columnCandidates = (columns0 >> shift \& 0b111) | (columns1 >> shift \& 0b111) << 3 | (columns2 >> shift \& 0b111) << 6;}\\"
     r"\texttt{Mask kept = PERMUTATION\_UNION[columnCandidates];}\\"
     r"\texttt{keptColumns0 |= (kept \& 0b111) << shift; \ keptColumns1 |= (kept >> 3 \& 0b111) << shift; \ keptColumns2 |= (kept >> 6 \& 0b111) << shift;}\\[2pt]"
     r"Each pass has three parts, drawn below: (a) build \texttt{columnCandidates}, a $3\times3$ table with one row per band and one column per column of the stack;"
     r" (b) look it up in \texttt{PERMUTATION\_UNION}, the same table as the band rule; (c) write each band's kept columns back into its \texttt{keptColumns}.", 30)
yy = Y - 3.6
CA, CB, CC, CD, CE = 3.0, 9.3, 15.5, 18.6, 25.6   # x of the five strip columns
nzl = lambda sh, n: ((1 << sh) - 1) << (n - sh) if sh else 0     # zeros shifted in on the left
nzr = lambda sh: (1 << sh) - 1                                   # zeros shifted in on the right
TS = 0.5                                                          # cell size of the small 3 x 3 tables
def table3(TX, TY, val, red=0, green=0, colbase=0, heading=''):
    """9 bits as a 3 x 3 table in strip order: band 2 on top, the stack's highest column on the left."""
    lab(TX + 1.5 * TS, TY + 3 * TS + 0.62, heading, 'center', r'\scriptsize')
    for j in range(3): lab(TX + (2.5 - j) * TS, TY + 3 * TS + 0.18, f"c{colbase + j}", 'center', r'\fontsize{5}{6}\selectfont')
    for bb in range(3):
        lab(TX - 0.06, TY + (bb + 0.5) * TS, f"band {bb}", 'east', r'\fontsize{5}{6}\selectfont')
        for j in range(3):
            bit = 3 * bb + j
            x, y = TX + (2 - j) * TS, TY + bb * TS
            if red >> bit & 1:
                w(rf"\fill[red!22] ({x},{y}) rectangle ++({TS},{TS}); \node[font=\scriptsize\bfseries,text=red!75!black] at ({x + TS / 2},{y + TS / 2}) {{0}};")
            elif val >> bit & 1:
                w(rf"\fill[{'green!40' if green >> bit & 1 else BANDC[bb]}] ({x},{y}) rectangle ++({TS},{TS}); \node[font=\scriptsize\bfseries] at ({x + TS / 2},{y + TS / 2}) {{1}};")
            else:
                w(rf"\node[font=\scriptsize,text=gray!75] at ({x + TS / 2},{y + TS / 2}) {{0}};")
            w(rf"\node[font=\fontsize{{4}}{{5}}\selectfont,text=gray] at ({x + TS - 0.08},{y + TS - 0.08}) {{{bit}}};")
    w(rf"\begin{{scope}}[shift={{({TX},{TY})}}]\draw[gray!55,step={TS}] (0,0) grid ({3 * TS},{3 * TS});\end{{scope}} \draw[thick] ({TX},{TY}) rectangle ++({3 * TS},{3 * TS});")
def sub(yy, t):
    lab(-0.3, yy, t, 'west', r'\footnotesize\bfseries')
for (shift, sl, m, ok, kb, ka) in iters:
    k = shift // 3
    cl = lambda bit, shift=shift: f"b{bit // 3}c{shift + bit % 3}"     # a bit of columnCandidates / kept
    w(rf"\fill[{STACKC[k]}] (-0.5,{yy + 0.15}) rectangle (31,{yy + 0.75});")
    lab(-0.3, yy + 0.45, rf"\textbf{{stack {k}}}: \texttt{{shift = {shift}}}, columns {shift}, {shift + 1}, {shift + 2}", 'west', r'\small')
    yy -= 0.75
    # (a) build columnCandidates
    sub(yy, r"(a) build \texttt{columnCandidates}")
    yy -= 0.9
    hdr = yy + W + 0.42
    lab((CB + strip_end(CB, 9)) / 2, hdr, rf"\texttt{{>> {shift}}}: the stack's columns move to bits 0--2", 'center', r'\scriptsize')
    lab((CC + strip_end(CC, 3)) / 2, hdr, r"\texttt{\& 0b111}", 'center', r'\scriptsize')
    lab((CD + strip_end(CD, 9)) / 2, hdr, r"\texttt{<< 3 * band}: into the band's row of the table", 'center', r'\scriptsize')
    slotted = 0
    for b in range(3):
        hl = lambda bit, shift=shift: 'yellow!55' if shift <= bit < shift + 3 else 'white'
        strip(CA, yy, p[b], 9, fills=gfill(b), boxbg=hl, top=(b == 0), labels=lambda bit: f"c{bit}", all_labels=False)
        lab(CA - 0.2, yy + W / 2, rf"\texttt{{columns{b}}}", font=r'\scriptsize')
        strip(CB, yy, p[b] >> shift, 9, fills=gfill(b), newzero=nzl(shift, 9), boxbg=lambda bit: 'white', top=(b == 0),
              labels=lambda bit, shift=shift: f"c{bit + shift}" if bit + shift < 9 else '')
        strip(CC, yy, sl[b], 3, fills=gfill(b), boxbg=lambda bit: STACKC[k], top=(b == 0), labels=lambda bit, shift=shift: f"c{shift + bit}")
        v = sl[b] << (3 * b)
        slotted |= v
        strip(CD, yy, v, 9, fills=gfill(b), newzero=nzr(3 * b), boxbg=lambda bit: STACKC[k], top=(b == 0), labels=cl)
        lab(strip_end(CD, 9) + 0.15, yy + W / 2, rf"\texttt{{{lit(v, 9)}}}", 'west', r'\scriptsize')
        yy -= 0.8
    w(rf"\draw[thick] ({CD - 0.2},{yy + 0.62}) -- ({strip_end(CD, 9)},{yy + 0.62});")
    yy -= 0.1
    strip(CD, yy, m, 9, fills=lambda bit: BANDC[bit // 3], boxbg=lambda bit: STACKC[k], top=False, labels=cl)
    lab(CD - 0.2, yy + W / 2, r"OR: \texttt{columnCandidates} $=$", font=r'\scriptsize')
    lab(strip_end(CD, 9) + 0.15, yy + W / 2, rf"\texttt{{{lit(m, 9)}}}", 'west', r'\scriptsize')
    yy -= 1.0
    # (b) look up
    sub(yy, rf"(b) \texttt{{kept = PERMUTATION\_UNION[{lit(m, 9)}]}}: \ which 1s lie on some pairing of bands with columns (one 1 per band and per column)?")
    yy -= 1.35 if k == 0 else 0.9
    if k == 0:
        lab(CB + 0.0, yy + W + 0.42, r"\texttt{permutation}: band $i$ gets column \texttt{p[i]} of the stack", 'west', r'\scriptsize')
        lab(CD, yy + W + 0.42, r"\texttt{columnCandidates \& permutation}", 'west', r'\scriptsize')
        for pp in PERMS:
            e = 1 << pp[0] | 1 << (3 + pp[1]) | 1 << (6 + pp[2])
            good = m & e == e
            lab(CB - 0.25, yy + W / 2, rf"\texttt{{p = \{{{pp[0]},{pp[1]},{pp[2]}\}}}}: b0$\to$c{shift + pp[0]}, b1$\to$c{shift + pp[1]}, b2$\to$c{shift + pp[2]}", 'east', r'\scriptsize')
            strip(CB, yy, e, 9, fills=lambda bit: 'gray!35', boxbg=lambda bit: STACKC[k], top=False, labels=lambda bit, e=e: cl(bit) if e >> bit & 1 else '')
            strip(CD, yy, m & e, 9, fills=lambda bit: BANDC[bit // 3], red=e & ~m, boxbg=lambda bit: STACKC[k], top=False)
            verdict = (r"\textcolor{green!50!black}{\textbf{yes}}: all 3 are 1s, so it is ORed in" if good
                       else rf"\textcolor{{red!70!black}}{{no}}: 0 at {', '.join(cl(bt) for bt in range(9) if (e & ~m) >> bt & 1)}")
            lab(strip_end(CD, 9) + 0.2, yy + W / 2, verdict, 'west', r'\scriptsize')
            yy -= 0.72
        w(rf"\draw[thick] ({CB - 0.2},{yy + 0.55}) -- ({strip_end(CB, 9)},{yy + 0.55});")
        yy -= 0.1
        strip(CB, yy, ok, 9, green=ok, boxbg=lambda bit: STACKC[k], top=False, labels=lambda bit: cl(bit) if ok >> bit & 1 else '')
        lab(CB - 0.25, yy + W / 2, r"OR of the yes rows: \texttt{kept} $=$", font=r'\scriptsize')
        lab(strip_end(CB, 9) + 0.15, yy + W / 2, rf"\texttt{{{lit(ok, 9)}}}", 'west', r'\scriptsize')
        TY = yy - 1.75
    else:
        strip(CB, yy, m, 9, fills=lambda bit: BANDC[bit // 3], boxbg=lambda bit: STACKC[k], top=True, labels=cl)
        lab(CB - 0.25, yy + W / 2, r"\texttt{columnCandidates} $=$", font=r'\scriptsize')
        yy -= 0.85
        strip(CB, yy, ok, 9, green=ok, red=m & ~ok, boxbg=lambda bit: STACKC[k], top=False, labels=lambda bit: cl(bit) if (ok | m) >> bit & 1 else '')
        lab(CB - 0.25, yy + W / 2, r"\texttt{kept} $=$", font=r'\scriptsize')
        lab(strip_end(CB, 9) + 0.15, yy + W / 2, rf"\texttt{{{lit(ok, 9)}}} \ (same table as the band rule's step 5)", 'west', r'\scriptsize')
        TY = yy - 0.3
    fits = []
    for pp in PERMS:
        e = 1 << pp[0] | 1 << (3 + pp[1]) | 1 << (6 + pp[2])
        if m & e == e: fits.append(', '.join(rf"b{bb}$\to$c{shift + pp[bb]}" for bb in range(3)))
    gone = [cl(bit) for bit in range(9) if (m & ~ok) >> bit & 1]
    TX = 23.6 if k == 0 else 26.0
    table3(TX - 2.6, TY, m, colbase=shift, heading=r"\texttt{columnCandidates}")
    table3(TX + 0.9, TY, ok | (m & ~ok), red=m & ~ok, green=ok, colbase=shift, heading=r"\texttt{kept}")
    yy -= 0.8
    txt = (rf"{'One pairing fits' if len(fits) == 1 else f'{len(fits)} pairings fit'}: " + r"; \ ".join(fits) + r". \ "
           + (rf"\textcolor{{red!70!black}}{{Red}}: {', '.join(gone)} {'is' if len(gone) == 1 else 'are'} on no pairing, so {'it is' if len(gone) == 1 else 'they are'} dropped." if gone else r"Every 1 of \texttt{columnCandidates} is on some pairing, so nothing is dropped."))
    note(CB - 0.2, yy + 0.1, txt, 9.8 if k == 0 else 13.5)
    yy = min(yy - 1.4, TY - 0.6)
    # (c) write back
    sub(yy, r"(c) write each band's 3 bits of \texttt{kept} back into its \texttt{keptColumns}, at the stack's columns")
    yy -= 1.35
    hdr = yy + W + 0.42
    lab((CB + strip_end(CB, 9)) / 2, hdr, r"\texttt{kept >> 3 * band}: the band's row to bits 0--2", 'center', r'\scriptsize')
    lab((CC + strip_end(CC, 3)) / 2, hdr, r"\texttt{\& 0b111}", 'center', r'\scriptsize')
    lab((CD + strip_end(CD, 9)) / 2, hdr, rf"\texttt{{<< {shift}}}: back to columns {shift}--{shift + 2}", 'center', r'\scriptsize')
    lab((CE + strip_end(CE, 9)) / 2, hdr, r"\texttt{keptColumns} after \texttt{|=} (new bits green)", 'center', r'\scriptsize')
    for b in range(3):
        strip(CA, yy, ok, 9, green=ok, boxbg=lambda bit, b=b: 'yellow!55' if bit // 3 == b else 'white', top=(b == 0), labels=lambda bit: '')
        lab(CA - 0.2, yy + W / 2, r"\texttt{kept}", font=r'\scriptsize')
        sh = ok >> (3 * b)
        strip(CB, yy, sh, 9, green=sh, newzero=nzl(3 * b, 9), boxbg=lambda bit: 'white', top=(b == 0),
              labels=lambda bit, b=b: cl(bit + 3 * b) if bit + 3 * b < 9 and ok >> (bit + 3 * b) & 1 else '')
        lab(CB - 0.2, yy + W / 2, rf"\texttt{{>> {3 * b}}}", font=r'\scriptsize')
        s3 = sh & 0b111
        strip(CC, yy, s3, 3, green=s3, boxbg=lambda bit: STACKC[k], top=(b == 0))
        v = s3 << shift
        strip(CD, yy, v, 9, green=v, newzero=nzr(shift), boxbg=col_bg, top=(b == 0), labels=lambda bit, v=v: f"c{bit}" if v >> bit & 1 else '')
        nb = ka[b] & ~kb[b]
        strip(CE, yy, ka[b], 9, fills=lambda bit, nb=nb, b=b: 'green!40' if nb >> bit & 1 else BANDC[b], boxbg=col_bg, top=(b == 0),
              labels=lambda bit: f"c{bit}")
        lab(CE - 0.2, yy + W / 2, rf"\texttt{{keptColumns{b}}}", font=r'\scriptsize')
        yy -= 0.8
    yy -= 0.9

# ---------------------------------------------------------------- 4. apply
Y = yy + 0.3
title(Y, r"4. \ \texttt{digitBands[0] \&= columnCells(keptColumns0);} \ (and the same for bands 1 and 2) \quad \texttt{columnCells(x) = x | x << 9 | x << 18}")
note(-0.3, Y - 0.45, r"\texttt{columnCells} copies the 9 kept columns into all 3 rows of the band (hatched 0s are new zeros that come in on the right), so the AND keeps a candidate only if its column is kept for its band.", 30)
yy = Y - 1.9
for b in range(3):
    lab(X - 4.6, yy + 0.25, rf"\textbf{{band {b}}}", 'west', r'\small')
    kcv = keep[b]
    for j, sh in enumerate((0, 9, 18)):
        strip(X, yy, kcv << sh, 27, green=kcv << sh, newzero=nzr(sh), boxbg=stack_bg, top=(b == 0 and j == 0),
              labels=lambda bit, sh=sh: f"c{bit % 9}" if (kcv << sh) >> bit & 1 else '')
        lab(X - 0.25, yy + W / 2, rf"\texttt{{keptColumns{b}}}" + (rf" \texttt{{<< {sh}}}" if sh else ""))
        yy -= 0.72
    yy -= 0.15
    cc = column_cells(kcv)
    w(rf"\draw[thick] ({X - 3.0},{yy + 0.6}) -- ({strip_end(X, 27)},{yy + 0.6});")
    strip(X, yy, cc, 27, green=cc, boxbg=stack_bg, top=False)
    lab(X - 0.25, yy + W / 2, rf"OR: \texttt{{columnCells(keptColumns{b})}}")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(cc, 27)}}}$", 'west', r'\scriptsize')
    yy -= 1.05
    strip(X, yy, digitBands[b], 27, labels=glab(b), fills=gfill(b), boxbg=stack_bg, top=False)
    lab(X - 0.25, yy + W / 2, rf"\texttt{{digitBands[{b}]}}")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(digitBands[b], 27)}}}$", 'west', r'\scriptsize')
    yy -= 0.8
    strip(X, yy, cc, 27, green=cc, boxbg=stack_bg, top=False)
    lab(X - 0.25, yy + W / 2, rf"\texttt{{\& columnCells(keptColumns{b})}}")
    w(rf"\draw[thick] ({X - 3.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
    yy -= 1.0
    rem = digitBands[b] & ~cc
    strip(X, yy, after[b], 27, labels=lambda bit, b=b: glab(b)(bit), fills=gfill(b), red=rem, boxbg=stack_bg, top=False)
    lab(X - 0.25, yy + W / 2, rf"new \texttt{{digitBands[{b}]}}")
    gone = [glab(b)(bit) for bit in range(27) if rem >> bit & 1]
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(after[b], 27)}}}$ \ " + (rf"removed: {', '.join(gone)}" if gone else "nothing removed"), 'west', r'\scriptsize')
    yy -= 1.35
note(X - 5.2, yy + 0.2,
     r"The \textcolor{red!75!black}{red 0s} are the candidates removed."
     r" Unlike the band rule, the answer for one band depends on the other two bands, and it lands in three different integers, so there is no single precomputed 27-bit mask to AND with: the stack rule builds"
     r" each \texttt{keptColumns} pass by pass and spreads it with \texttt{columnCells}. It runs only when a band's set of columns has changed, since that is all it reads.\\[3pt]"
     r"It writes \texttt{valueToBand} but not \texttt{checked}. Band 1 lost cells here, so \texttt{valueToBand[5][1]} no longer matches \texttt{checked[5][1]}, and \texttt{update}'s next pass runs \texttt{updateBand<1>} on it."
     r" Band 0 is the band \texttt{updateBand<0>} is working on; it is unchanged here, but that call still re-reads it (\texttt{digitMaskNow}) before placing, in case it was not.", 20.5)

# after board
def show_after(r, c, x, y):
    b, bit = r // 3, 9 * (r % 3) + c
    if after[b] >> bit & 1:
        w(rf"\node[font=\small\bfseries] at ({x + CS / 2},{y + CS / 2}) {{{VALUE}}};")
    elif digitBands[b] >> bit & 1:
        w(rf"\node[font=\small\bfseries,text=red!75!black] at ({x + CS / 2},{y + CS / 2}) {{{VALUE}}}; \draw[red!75!black,thick] ({x + 0.08},{y + 0.08}) -- ++({CS - 0.16},{CS - 0.16});")
CS2 = 0.5
_cs = CS; CS = CS2
board(25.0, yy - 4.4, CS2, show_after)
CS = _cs
lab(25.0 + 4.5 * CS2, yy - 4.75, r"the grid after: struck 6s are the ones removed", 'center', r'\scriptsize')

w(r"\end{tikzpicture}\end{document}")
# build in a temporary directory, keep only the PNG, next to this script
here = os.path.dirname(os.path.abspath(__file__))
with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, 'stackrule.tex'), 'w').write('\n'.join(L))
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'stackrule.tex'], cwd=tmp, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['pdftoppm', '-r', '170', '-png', '-singlefile', 'stackrule.pdf', 'stackrule'], cwd=tmp, check=True)
    shutil.copy(os.path.join(tmp, 'stackrule.png'), os.path.join(here, 'stackrule.png'))
