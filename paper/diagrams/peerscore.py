#!/usr/bin/env python3
# peerScore, traced on one real call: the cell chooseGuessCell picks in chooseguesscell.py (magictour puzzle 96, three
# guesses deep). Every mask is drawn as its full bit string, high bit on the left, including the 64-bit word that packs
# two bands. The code shown is read from fastbandsolver.hpp. Writes peerscore.png next to this script.
from search_common import *

J = DATA['guess']
state = State(J)
BAND, CELL_MASK = J['result'][0], J['result'][1]
BIT = countr_zero(CELL_MASK)
NAME = cell_name(BAND, BIT)

# ---------------------------------------------------------------- the code, step by step, in the same order
COLUMN_BIT = 1 << (BIT % 9)
COLUMN = column_cells(COLUMN_BIT)
OTHER1 = 1 if BAND == 0 else 0
OTHER2 = 1 if BAND == 2 else 2
LOW = state.unsolved[OTHER1] & COLUMN
HIGH = state.unsolved[OTHER2] & COLUMN
OTHERS = LOW | HIGH << 32
PEERS = band_peers(BIT)
IN_BAND = state.unsolved[BAND] & PEERS
SCORE = popcount(IN_BAND) + popcount(OTHERS)
parts = peer_score_parts(state, BAND, BIT)
assert (parts['others'], parts['inBand'], parts['score']) == (OTHERS, IN_BAND, SCORE)
assert [BAND, BIT, SCORE] in J['scores']
assert popcount(PEERS) == 14 and popcount(COLUMN) == 3

# ---------------------------------------------------------------- drawing
Y = 2.9
header(Y, r"\texttt{peerScore}: how many of a cell's 20 peers are still unsolved",
       r"\textbf{What it is for.} \texttt{chooseGuessCell} and \texttt{fewestCandidatesCell} use it to rank cells: guessing a cell with many open peers removes the most candidates. "
       r"A cell's 20 peers are the other cells of its row, column and box. 14 of them are in its own band (its row and its box, which also holds its column's other two cells in the band): that is \texttt{BAND\_PEERS[bitIndex]}. "
       r"The other 6 are its column in the other two bands. At guessing time every unsolved cell has two or more candidates, so this counts the peers still open.\\[3pt]"
       rf"\textbf{{The call drawn here}} is \texttt{{peerScore(state, {BAND}, {BIT})}}, for {NAME}, the cell \texttt{{chooseGuessCell}} picks in its diagram (magictour puzzle {DATA['index'] + 1}, {J['depth']} guesses deep).")
code(Y - 3.4, source('FastBandSolver::peerScore('), 20)

GX, GY, CS = 23.2, Y - 10.0, 0.68
fills, marks = {}, {}
for band in range(3):
    for bit in range(27):
        rc = (3 * band + bit // 9, bit % 9)
        unsolved = state.unsolved[band] >> bit & 1
        if band == BAND and PEERS >> bit & 1: fills[rc] = 'blue!30' if unsolved else 'blue!7'
        elif band != BAND and COLUMN >> bit & 1: fills[rc] = 'orange!45' if unsolved else 'orange!10'
        if unsolved and rc in fills: marks[rc] = r'$\bullet$'
fills[(3 * BAND + BIT // 9, BIT % 9)] = 'green!40'
marks[(3 * BAND + BIT // 9, BIT % 9)] = r'$\star$'
board(GX, GY, state, CS, fills=fills, marks=marks, show_candidates=False)
note(GX - 1.2, GY - 0.25,
     rf"$\star$ {NAME}. \colorbox{{blue!30}}{{Blue}}: its 14 peers in band {BAND} (\texttt{{BAND\_PEERS}}), \colorbox{{orange!45}}{{orange}}: its 6 column peers in bands {OTHER1} and {OTHER2}. "
     rf"Dark with $\bullet$: unsolved, so counted; pale with a digit: solved. {popcount(IN_BAND)} $+$ {popcount(OTHERS)} $= {SCORE}$.", 8.4)

# ---------------------------------------------------------------- 1. column
yy = Y - 12.4
section(yy, rf"1. \ \texttt{{Mask column = columnCells(Mask(1) << (bitIndex \% 9));}} \quad \texttt{{bitIndex \% 9}} $= {BIT} \bmod 9 = {BIT % 9}$, the cell's column")
yy -= 1.4
strip(X, yy, COLUMN_BIT, 27, boxbg=cell_bg, top=True, fills=lambda bit: 'orange!45', labels=lambda bit: f"c{bit}")
lab(X - 0.25, yy + W / 2, rf"\texttt{{Mask(1) << {BIT % 9}}}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"one bit, in row 0's column", 'west', r'\scriptsize')
yy -= 0.85
strip(X, yy, COLUMN, 27, boxbg=cell_bg, top=False, fills=lambda bit: 'orange!45', labels=lambda bit: f"row {bit // 9} c{bit % 9}")
lab(X - 0.25, yy + W / 2, r"\texttt{column = columnCells(...)}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(COLUMN, 27)}}}$: \texttt{{x | x << 9 | x << 18}}, the column in all three rows of a band", 'west', r'\scriptsize')
yy -= 1.2

# ---------------------------------------------------------------- 2. the other bands
section(yy, rf"2. \ \texttt{{int otherBand1 = band == 0 ? 1 : 0, otherBand2 = band == 2 ? 1 : 2;}} \quad \texttt{{band}} $= {BAND}$, so \texttt{{otherBand1}} $= {OTHER1}$ and \texttt{{otherBand2}} $= {OTHER2}$")
note(-0.3, yy - 0.45, r"Band 0 $\to$ bands 1 and 2; band 1 $\to$ 0 and 2; band 2 $\to$ 0 and 1.", 30)
yy -= 1.5

# ---------------------------------------------------------------- 3. the packed word
section(yy, r"3. \ \texttt{uint64\_t others = uint64\_t(state.unsolved[otherBand1] \& column) | uint64\_t(state.unsolved[otherBand2] \& column) << 32;}")
note(-0.3, yy - 0.45,
     r"Each band is 27 bits, so two of them fit side by side in one 64-bit word, the second starting at bit 32. Then one \texttt{popcount} counts both bands' column peers at once: two popcounts in all instead of three.", 30)
yy -= 1.9
for k, (ob, part) in enumerate(((OTHER1, LOW), (OTHER2, HIGH))):
    strip(X, yy, state.unsolved[ob], 27, labels=band_label(ob), fills=lambda bit: 'gray!30', boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{state.unsolved[{ob}]}}")
    yy -= 0.8
    strip(X, yy, COLUMN, 27, fills=lambda bit: 'orange!45', boxbg=cell_bg, top=False)
    lab(X - 0.25, yy + W / 2, r"\texttt{\& column}")
    w(rf"\draw[thick] ({X - 3.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
    yy -= 0.95
    strip(X, yy, part, 27, labels=band_label(ob), fills=lambda bit: 'orange!45', boxbg=cell_bg, top=False)
    lab(X - 0.25, yy + W / 2, rf"\texttt{{state.unsolved[{ob}] \& column}}")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(part, 27)}}}$: {popcount(part)} of the 3 column cells in band {ob} unsolved", 'west', r'\scriptsize')
    yy -= 1.05
G64 = [(5, 0.12)] + groups27(0.05, 0.16)[:-1] + [(3, 0.5)] + [(5, 0.12)] + groups27(0.05, 0.16)
BW = 0.33
yy -= 0.2
lab(-0.3, yy + 0.75, r"the 64-bit word, bit 63 on the left:", 'west', r'\scriptsize')
_, end64 = bit_strip(1.6, yy, LOW, G64, fills=lambda bit: 'orange!45', top=True, bw=BW, labels=band_label(OTHER1))
lab(end64 + 0.2, yy + BW / 2, rf"\texttt{{uint64\_t(state.unsolved[{OTHER1}] \& column)}}: bits 0--26", 'west', r'\scriptsize')
yy -= 0.75
bit_strip(1.6, yy, HIGH << 32, G64, fills=lambda bit: 'orange!45', top=False, bw=BW, labels=lambda bit: cell_name(OTHER2, bit - 32) if bit >= 32 else '')
lab(end64 + 0.2, yy + BW / 2, rf"\texttt{{uint64\_t(state.unsolved[{OTHER2}] \& column) << 32}}: bits 32--58", 'west', r'\scriptsize')
w(rf"\draw[thick] (1.4,{yy - 0.25}) -- ({end64},{yy - 0.25});")
yy -= 0.85
pos, _ = bit_strip(1.6, yy, OTHERS, G64, fills=lambda bit: 'orange!45', top=False, bw=BW,
                   labels=lambda bit: cell_name(OTHER2, bit - 32) if bit >= 32 else cell_name(OTHER1, bit))
lab(end64 + 0.2, yy + BW / 2, rf"\texttt{{others}}: \texttt{{std::popcount(others)}} $= {popcount(OTHERS)}$", 'west', r'\scriptsize')
for lo, hi, t in ((59, 63, 'always 0'), (27, 31, 'always 0')):
    x0, x1 = pos[hi], pos[lo] + BW
    w(rf"\draw[decorate,decoration={{brace,amplitude=3pt,mirror}}] ({x0},{yy - 0.3}) -- ({x1},{yy - 0.3}) node[midway,below=2pt,font=\fontsize{{5}}{{6}}\selectfont] {{{t}}};")
for lo, hi, t in ((32, 58, rf"band {OTHER2}"), (0, 26, rf"band {OTHER1}")):
    x0, x1 = pos[hi], pos[lo] + BW
    w(rf"\draw[decorate,decoration={{brace,amplitude=3pt,mirror}}] ({x0},{yy - 0.3}) -- ({x1},{yy - 0.3}) node[midway,below=2pt,font=\fontsize{{5}}{{6}}\selectfont] {{{t}}};")
yy -= 1.5

# ---------------------------------------------------------------- 4. the own band
section(yy, rf"4. \ \texttt{{std::popcount(state.unsolved[band] \& BAND\_PEERS[bitIndex])}} \quad \texttt{{BAND\_PEERS[{BIT}]}}: {NAME}'s row and box in band {BAND}, without the cell")
yy -= 1.4
strip(X, yy, state.unsolved[BAND], 27, labels=band_label(BAND), fills=lambda bit: 'gray!30', boxbg=cell_bg, top=True)
lab(X - 0.25, yy + W / 2, rf"\texttt{{state.unsolved[{BAND}]}}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(state.unsolved[BAND], 27)}}}$", 'west', r'\scriptsize')
yy -= 0.8
strip(X, yy, PEERS, 27, labels=band_label(BAND), fills=lambda bit: 'blue!30', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, rf"\texttt{{\& BAND\_PEERS[{BIT}]}}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(PEERS, 27)}}}$: 14 cells", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 3.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 0.95
strip(X, yy, IN_BAND, 27, labels=band_label(BAND), fills=lambda bit: 'blue!30', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"unsolved peers in the band")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(IN_BAND, 27)}}}$: \texttt{{popcount}} $= {popcount(IN_BAND)}$", 'west', r'\scriptsize')
yy -= 1.3

# ---------------------------------------------------------------- 5. the sum
section(yy, rf"5. \ \texttt{{return}} ${popcount(IN_BAND)} + {popcount(OTHERS)} = {SCORE}$")
note(-0.3, yy - 0.45,
     rf"{NAME} has {SCORE} unsolved peers: {popcount(IN_BAND)} in its own band and {popcount(OTHERS)} in its column in the other two. This is the {SCORE} in red on {NAME} in the \texttt{{chooseGuessCell}} diagram.", 30)

render('peerscore')
