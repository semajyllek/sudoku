#!/usr/bin/env python3
# The six smaller lookup tables of fastbandsolver.hpp, one diagram each: the build code, one entry traced bit by bit
# in the same style as bandrule.py (full bit strings, high bit on the left, every 0 shown), and where it is used.
# Writes one_column_boxes.png, single_rows.png, rows_cells.png, after_placing.png, other_bands_after_placing.png and
# band_peers.png next to this script.
import subprocess, os, shutil, tempfile

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'bandrule.py')).read()
exec(src.split('# ---------------------------------------------------------------- 0. the board')[0])
PREAMBLE = L[:]
ALL = (1 << 27) - 1


def render(name):
    w(r"\end{tikzpicture}\end{document}")
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, f'{name}.tex'), 'w').write('\n'.join(L))
        subprocess.run(['pdflatex', '-interaction=nonstopmode', f'{name}.tex'], cwd=tmp, stdout=subprocess.DEVNULL, check=True)
        subprocess.run(['pdftoppm', '-r', '170', '-png', '-singlefile', f'{name}.pdf', name], cwd=tmp, check=True)
        shutil.copy(os.path.join(tmp, f'{name}.png'), os.path.join(here, f'{name}.png'))
    L[:] = PREAMBLE


def tt(line):
    """One line of C++ as LaTeX \\texttt content: escape the special characters, keep the indentation."""
    body = line.lstrip(' \t')
    indent = len(line) - len(body)
    for a, b in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'),
                 ("'", r'\textquotesingle{}'), ('%', r'\%'), ('#', r'\#')]:
        body = body.replace(a, b)
    return r'\hspace*{' + f'{indent * 0.5}' + r'em}' + body


def code(Y, lines, width=30):
    note(-0.3, Y, r"\texttt{" + r"\\".join(tt(x) for x in lines) + "}", width)


def header(Y, t, purpose):
    title(Y, t)
    w(r"\node[draw=blue!50!black,fill=blue!4,rounded corners=3pt,inner sep=7pt,anchor=north west,align=left,text width=29.2cm,font=\normalsize] at (-0.5,"
      + f"{Y - 0.7}" + r") {" + purpose + "};")


def section(Y, t):
    w(rf"\node[font=\bfseries,anchor=west] at (-0.5,{Y}) {{{t}}};")
    w(rf"\draw[gray!40] (-0.5,{Y - 0.3}) -- (31,{Y - 0.3});")


def band_grid(GX, GY, fills, struck=(), cs=0.55, caption='', dots=()):
    """A 3 x 9 band, row 0 on top, each cell with its bit number; fills = {bit: colour}."""
    for r in range(3):
        for c in range(9):
            bit = 9 * r + c
            x, y = GX + c * cs, GY + (2 - r) * cs
            w(rf"\fill[{fills.get(bit, BOXC[c // 3])}] ({x},{y}) rectangle ++({cs},{cs});")
            w(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont,text=gray] at ({x + cs - 0.12},{y + cs - 0.1}) {{{bit}}};")
            if bit in dots:
                w(rf"\node[font=\small\bfseries] at ({x + cs / 2 - 0.04},{y + cs / 2 - 0.04}) {{5}};")
            if bit in struck:
                w(rf"\draw[red!75!black,thick] ({x + 0.08},{y + 0.08}) -- ++({cs - 0.16},{cs - 0.16});")
    w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={cs}] (0,0) grid ({9 * cs},{3 * cs});\end{{scope}}")
    w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * cs},{3 * cs});")
    for q in (3, 6): w(rf"\draw[thick] ({GX + q * cs},{GY}) -- ++(0,{3 * cs});")
    for c in range(9): lab(GX + (c + 0.5) * cs, GY + 3 * cs + 0.18, f"c{c}", 'center', r'\fontsize{5}{6}\selectfont')
    for r in range(3): lab(GX - 0.06, GY + (2.5 - r) * cs, f"r{r}", 'east', r'\fontsize{5}{6}\selectfont')
    if caption: lab(GX + 4.5 * cs, GY - 0.3, caption, 'center', r'\scriptsize')


hlz = lambda sh, n: ((1 << sh) - 1) << (n - sh) if sh else 0     # zeros a right shift brings in on the left
hrz = lambda sh: (1 << sh) - 1                                    # zeros a left shift brings in on the right
X = 8.2

# the running example, from the band rule diagram: the value 5 in band 0 after the band rule
BAND = (1 << 1) | (1 << 4) | (1 << 9) | (1 << 14) | (1 << 26)    # r0c1, r0c4, r1c0, r1c5, r2c8
COLUMNS = (BAND | BAND >> 9 | BAND >> 18) & M9
KEPT = 0b100_011_011
assert COLUMNS == 0b100_110_011

# ======================================================================== ONE_COLUMN_BOXES
Y = 2.9
header(Y, r"\texttt{ONE\_COLUMN\_BOXES}: a band's set of columns $\to$ the boxes that have exactly one column left",
       r"\textbf{What it is for.} \texttt{columns} is a band's 9-bit set of columns: bit $c$ is 1 when the value can still go somewhere in column $c$ of the band "
       r"(\texttt{columns = bandColumns(bandCells)}). The entry says which of the band's 3 boxes are down to a single column. "
       r"\texttt{updateBand} feeds it, together with the band rule's \texttt{kept} box candidates, into \texttt{SINGLE\_ROWS} to find the rows that are down to one cell. "
       r"512 entries of 8 bits (3 used), built at compile time.")
code(Y - 2.5, ["static constexpr std::array<uint8_t, 512> ONE_COLUMN_BOXES = [] {",
               "    std::array<uint8_t, 512> t{};",
               "    for (int columns = 0; columns < 512; columns++) {",
               "        for (int box = 0; box < 3; box++) {",
               "            if (std::popcount(unsigned((columns >> (box * 3)) & 0b111)) == 1) t[columns] |= 1 << box;",
               "        }",
               "    }",
               "    return t;",
               "}();"])
yy = Y - 7.6
section(yy + 0.6, r"One entry: \texttt{columns = " + lit(COLUMNS, 9) + r"}, the band of the band rule diagram after the band rule (5 at r0c1, r0c4, r1c0, r1c5, r2c8)")
band_grid(24.0, yy - 2.2, {b: 'blue!25' for b in (1, 4, 9, 14, 26)}, dots=(1, 4, 9, 14, 26), caption='the band: 5s in columns 0, 1, 4, 5, 8')
yy -= 0.9
strip(X, yy, COLUMNS, 9, labels=lambda b: f"c{b}", fills=lambda b: 'blue!25', boxbg=lambda b: BOXC[b // 3], all_labels=True)
lab(X - 0.25, yy + W / 2, r"\texttt{columns} $=$")
lab(strip_end(X, 9) + 0.2, yy + W / 2, rf"\texttt{{{lit(COLUMNS, 9)}}}", 'west', r'\scriptsize')
yy -= 1.75
SX, CX = X, 15.0
lab((SX + strip_end(SX, 9)) / 2, yy + W + 0.42, r"\texttt{columns >> (box * 3)}: the box's 3 columns land in bits 0--2", 'center', r'\scriptsize')
lab((CX + strip_end(CX, 3)) / 2, yy + W + 0.42, r"\texttt{\& 0b111}", 'center', r'\scriptsize')
entry = 0
for box in range(3):
    v = COLUMNS >> (box * 3)
    strip(SX, yy, v, 9, fills=lambda b: 'blue!25', newzero=hlz(box * 3, 9), boxbg=lambda b: 'white', top=(box == 0),
          labels=lambda b, box=box: f"c{b + box * 3}" if b + box * 3 < 9 and COLUMNS >> (b + box * 3) & 1 else '')
    lab(SX - 0.25, yy + W / 2, rf"box {box}: \ \texttt{{>> {box * 3}}}", font=r'\scriptsize')
    s3 = v & 0b111
    strip(CX, yy, s3, 3, fills=lambda b: 'blue!25', boxbg=lambda b, box=box: BOXC[box], top=(box == 0), labels=lambda b, box=box: f"c{box * 3 + b}")
    n = bin(s3).count('1')
    if n == 1:
        entry |= 1 << box
        verdict = rf"\texttt{{popcount}} $= 1$ $\Rightarrow$ \texttt{{t[columns] |= 1 << {box}}} \ (box {box} has one column left)"
    else:
        verdict = rf"\texttt{{popcount}} $= {n}$ $\Rightarrow$ skip \ (box {box} has {n} columns)"
    lab(strip_end(CX, 3) + 0.25, yy + W / 2, verdict, 'west', r'\scriptsize')
    yy -= 0.85
yy -= 0.2
strip(CX, yy, entry, 3, green=entry, boxbg=lambda b: BOXC[b], top=True, labels=lambda b: f"b{b}", all_labels=True)
lab(CX - 0.25, yy + W / 2, rf"\texttt{{ONE\_COLUMN\_BOXES[{lit(COLUMNS, 9)}]}} $=$", font=r'\scriptsize')
lab(strip_end(CX, 3) + 0.25, yy + W / 2, rf"\texttt{{{lit(entry, 3)}}}: only box 2 is down to one column (column 8)", 'west', r'\scriptsize')
yy -= 1.4
section(yy + 0.3, r"Where it is used")
note(-0.3, yy - 0.1, r"\texttt{updateBand}: \ \texttt{unsigned singleRows = SINGLE\_ROWS[PERMUTATION\_UNION[boxCandidates] | ONE\_COLUMN\_BOXES[columns] << 9];} \ (see the \texttt{SINGLE\_ROWS} diagram)", 30)
render('one_column_boxes')

# ======================================================================== SINGLE_ROWS
Y = 2.9
header(Y, r"\texttt{SINGLE\_ROWS}: kept box candidates and one-column boxes $\to$ the rows that are down to one cell",
       r"\textbf{What it is for.} After the band rule, a row is down to a single cell when the value can go in only one place in it: that is a \emph{row single}, and the solver places it. "
       r"Checking the 3 rows bit by bit would cost branches, so one lookup does it. The index is 12 bits: the band rule's \texttt{kept} box candidates "
       r"(\texttt{PERMUTATION\_UNION[boxCandidates]}, bit \texttt{3 * row + box}) in bits 0--8, and \texttt{ONE\_COLUMN\_BOXES[columns]} in bits 9--11. "
       r"\textbf{Why that is enough:} a row with two kept boxes has at least two cells. A row with exactly one kept box owns that box in every pairing, so no other row has candidates in it, "
       r"and the box's candidates are exactly this row's triad; the row is down to one cell exactly when that box has one column left. 4096 entries of 8 bits (3 used).")
code(Y - 3.1, ["static constexpr std::array<uint8_t, 4096> SINGLE_ROWS = [] {",
               "    std::array<uint8_t, 4096> t{};",
               "    for (int i = 0; i < 4096; i++) {",
               "        int kept = i & 0b111'111'111, boxes = i >> 9;",
               "        for (int row = 0; row < 3; row++) {",
               "            int inRow = (kept >> (row * 3)) & 0b111;",
               "            if (std::popcount(unsigned(inRow)) == 1 && (boxes & inRow)) t[i] |= 1 << row;",
               "        }",
               "    }",
               "    return t;",
               "}();"])
yy = Y - 8.6
boxes = 0b100
I = KEPT | boxes << 9
section(yy + 0.6, rf"One entry: \texttt{{i = 0b{boxes:03b}\textquotesingle{{}}{lit(KEPT, 9)[2:]}}} $= {I}$, the index \texttt{{updateBand}} builds for the band of the band rule diagram")
band_grid(24.0, yy - 3.0, {b: 'blue!25' for b in (1, 4, 9, 14, 26)}, dots=(1, 4, 9, 14, 26), caption='the band after the band rule: row 2 has one cell')
yy -= 1.0
mlab = lambda b: f"r{b // 3}b{b % 3}"
# i as 12 bits: boxes in bits 11-9, a wide gap, kept in bits 8-0
KX = X + 3 * W + 0.55
strip(X, yy, boxes, 3, green=boxes, boxbg=lambda b: BOXC[b], top=False, labels=lambda b: f"b{b}")
for j in range(3): lab(X + j * W + W / 2, yy + W + 0.13, f"{11 - j}", 'center', r'\fontsize{4.5}{5}\selectfont')
strip(KX, yy, KEPT, 9, green=KEPT, boxbg=lambda b: BOXC[b % 3], labels=lambda b: mlab(b) if KEPT >> b & 1 else '')
w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({X},{yy + W + 0.32}) -- ({X + 3 * W},{yy + W + 0.32}) node[midway,above=2pt,font=\scriptsize] {{\texttt{{boxes}}}};")
w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({KX},{yy + W + 0.32}) -- ({strip_end(KX, 9)},{yy + W + 0.32}) node[midway,above=2pt,font=\scriptsize] {{\texttt{{kept}}}};")
lab(X - 0.25, yy + W / 2, r"\texttt{i} $=$")
lab(strip_end(KX, 9) + 0.2, yy + W / 2, rf"\texttt{{0b{boxes:03b}\textquotesingle{{}}{lit(KEPT, 9)[2:]}}} $= {I}$", 'west', r'\scriptsize')
yy -= 0.75
note(-0.3, yy, r"built in \texttt{updateBand} as \texttt{i = PERMUTATION\_UNION[boxCandidates] | ONE\_COLUMN\_BOXES[columns] << 9}: "
     r"\texttt{kept} (the band rule's kept box candidates, from step 5 of the band rule diagram) in bits 0--8, and \texttt{boxes} "
     r"(from the \texttt{ONE\_COLUMN\_BOXES} diagram) shifted up to bits 9--11. The build loop below takes it apart again:", 21)
yy -= 1.45
strip(KX, yy, KEPT, 9, labels=lambda b: mlab(b) if KEPT >> b & 1 else '', green=KEPT, boxbg=lambda b: BOXC[b % 3], top=False)
lab(KX - 0.25, yy + W / 2, r"\texttt{kept = i \& 0b111\textquotesingle{}111\textquotesingle{}111} $=$", font=r'\scriptsize')
lab(strip_end(KX, 9) + 0.2, yy + W / 2, rf"\texttt{{{lit(KEPT, 9)}}}: bits 0--8 (bit \texttt{{3 * row + box}})", 'west', r'\scriptsize')
yy -= 0.85
strip(KX + 6 * W + 2 * G3, yy, boxes, 3, labels=lambda b: f"b{b}", green=boxes, boxbg=lambda b: BOXC[b], top=False, all_labels=True)
lab(KX - 0.25, yy + W / 2, r"\texttt{boxes = i >> 9} $=$", font=r'\scriptsize')
lab(strip_end(KX, 9) + 0.2, yy + W / 2, r"\texttt{0b100}: bits 9--11 moved down to 0--2; box 2 has one column left", 'west', r'\scriptsize')
yy -= 1.75
SX, CX, BX = X, 15.0, 19.2
lab((SX + strip_end(SX, 9)) / 2, yy + W + 0.42, r"\texttt{kept >> (row * 3)}: the row's 3 box bits land in bits 0--2", 'center', r'\scriptsize')
lab((CX + strip_end(CX, 3)) / 2, yy + W + 0.42, r"\texttt{inRow = \ldots\ \& 0b111}", 'center', r'\scriptsize')
lab((BX + strip_end(BX, 3)) / 2, yy + W + 0.42, r"\texttt{boxes \& inRow}", 'center', r'\scriptsize')
entry = 0
for row in range(3):
    v = KEPT >> (row * 3)
    strip(SX, yy, v, 9, green=v, newzero=hlz(row * 3, 9), boxbg=lambda b: 'white', top=(row == 0),
          labels=lambda b, row=row: mlab(b + row * 3) if b + row * 3 < 9 and KEPT >> (b + row * 3) & 1 else '')
    lab(SX - 0.25, yy + W / 2, rf"row {row}: \ \texttt{{>> {row * 3}}}", font=r'\scriptsize')
    inRow = v & 0b111
    strip(CX, yy, inRow, 3, green=inRow, boxbg=lambda b: BOXC[b], top=(row == 0), labels=lambda b: f"b{b}")
    both = boxes & inRow
    strip(BX, yy, both, 3, green=both, boxbg=lambda b: BOXC[b], top=(row == 0), labels=lambda b: f"b{b}")
    n = bin(inRow).count('1')
    if n == 1 and both:
        entry |= 1 << row
        verdict = rf"one kept box, and it has one column $\Rightarrow$ \texttt{{t[i] |= 1 << {row}}}: row {row} is a single"
    elif n != 1:
        verdict = rf"\texttt{{popcount(inRow)}} $= {n}$ $\Rightarrow$ skip: row {row} has {n} boxes, so at least {n} cells"
    else:
        verdict = r"one kept box, but it has 2 or more columns $\Rightarrow$ skip"
    lab(strip_end(BX, 3) + 0.25, yy + W / 2, verdict, 'west', r'\scriptsize')
    yy -= 0.85
yy -= 0.2
strip(CX, yy, entry, 3, green=entry, boxbg=lambda b: 'white', top=True, labels=lambda b: f"r{b}", all_labels=True)
lab(CX - 0.25, yy + W / 2, r"\texttt{SINGLE\_ROWS[i]} $=$", font=r'\scriptsize')
lab(strip_end(CX, 3) + 0.25, yy + W / 2, rf"\texttt{{{lit(entry, 3)}}}: row 2 is down to one cell (r2c8)", 'west', r'\scriptsize')
yy -= 1.4
section(yy + 0.3, r"Where it is used")
note(-0.3, yy - 0.1, r"\texttt{updateBand}: \ \texttt{unsigned singleRows = SINGLE\_ROWS[PERMUTATION\_UNION[boxCandidates] | ONE\_COLUMN\_BOXES[columns] << 9];}\\"
     r"then \texttt{newSingleRows = singleRows \& openRowsInBand} keeps the rows where the value is not placed yet, and \texttt{ROWS\_CELLS[newSingleRows]} picks out their cells (see the \texttt{ROWS\_CELLS} diagram).", 30)
render('single_rows')

# ======================================================================== ROWS_CELLS
Y = 2.9
header(Y, r"\texttt{ROWS\_CELLS}: a set of a band's rows (3 bits) $\to$ all the cells of those rows",
       r"\textbf{What it is for.} \texttt{SINGLE\_ROWS} says \emph{which rows} are down to one cell, as 3 bits. To place those cells the solver needs them as a 27-bit band mask: "
       r"\texttt{ROWS\_CELLS} widens each row bit to the row's 9 cells, and ANDing with the band's candidates leaves exactly the one cell per row. "
       r"It is \texttt{BOXES\_OF\_ROW} run backwards, and has only 8 entries of 32 bits.")
code(Y - 2.2, ["static constexpr std::array<Mask, 8> ROWS_CELLS = [] {",
               "    std::array<Mask, 8> t{};",
               "    for (int r = 0; r < 8; r++) t[r] = (r & 1 ? 0b111'111'111u : 0) | (r & 2 ? 0b111'111'111u << 9 : 0) | (r & 4 ? 0b111'111'111u << 18 : 0);",
               "    return t;",
               "}();"])
yy = Y - 5.4
r_ex = 0b101
section(yy + 0.6, r"One entry: \texttt{r = 0b101} (rows 0 and 2)")
yy -= 0.9
strip(X, yy, r_ex, 3, labels=lambda b: f"r{b}", green=r_ex, boxbg=lambda b: 'white', all_labels=True)
lab(X - 0.25, yy + W / 2, r"\texttt{r} $=$")
yy -= 1.2
tot = 0
for k, (bitv, sh) in enumerate([(1, 0), (2, 9), (4, 18)]):
    on = r_ex & bitv
    v = (M9 << sh) if on else 0
    tot |= v
    strip(X, yy, v, 27, green=v, boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{r \& {bitv} ? 0b111\textquotesingle{{}}111\textquotesingle{{}}111u{' << ' + str(sh) if sh else ''} : 0}}", font=r'\scriptsize')
    lab(strip_end(X, 27) + 0.25, yy + W / 2, (rf"row {k}'s bit is 1 $\Rightarrow$ row {k}'s 9 cells, bits {sh}--{sh + 8}" if on else rf"row {k}'s bit is 0 $\Rightarrow$ 0"), 'west', r'\scriptsize')
    yy -= 0.8
w(rf"\draw[thick] ({X - 4.0},{yy + 0.62}) -- ({strip_end(X, 27)},{yy + 0.62});")
yy -= 0.05
strip(X, yy, tot, 27, green=tot, boxbg=cell_bg, top=False, labels=cell_label, all_labels=True)
lab(X - 0.25, yy + W / 2, r"OR: \texttt{ROWS\_CELLS[0b101]} $=$", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"\texttt{{{lit(tot, 27)}}}", 'west', r'\scriptsize')
yy -= 1.2
ent = lambda r: rf"\texttt{{ROWS\_CELLS[{lit(r, 3)}] = {lit((M9 if r & 1 else 0) | (M9 << 9 if r & 2 else 0) | (M9 << 18 if r & 4 else 0), 27)}}}"
lab(-0.3, yy + 0.3, r"All 8 entries:", 'west', r'\footnotesize\bfseries')
note(-0.3, yy, r"\\".join(ent(r) for r in range(4)), 15)
note(15.0, yy, r"\\".join(ent(r) for r in range(4, 8)), 15)
yy -= 2.6
section(yy + 0.3, r"Where it is used: \ \texttt{Mask placedCells = bandCells \& ROWS\_CELLS[newSingleRows];} \ in \texttt{updateBand}, with the band of the band rule diagram")
yy -= 1.0
newly = 0b100
rc = M9 << 18
placed = BAND & rc
strip(X, yy, BAND, 27, labels=lambda b: cell_label(b) if BAND >> b & 1 else '', fills=cell_fill, boxbg=cell_bg)
lab(X - 0.25, yy + W / 2, r"\texttt{bandCells}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"after the band rule", 'west', r'\scriptsize')
yy -= 0.8
strip(X, yy, rc, 27, green=rc, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{\& ROWS\_CELLS[0b100]}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"\texttt{newSingleRows = 0b100} from \texttt{SINGLE\_ROWS}: row 2", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 4.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 1.0
strip(X, yy, placed, 27, labels=lambda b: cell_label(b) if placed >> b & 1 else '', fills=cell_fill, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{placedCells} $=$")
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"r2c8: one cell for the one single row; it is then cleared from the other 8 values", 'west', r'\scriptsize')
render('rows_cells')

# ======================================================================== AFTER_PLACING, OTHER_BANDS_AFTER_PLACING, BAND_PEERS share an example cell
CELL = 13                                  # r1c4: row 1, column 4, box 1 of the band
row, col, box = CELL // 9, CELL % 9, CELL % 9 // 3
rowCells = M9 << (row * 9)
boxCells = (0b111 | 0b111 << 9 | 0b111 << 18) << (box * 3)
after = (ALL & ~rowCells & ~boxCells) | 1 << CELL
colMask = (1 | 1 << 9 | 1 << 18) << col
other = ALL & ~colMask
peers = ~after & ALL
assert bin(peers).count('1') == 14

# ---------------------------------------------------------------- AFTER_PLACING
# its own example cell, away from the middle of the band: r2c2, the bottom-right corner of box 0
PLACE_CELL = 20
placeRow, placeCol, placeBox = PLACE_CELL // 9, PLACE_CELL % 9, PLACE_CELL % 9 // 3
placeName = f"r{placeRow}c{placeCol}"
placeRowCells = M9 << (placeRow * 9)
placeBoxCells = (0b111 | 0b111 << 9 | 0b111 << 18) << (placeBox * 3)
placeAfter = (ALL & ~placeRowCells & ~placeBoxCells) | 1 << PLACE_CELL
Y = 2.9
header(Y, r"\texttt{AFTER\_PLACING}: a cell $\to$ what is left of the value's own band after the value is placed there",
       r"\textbf{What it is for.} When the value is placed in a cell, it can no longer go anywhere else in that cell's row or box. "
       r"\texttt{AFTER\_PLACING[cell]} is the band with the cell's row and box cleared, except the cell itself, so one AND does all of it: "
       r"\texttt{valueToBand[digit][band] \&= AFTER\_PLACING[bitIndex]}. \texttt{bitIndex} is the cell\'s bit number 0--26 inside the band. 27 entries of 32 bits.")
code(Y - 2.2, ["static constexpr std::array<Mask, 27> AFTER_PLACING = [] {",
               "    std::array<Mask, 27> t{};",
               "    for (int bitIndex = 0; bitIndex < 27; bitIndex++) {",
               "        int row = bitIndex / 9, box = bitIndex % 9 / 3;",
               "        Mask rowCells = Mask(0b111'111'111) << (row * 9);",
               "        Mask boxCells = (Mask(0b111) | Mask(0b111) << 9 | Mask(0b111) << 18) << (box * 3);",
               "        t[bitIndex] = (ALL_CELLS & ~rowCells & ~boxCells) | Mask(1) << bitIndex;",
               "    }",
               "    return t;",
               "}();"])
yy = Y - 7.4
section(yy + 0.6, rf"One entry: \texttt{{bitIndex = {PLACE_CELL}}}, that is {placeName}: \texttt{{row = {PLACE_CELL} / 9 = {placeRow}}}, \texttt{{box = {PLACE_CELL} \% 9 / 3 = {placeBox}}}")
yy -= 0.9
steps = [(ALL, r"\texttt{ALL\_CELLS}", "all 27 cells", 0, 0),
         (placeRowCells, rf"\texttt{{rowCells = 0b111\textquotesingle{{}}111\textquotesingle{{}}111 << {placeRow * 9}}}", f"row {placeRow}'s 9 cells", 0, 0),
         (placeBoxCells, rf"\texttt{{boxCells = (0b111 | 0b111 << 9 | 0b111 << 18) << {placeBox * 3}}}", f"box {placeBox}'s 9 cells", 0, 0)]
for k, (v, name, why, _, _) in enumerate(steps):
    strip(X, yy, v, 27, fills=lambda b: 'gray!30', boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, name, font=r'\scriptsize')
    lab(strip_end(X, 27) + 0.25, yy + W / 2, why, 'west', r'\scriptsize')
    yy -= 0.85
yy -= 0.3
a1 = ALL & ~placeRowCells & ~placeBoxCells
strip(X, yy, a1, 27, green=a1, red=(placeRowCells | placeBoxCells), boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{ALL\_CELLS \& \textasciitilde{}rowCells \& \textasciitilde{}boxCells}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"red: the row and box, cleared", 'west', r'\scriptsize')
yy -= 0.85
strip(X, yy, 1 << PLACE_CELL, 27, green=1 << PLACE_CELL, boxbg=cell_bg, top=False, labels=lambda b: cell_label(b) if b == PLACE_CELL else '')
lab(X - 0.25, yy + W / 2, rf"\texttt{{| Mask(1) << {PLACE_CELL}}}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"put the cell itself back: the value stays there", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 4.6},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 1.0
strip(X, yy, placeAfter, 27, green=placeAfter, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, rf"\texttt{{AFTER\_PLACING[{PLACE_CELL}]}} $=$", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"\texttt{{{lit(placeAfter, 27)}}}", 'west', r'\scriptsize')
yy -= 0.9
band_grid(X + 1.0, yy - 2.0, {b: ('green!40' if placeAfter >> b & 1 else 'red!22') for b in range(27)}, caption=f'green: still allowed for the value; red: cleared (row {placeRow} and box {placeBox}, except {placeName})')
yy -= 3.1
section(yy + 0.3, r"Where it is used")
note(-0.3, yy - 0.1, r"\texttt{clearPeers}, called by \texttt{place} (clues and guesses) and \texttt{propagate} (naked singles): \ \texttt{state.valueToBand[digit][band] \&= AFTER\_PLACING[bitIndex];}\\"
     r"always next to two \texttt{OTHER\_BANDS\_AFTER\_PLACING} lines for the other two bands. \texttt{BAND\_PEERS} is built from this table.", 30)
render('after_placing')

# ---------------------------------------------------------------- OTHER_BANDS_AFTER_PLACING
Y = 2.9
header(Y, r"\texttt{OTHER\_BANDS\_AFTER\_PLACING}: a cell $\to$ what is left of the value's \emph{other two} bands after it is placed there",
       r"\textbf{What it is for.} A value placed in a cell can no longer go anywhere else in that cell's column, and the column runs through all three bands. "
       r"Inside the cell's own band \texttt{AFTER\_PLACING} already cleared it (the column's other two cells there are in the cell's box). "
       r"In the other two bands the column is not in the cell's row or box, so this second table clears just the column: the same 27-bit entry is ANDed into both other bands. 27 entries of 32 bits.")
code(Y - 2.6, ["static constexpr std::array<Mask, 27> OTHER_BANDS_AFTER_PLACING = [] {",
               "    std::array<Mask, 27> t{};",
               "    for (int bitIndex = 0; bitIndex < 27; bitIndex++) t[bitIndex] = ALL_CELLS & ~((1u | 1u << 9 | 1u << 18) << (bitIndex % 9));",
               "    return t;",
               "}();"])
yy = Y - 5.5
section(yy + 0.6, rf"One entry: \texttt{{bitIndex = {CELL}}} (r1c4): \texttt{{bitIndex \% 9 = {col}}}, column {col}")
yy -= 0.9
c0 = 1 | 1 << 9 | 1 << 18
strip(X, yy, c0, 27, fills=lambda b: 'gray!30', boxbg=cell_bg)
lab(X - 0.25, yy + W / 2, r"\texttt{1u | 1u << 9 | 1u << 18}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"column 0 in all 3 rows", 'west', r'\scriptsize')
yy -= 0.85
strip(X, yy, colMask, 27, fills=lambda b: 'gray!30', newzero=hrz(col), boxbg=cell_bg, top=False, labels=lambda b: f"c{b % 9}" if colMask >> b & 1 else '')
lab(X - 0.25, yy + W / 2, rf"\texttt{{<< {col}}}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"moved to column {col} (hatched 0s came in on the right)", 'west', r'\scriptsize')
yy -= 0.85
strip(X, yy, ALL, 27, fills=lambda b: 'gray!30', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{ALL\_CELLS}", font=r'\scriptsize')
yy -= 0.85
strip(X, yy, other, 27, green=other, red=colMask, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{\& \textasciitilde{}(\ldots)}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"red: column {col}, cleared", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 4.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 1.0
strip(X, yy, other, 27, green=other, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, rf"\texttt{{OTHER\_BANDS\_AFTER\_PLACING[{CELL}]}} $=$", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"\texttt{{{lit(other, 27)}}}", 'west', r'\scriptsize')
yy -= 0.9
band_grid(X + 1.0, yy - 2.0, {b: ('green!40' if other >> b & 1 else 'red!22') for b in range(27)}, caption='either other band: column 4 cleared in all three rows')
yy -= 3.1
section(yy + 0.3, r"Where it is used")
note(-0.3, yy - 0.1, r"\texttt{place} and \texttt{propagate}, for the two bands that are not the cell's:\\"
     r"\texttt{state.valueToBand[digit][otherBand1] \&= OTHER\_BANDS\_AFTER\_PLACING[bitIndex];}\\"
     r"\texttt{state.valueToBand[digit][otherBand2] \&= OTHER\_BANDS\_AFTER\_PLACING[bitIndex];}\\"
     r"\texttt{band == 0 ? 1 : 0} and \texttt{band == 2 ? 1 : 2} are the two other bands: for band 0 they are 1 and 2, for band 1 they are 0 and 2, for band 2 they are 0 and 1.", 30)
render('other_bands_after_placing')

# ---------------------------------------------------------------- BAND_PEERS
Y = 2.9
header(Y, r"\texttt{BAND\_PEERS}: a cell $\to$ its peers inside its own band (its row and box, the cell itself excluded)",
       r"\textbf{What it is for.} A cell's 20 \emph{peers} are the other cells of its row, column and box. 14 of them are in the cell's own band "
       r"(8 in its row, 8 in its box, 2 counted twice: $8 + 8 - 2 = 14$); the other 6 are its column in the other two bands, 3 in each. "
       r"When the solver guesses, it picks the two-candidate cell with the most unsolved peers, and \texttt{peerScore} counts the 14 with this table. "
       r"It is \texttt{AFTER\_PLACING} turned inside out. 27 entries of 32 bits.")
code(Y - 2.5, ["static constexpr std::array<Mask, 27> BAND_PEERS = [] {",
               "    std::array<Mask, 27> t{};",
               "    for (int bitIndex = 0; bitIndex < 27; bitIndex++) t[bitIndex] = ~AFTER_PLACING[bitIndex] & ALL_CELLS;",
               "    return t;",
               "}();"])
yy = Y - 5.6
section(yy + 0.6, rf"One entry: \texttt{{bitIndex = {CELL}}} (r1c4)")
yy -= 0.9
strip(X, yy, after, 27, green=after, boxbg=cell_bg)
lab(X - 0.25, yy + W / 2, rf"\texttt{{AFTER\_PLACING[{CELL}]}}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"everything but the row and box, plus the cell", 'west', r'\scriptsize')
yy -= 0.85
inv = ~after & 0xFFFFFFFF
strip(X, yy, inv & ALL, 27, fills=lambda b: 'gray!30', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{\textasciitilde{}AFTER\_PLACING[13]}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"flip every bit: the row and box, minus the cell (bits 27--31 also become 1)", 'west', r'\scriptsize')
yy -= 0.85
strip(X, yy, ALL, 27, fills=lambda b: 'gray!30', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{\& ALL\_CELLS}", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"clears bits 27--31 again", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 4.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 1.0
strip(X, yy, peers, 27, green=peers, boxbg=cell_bg, top=False, labels=lambda b: cell_label(b) if peers >> b & 1 else '')
lab(X - 0.25, yy + W / 2, rf"\texttt{{BAND\_PEERS[{CELL}]}} $=$", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"\texttt{{{lit(peers, 27)}}}: 14 cells", 'west', r'\scriptsize')
yy -= 0.9
band_grid(X + 1.0, yy - 2.0, {**{b: 'green!40' for b in range(27) if peers >> b & 1}, CELL: 'yellow!70'},
          caption='green: the 14 peers of r1c4 (yellow) inside its band')
yy -= 3.1
section(yy + 0.3, r"Where it is used")
note(-0.3, yy - 0.1, r"\texttt{peerScore}, which scores a guess cell by its unsolved peers: the 14 in the band come from this table, the 6 in the other bands from the cell's column:\\"
     r"\texttt{return std::popcount(state.unsolved[band] \& BAND\_PEERS[bitIndex]) + std::popcount(others);}\\"
     r"\texttt{others} packs \texttt{unsolved[otherBand1] \& column} and \texttt{unsolved[otherBand2] \& column} into one 64-bit word, so both other bands are counted with a single \texttt{popcount}.", 30)
render('band_peers')
