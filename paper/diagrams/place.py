#!/usr/bin/env python3
# place and clearPeers, traced line by line on the first clue of an empty board: a 6 in r7c3, every mask drawn as its
# full bit string in the style of bandrule.py. Writes place.png next to this script.
import os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'tables.py')).read()
exec(src.split('# ======================================================================== ONE_COLUMN_BOXES')[0])

# the example: the value 6 (digit 5) at board row 7, column 3. Not the centre square, so that the row, box, column and
# bands all differ: band 2, row 1 of the band, box 1 (the middle stack), and the other bands are 0 and 1
VALUE, BOARD_ROW, COLUMN = 6, 7, 3
DIGIT = VALUE - 1
BAND = BOARD_ROW // 3
ROW_IN_BAND = BOARD_ROW % 3
BOX = COLUMN // 3
BIT_INDEX = 9 * ROW_IN_BAND + COLUMN
CELL_BIT_MASK = 1 << BIT_INDEX
OTHER1, OTHER2 = (1 if BAND == 0 else 0), (1 if BAND == 2 else 2)
NAME = f"r{BOARD_ROW}c{COLUMN}"
assert (BAND, BIT_INDEX, OTHER1, OTHER2) == (2, 12, 0, 1)

AFTER = (ALL & ~(M9 << 9 * ROW_IN_BAND) & ~((0b111 | 0b111 << 9 | 0b111 << 18) << 3 * BOX)) | CELL_BIT_MASK
OTHER = ALL & ~((1 | 1 << 9 | 1 << 18) << COLUMN)
NOT_CELL = ALL & ~CELL_BIT_MASK
ROWS_OF = lambda b: f"{3 * b}--{3 * b + 2}"
board_label = lambda bit: f"r{BAND * 3 + bit // 9}c{bit % 9}"   # the cell's name on the board, not inside the band


def board_grid(GX, GY, fills, cs=0.42, caption=''):
    """The whole 9 x 9 board, row 0 on top; fills = {(row, col): colour}; bands separated by thick lines."""
    for r in range(9):
        for c in range(9):
            x, y = GX + c * cs, GY + (8 - r) * cs
            w(rf"\fill[{fills.get((r, c), BOXC[c // 3])}] ({x},{y}) rectangle ++({cs},{cs});")
    w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={cs}] (0,0) grid ({9 * cs},{9 * cs});\end{{scope}}")
    w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * cs},{9 * cs});")
    for q in (3, 6):
        w(rf"\draw[thick] ({GX + q * cs},{GY}) -- ++(0,{9 * cs});")
        w(rf"\draw[very thick] ({GX},{GY + q * cs}) -- ++({9 * cs},0);")
    for c in range(9): lab(GX + (c + 0.5) * cs, GY + 9 * cs + 0.16, f"c{c}", 'center', r'\fontsize{5}{6}\selectfont')
    for r in range(9): lab(GX - 0.06, GY + (8.5 - r) * cs, f"r{r}", 'east', r'\fontsize{5}{6}\selectfont')
    for b in range(3): lab(GX + 9 * cs + 0.1, GY + (7.5 - 3 * b) * cs, f"band {b}", 'west', r'\fontsize{5}{6}\selectfont')
    if caption: lab(GX + 4.5 * cs, GY - 0.3, caption, 'center', r'\scriptsize')


def row(yy, value, name, why, n=27, **kw):
    kw.setdefault('boxbg', cell_bg if n == 27 else (lambda b: 'white'))
    strip(X, yy, value, n, **kw)
    lab(X - 0.25, yy + W / 2, name, font=r'\scriptsize')
    lab(strip_end(X, n) + 0.25, yy + W / 2, why, 'west', r'\scriptsize')


def rule(yy):
    w(rf"\draw[thick] ({X - 5.2},{yy}) -- ({strip_end(X, 27)},{yy});")


# ---------------------------------------------------------------- header and code
Y = 2.9
header(Y, r"\texttt{place}: put a value in a cell, and clear it from everywhere else the cell can see",
       rf"\textbf{{The example.}} The first clue of a puzzle: a {VALUE} in {NAME} (board row {BOARD_ROW}, column {COLUMN}), so \texttt{{digit = {DIGIT}}} (values are 0--8 in the code). "
       r"The board is empty before it, so every mask starts as \texttt{ALL\_CELLS}. "
       r"\texttt{place} is called by \texttt{load} for each clue and by \texttt{search} for each guess; it changes only the masks below, "
       r"and everything that follows from them (band rule, stack rule, singles) waits for the next \texttt{propagate}.")
code(Y - 2.75, ["void place(State &state, int digit, int band, Mask cellBitMask) {",
               "    for (int other = 0; other < 9; other++) state.valueToBand[other][band] &= ~cellBitMask;",
               "    state.valueToBand[digit][band] |= cellBitMask;",
               "    clearPeers(state, digit, band, cellBitMask);",
               "}",
               "",
               "void clearPeers(State &state, int digit, int band, Mask cellBitMask) {",
               "    int bitIndex = std::countr_zero(cellBitMask);  // the cell's bit number, 0-26",
               "    int otherBand1 = band == 0 ? 1 : 0, otherBand2 = band == 2 ? 1 : 2;  // the two bands that are not band",
               "    int boardRow = band * 3 + bitIndex / 9;  // the cell's row on the board, 0-8",
               "    state.valueToBand[digit][band] &= AFTER_PLACING[bitIndex];",
               "    state.valueToBand[digit][otherBand1] &= OTHER_BANDS_AFTER_PLACING[bitIndex];",
               "    state.valueToBand[digit][otherBand2] &= OTHER_BANDS_AFTER_PLACING[bitIndex];",
               "    state.unsolved[band] &= ~cellBitMask;",
               "    state.openRows[digit] &= ~(1u << boardRow);",
               "}"])
board_grid(24.0, Y - 7.8, {(BOARD_ROW, COLUMN): 'yellow!70'}, caption=f'the cell: {NAME}, in band {BAND}')

# ---------------------------------------------------------------- the arguments
yy = Y - 10.0
section(yy + 0.6, rf"The arguments: \texttt{{digit = {DIGIT}}} (the value {VALUE}), \texttt{{band = {BAND}}} (board rows {ROWS_OF(BAND)}), and \texttt{{cellBitMask}}, the band with only the cell's bit set")
yy -= 0.9
row(yy, CELL_BIT_MASK, r"\texttt{cellBitMask} $=$", rf"\texttt{{{lit(CELL_BIT_MASK, 27)}}}: row {ROW_IN_BAND} of the band, column {COLUMN}",
    labels=board_label, fills=lambda b: 'yellow!70')
yy -= 0.75
note(X - 5.4, yy, rf"\texttt{{bitIndex = countr\_zero(cellBitMask) = {BIT_INDEX}}} \ ({BIT_INDEX} zeros below the 1)\\"
     rf"\texttt{{otherBand1 = {OTHER1}}}, \ \texttt{{otherBand2 = {OTHER2}}} \ (\texttt{{band}} is {BAND})\\"
     rf"\texttt{{boardRow = {BAND} * 3 + {BIT_INDEX} / 9 = {BAND * 3} + {BIT_INDEX // 9} = {BOARD_ROW}}} \ (integer division: \texttt{{{BIT_INDEX} / 9 = {BIT_INDEX // 9}}}, the row inside the band)", 27)
yy -= 0.8

# ---------------------------------------------------------------- place, line 1
yy -= 1.55
section(yy + 0.6, rf"\texttt{{place}}, line 1: \ \texttt{{valueToBand[other][{BAND}] \&= \textasciitilde{{}}cellBitMask}} for all 9 values: no value can go in the cell any more")
yy -= 0.9
row(yy, ALL, rf"\texttt{{valueToBand[other][{BAND}]}}", "before: every cell (the empty board)")
yy -= 0.75
row(yy, NOT_CELL, r"\texttt{\& \textasciitilde{}cellBitMask}", "every bit except the cell's", top=False)
rule(yy - 0.2)
yy -= 0.95
row(yy, NOT_CELL, rf"\texttt{{valueToBand[other][{BAND}]}} $=$", "after: the cell is gone; the same for each of the 9 values", top=False, red=CELL_BIT_MASK,
    labels=lambda b: board_label(b) if b == BIT_INDEX else '')

# ---------------------------------------------------------------- place, line 2
yy -= 1.4
section(yy + 0.6, rf"\texttt{{place}}, line 2: \ \texttt{{valueToBand[{DIGIT}][{BAND}] |= cellBitMask}}: give the cell back to the {VALUE} only")
yy -= 0.9
row(yy, ALL, rf"\texttt{{valueToBand[{DIGIT}][{BAND}]}} $=$", f"the {VALUE} has the cell again: it is now the cell's only value", green=CELL_BIT_MASK,
    labels=lambda b: board_label(b) if b == BIT_INDEX else '')

# ---------------------------------------------------------------- clearPeers: own band
yy -= 1.4
section(yy + 0.6, rf"\texttt{{clearPeers}}: \ \texttt{{valueToBand[{DIGIT}][{BAND}] \&= AFTER\_PLACING[{BIT_INDEX}]}}: no other {VALUE} in the cell's row or box")
yy -= 0.9
row(yy, ALL, rf"\texttt{{valueToBand[{DIGIT}][{BAND}]}}", "from line 2")
yy -= 0.75
row(yy, AFTER, rf"\texttt{{\& AFTER\_PLACING[{BIT_INDEX}]}}", f"row {ROW_IN_BAND} and box {BOX} cleared, except the cell itself", top=False, fills=lambda b: 'gray!30')
rule(yy - 0.2)
yy -= 0.95
row(yy, AFTER, rf"\texttt{{valueToBand[{DIGIT}][{BAND}]}} $=$", rf"\texttt{{{lit(AFTER, 27)}}}", top=False, green=AFTER, red=ALL & ~AFTER)

# ---------------------------------------------------------------- clearPeers: other bands
yy -= 1.4
section(yy + 0.6, rf"\texttt{{clearPeers}}: \ \texttt{{valueToBand[{DIGIT}][otherBand1]}} and \texttt{{[otherBand2] \&= OTHER\_BANDS\_AFTER\_PLACING[{BIT_INDEX}]}}: no other {VALUE} in column {COLUMN}")
yy -= 0.9
row(yy, ALL, rf"\texttt{{valueToBand[{DIGIT}][{OTHER1}]}}", rf"band {OTHER1} (rows {ROWS_OF(OTHER1)}) = \texttt{{otherBand1}}, from the empty board")
yy -= 0.75
row(yy, OTHER, rf"\texttt{{\& OTHER\_BANDS\_AFTER\_PLACING[{BIT_INDEX}]}}", f"column {COLUMN} cleared in all three rows", top=False, fills=lambda b: 'gray!30')
rule(yy - 0.2)
yy -= 0.95
row(yy, OTHER, rf"\texttt{{valueToBand[{DIGIT}][{OTHER1}]}} $=$", rf"\texttt{{{lit(OTHER, 27)}}}; band {OTHER2} (\texttt{{otherBand2}}) gets exactly the same", top=False, green=OTHER, red=ALL & ~OTHER)

# ---------------------------------------------------------------- clearPeers: unsolved, openRows
yy -= 1.4
section(yy + 0.6, rf"\texttt{{clearPeers}}: \ the cell is solved, and the {VALUE} is done in board row {BOARD_ROW}")
yy -= 0.9
row(yy, NOT_CELL, rf"\texttt{{unsolved[{BAND}] \&= \textasciitilde{{}}cellBitMask}} $\to$", "the cell is no longer unsolved", red=CELL_BIT_MASK,
    labels=lambda b: board_label(b) if b == BIT_INDEX else '')
yy -= 1.15
OPEN_AFTER = M9 & ~(1 << BOARD_ROW)
row(yy, M9, rf"\texttt{{openRows[{DIGIT}]}}", f"before: the {VALUE} is not placed in any board row", n=9, labels=lambda b: f"r{b}", all_labels=True)
yy -= 0.95
row(yy, OPEN_AFTER, r"\texttt{\& \textasciitilde{}(1u << boardRow)}", rf"\texttt{{1u << {BOARD_ROW}}}, flipped: every row except row {BOARD_ROW}", n=9, top=False)
rule(yy - 0.2)
yy -= 0.95
row(yy, OPEN_AFTER, rf"\texttt{{openRows[{DIGIT}]}} $=$", rf"\texttt{{{lit(OPEN_AFTER, 9)}}}: \texttt{{updateBand}} will not place a {VALUE} in row {BOARD_ROW} again", n=9, top=False,
    red=1 << BOARD_ROW, labels=lambda b: f'r{BOARD_ROW}' if b == BOARD_ROW else '')

# ---------------------------------------------------------------- the result on the board
yy -= 1.5
section(yy + 0.6, r"The result on the board")
yy -= 4.6
placed = {}
for r in range(9):
    for c in range(9):
        if (r, c) == (BOARD_ROW, COLUMN): placed[(r, c)] = 'yellow!70'
        elif r == BOARD_ROW or c == COLUMN or (r // 3, c // 3) == (BAND, BOX): placed[(r, c)] = 'red!22'
        else: placed[(r, c)] = 'green!40'
board_grid(1.0, yy, placed, caption=rf'where a {VALUE} can still go: \texttt{{valueToBand[{DIGIT}][0..2]}}')
other = {(r, c): ('red!22' if (r, c) == (BOARD_ROW, COLUMN) else 'green!40') for r in range(9) for c in range(9)}
board_grid(8.5, yy, other, caption=r'where any other value can go, e.g.\ \texttt{valueToBand[0][0..2]} (the 1s)')
note(15.6, yy + 3.6, rf"yellow: the {VALUE} placed in {NAME} \\ red: cleared by \texttt{{place}} \\ green: still allowed \\[4pt]"
     rf"The {VALUE} lost the cell's 20 peers: its row (8 cells), the rest of its box (6 more) and its column in the other two bands (6 more). "
     rf"Every other value lost only the cell itself. The 11 masks that changed (band {BAND} of all 9 values, and bands {OTHER1} and {OTHER2} of the {VALUE}) now differ from \texttt{{checked}}, "
     r"so the next \texttt{update} runs the rules on them.", 13)
render('place')
