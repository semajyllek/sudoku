#!/usr/bin/env python3
# updateBand, traced step by step on one real call, every mask drawn as its full bit string in the style of
# bandrule.py: the call updateBand<0>(state, 5) (the value 6 in band 0) while solving magictour puzzle 96, the same
# call as the paper's UpdateBand figure. All three steps fire on it: the band rule removes three cells, the stack rule
# removes four cells from band 1, and one row single is placed. Writes updateband.png next to this script.
import os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'tables.py')).read()
exec(src.split('# ======================================================================== ONE_COLUMN_BOXES')[0])

# ---------------------------------------------------------------- the real state, from paper/figs/dump.cpp
PUZZLE = "4.21......5.....78...3......7..5...6......1.....4.........67.5.2.....4..3........"
VALUE_TO_BAND = [  # [digit][band], just before the call
    [0b110_000_000_000_000_101_000_001_000, 0b000_110_111_001_000_000_000_100_101, 0b110_110_110_110_110_110_100_000_111],
    [0b111_110_000_001_111_000_000_000_100, 0b111_110_010_110_110_010_011_101_000, 0b111_111_000_000_000_001_101_001_000],
    [0b000_001_000_001_000_100_111_000_010, 0b111_110_110_110_110_110_011_100_100, 0b000_000_001_000_110_000_101_000_000],
    [0b110_000_000_000_110_000_000_000_001, 0b000_001_000_110_000_110_010_000_100, 0b000_110_000_001_000_000_000_000_110],
    [0b101_100_000_000_000_010_101_100_000, 0b101_000_001_100_000_001_000_010_000, 0b000_001_100_000_001_100_010_000_000],
    [0b011_000_110_001_001_101_011_000_010, 0b000_100_111_000_100_111_100_000_000, 0b011_000_110_010_000_110_000_010_000],
    [0b000_000_001_010_000_000_000_010_000, 0b101_000_000_000_001_000_000_000_010, 0b101_000_100_100_000_100_000_100_000],
    [0b000_110_110_100_000_000_000_100_010, 0b011_110_111_010_110_111_011_101_101, 0b011_111_110_010_111_110_001_001_111],
    [0b111_110_110_001_111_101_111_100_010, 0b111_110_111_110_110_111_011_101_101, 0b111_111_110_110_111_110_101_001_111]]
CHECKED_5 = [0b011_100_111_001_101_101_011_100_010, 0b000_100_111_000_100_111_100_000_000, 0b011_000_110_010_000_110_000_010_000]
OPEN_ROWS_5 = 0b110_110_111
UNSOLVED = [0b111_110_110_001_111_101_111_100_010, 0b111_110_111_110_110_111_011_101_101, 0b111_111_110_110_111_110_101_001_111]
# what the real call left behind, to check the Python below against
EXPECTED_5 = [0b011_000_110_000_001_000_011_000_010, 0b000_100_001_000_100_001_100_000_000, 0b011_000_110_010_000_110_000_010_000]
EXPECTED_1_0 = 0b111_110_000_001_110_000_000_000_100
EXPECTED_8_0 = 0b111_110_110_001_110_101_111_100_010
EXPECTED_OPEN_ROWS_5 = 0b110_110_101
EXPECTED_UNSOLVED_0 = 0b111_110_110_001_110_101_111_100_010

DIGIT, VALUE, B = 5, 6, 0


# ---------------------------------------------------------------- the code, step by step, in the same order
def band_columns(m): return (m | m >> 9 | m >> 18) & M9
def column_cells(c): return c | c << 9 | c << 18
def one_column_boxes(c): return sum(1 << box for box in range(3) if bin((c >> (box * 3)) & 0b111).count('1') == 1)
def single_rows(i):
    kept, boxes, t = i & M9, i >> 9, 0
    for row in range(3):
        inRow = (kept >> (row * 3)) & 0b111
        if bin(inRow).count('1') == 1 and boxes & inRow: t |= 1 << row
    return t
def rows_cells(r): return (M9 if r & 1 else 0) | (M9 << 9 if r & 2 else 0) | (M9 << 18 if r & 4 else 0)

state = [m[:] for m in VALUE_TO_BAND]
checked5 = CHECKED_5[:]

# step 1: read
START = state[DIGIT][B]
LAST_CHECKED = checked5[B]
# step 2: band rule
ROWS = [START & M9, (START >> 9) & M9, START >> 18]
ROW_BOXES = [boxes_of_row(r) for r in ROWS]
BOX_CANDIDATES = ROW_BOXES[0] | ROW_BOXES[1] << 3 | ROW_BOXES[2] << 6
POSSIBLE = possible(BOX_CANDIDATES)
BAND_CELLS = START & POSSIBLE
assert BAND_CELLS != 0
state[DIGIT][B] = checked5[B] = BAND_CELLS
# step 3: stack rule
COLUMNS = band_columns(BAND_CELLS)
OLD_COLUMNS = band_columns(LAST_CHECKED)
assert COLUMNS != OLD_COLUMNS
BEFORE_STACK = state[DIGIT][:]
STACK_COLUMNS = [band_columns(m) for m in state[DIGIT]]
KEPT_COLUMNS = [0, 0, 0]
for shift in (0, 3, 6):
    columnCandidates = sum(((STACK_COLUMNS[b] >> shift) & 0b111) << (3 * b) for b in range(3))
    kept = permutation_union(columnCandidates)
    for b in range(3): KEPT_COLUMNS[b] |= ((kept >> (3 * b)) & 0b111) << shift
for b in range(3): state[DIGIT][b] &= column_cells(KEPT_COLUMNS[b])
AFTER_STACK = state[DIGIT][:]
# step 4: row singles
KEPT_BOXES = permutation_union(BOX_CANDIDATES)
ONE_COLUMN = one_column_boxes(COLUMNS)
SINGLE_INDEX = KEPT_BOXES | ONE_COLUMN << 9
SINGLE = single_rows(SINGLE_INDEX)
OPEN_IN_BAND = (OPEN_ROWS_5 >> (B * 3)) & 0b111
NEW_SINGLE = SINGLE & OPEN_IN_BAND
assert NEW_SINGLE != 0
PLACED = BAND_CELLS & rows_cells(NEW_SINGLE)
DIGIT_MASK_NOW = state[DIGIT][B]
BEFORE_SINGLES = [state[o][B] for o in range(9)]
for o in range(9): state[o][B] &= ~PLACED
state[DIGIT][B] = DIGIT_MASK_NOW
unsolved0 = UNSOLVED[B] & ~PLACED
openRows5 = OPEN_ROWS_5 & ~(NEW_SINGLE << (B * 3))

assert state[DIGIT] == EXPECTED_5 and state[1][0] == EXPECTED_1_0 and state[8][0] == EXPECTED_8_0
assert openRows5 == EXPECTED_OPEN_ROWS_5 and unsolved0 == EXPECTED_UNSOLVED_0
assert checked5 == [EXPECTED_5[0], CHECKED_5[1], CHECKED_5[2]]

PLACED_BIT = PLACED.bit_length() - 1
PLACED_NAME = f"r{PLACED_BIT // 9}c{PLACED_BIT % 9}"
LOSERS = [o for o in range(9) if o != DIGIT and BEFORE_SINGLES[o] & PLACED]
assert (PLACED_NAME, LOSERS) == ("r1c3", [1, 8])
BAND_RULE_REMOVED = START & ~BAND_CELLS
STACK_REMOVED = [BEFORE_STACK[b] & ~AFTER_STACK[b] for b in range(3)]
assert STACK_REMOVED[0] == 0 and STACK_REMOVED[2] == 0 and STACK_REMOVED[1] != 0
CHANGED_COLUMNS = OLD_COLUMNS & ~COLUMNS
names = lambda m, band=0: ", ".join(f"r{band * 3 + b // 9}c{b % 9}" for b in range(27) if m >> b & 1)


STACK_REMOVED_COLUMNS = [STACK_COLUMNS[b] & ~KEPT_COLUMNS[b] for b in range(3)]
STACK_NOTE = (r"\texttt{stackRule} pairs each stack's three columns one to one with the three bands (the band rule turned sideways), and can shrink all three of the value's bands. "
              r"Here, in stack 0 (columns 0--2), bands 0 and 2 can each use only c1 and c2, so between them they take both, and band 1 must use c0: it loses c1 and c2. "
              r"Stacks 1 and 2 still fit with every column they have (see \texttt{stackrule.png} for the lookup):")
assert STACK_COLUMNS[0] >> 0 & 0b111 == 0b110 and STACK_COLUMNS[2] >> 0 & 0b111 == 0b110 and STACK_REMOVED_COLUMNS == [0, 0b110, 0]

# ---------------------------------------------------------------- drawing helpers
def board_grid(GX, GY, fills, cs=0.42, caption='', digits=None):
    """The whole 9 x 9 board, row 0 on top; fills = {(row, col): colour}; bands separated by thick lines."""
    for r in range(9):
        for c in range(9):
            x, y = GX + c * cs, GY + (8 - r) * cs
            w(rf"\fill[{fills.get((r, c), BOXC[c // 3])}] ({x},{y}) rectangle ++({cs},{cs});")
            if digits and digits.get((r, c)):
                w(rf"\node[font=\scriptsize\bfseries] at ({x + cs / 2},{y + cs / 2}) {{{digits[(r, c)]}}};")
    w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={cs}] (0,0) grid ({9 * cs},{9 * cs});\end{{scope}}")
    w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * cs},{9 * cs});")
    for q in (3, 6):
        w(rf"\draw[thick] ({GX + q * cs},{GY}) -- ++(0,{9 * cs});")
        w(rf"\draw[very thick] ({GX},{GY + q * cs}) -- ++({9 * cs},0);")
    for c in range(9): lab(GX + (c + 0.5) * cs, GY + 9 * cs + 0.16, f"c{c}", 'center', r'\fontsize{5}{6}\selectfont')
    for r in range(9): lab(GX - 0.06, GY + (8.5 - r) * cs, f"r{r}", 'east', r'\fontsize{5}{6}\selectfont')
    for b in range(3): lab(GX + 9 * cs + 0.1, GY + (7.5 - 3 * b) * cs, f"band {b}", 'west', r'\fontsize{5}{6}\selectfont')
    if caption: lab(GX + 4.5 * cs, GY - 0.3, caption, 'center', r'\scriptsize')


def row(yy, value, name, why, n=27, x=None, **kw):
    x = X if x is None else x
    kw.setdefault('boxbg', cell_bg if n == 27 else (lambda b: 'white'))
    strip(x, yy, value, n, **kw)
    lab(x - 0.25, yy + W / 2, name, font=r'\scriptsize')
    lab(strip_end(x, n) + 0.25, yy + W / 2, why, 'west', r'\scriptsize')


def rule(yy, n=27, x=None):
    x = X if x is None else x
    w(rf"\draw[thick] ({X - 5.2},{yy}) -- ({strip_end(x, n)},{yy});")


band_label = lambda band: (lambda bit: f"r{band * 3 + bit // 9}c{bit % 9}")
box_label = lambda b: f"r{b // 3}b{b % 3}"   # bit row * 3 + box of a 3 x 3 table
CLUES = {(k // 9, k % 9): PUZZLE[k] for k in range(81) if PUZZLE[k] != '.'}


def six_board(masks, extra=None):
    """Where the 6 can go: green for a candidate in an unsolved cell, yellow for a placed 6."""
    fills = {(r, c): 'white' for r in range(9) for c in range(9)}
    for band in range(3):
        for bit in range(27):
            r, c = band * 3 + bit // 9, bit % 9
            if masks[band] >> bit & 1: fills[(r, c)] = 'green!40' if UNSOLVED[band] >> bit & 1 else 'yellow!70'
    fills.update(extra or {})
    return fills


# ---------------------------------------------------------------- header and code
Y = 2.9
header(Y, r"\texttt{updateBand<B>(state, digit)}: the band rule, the stack rule and row singles, for one value in one band",
       rf"\textbf{{The example.}} A real call: \texttt{{updateBand<0>(state, {DIGIT})}}, the value {VALUE} in band 0, while solving magictour puzzle 96, "
       r"the same call as the paper's \textsc{UpdateBand} figure. All three steps fire on it. "
       r"\texttt{update} calls \texttt{updateBand} on a (value, band) only when its mask differs from \texttt{checked}; "
       r"it returns false if the value has no way left to fit in the band (a contradiction), true otherwise. "
       r"How the band rule's table and the stack rule work inside is in \texttt{bandrule.png} and \texttt{stackrule.png}; here each step is shown on the masks it reads and writes.")
code(Y - 2.75, ["template <int B> bool updateBand(State &state, int digit) {",
                "    Mask bandCells = state.valueToBand[digit][B];",
                "    Mask lastChecked = state.checked[digit][B];",
                "",
                "    int boxCandidates = BOXES_OF_ROW[bandCells & 0b111'111'111]               // row 0's boxes, bits 0-2",
                "                      | BOXES_OF_ROW[(bandCells >> 9) & 0b111'111'111] << 3  // row 1's boxes, bits 3-5",
                "                      | BOXES_OF_ROW[bandCells >> 18] << 6;                  // row 2's boxes, bits 6-8",
                "    bandCells &= POSSIBLE_CELLS[boxCandidates];",
                "    if (!bandCells) return false;",
                "    state.valueToBand[digit][B] = state.checked[digit][B] = bandCells;",
                "",
                "    Mask columns = bandColumns(bandCells);",
                "    if (columns != bandColumns(lastChecked)) stackRule(state, digit);",
                "",
                "    unsigned singleRows = SINGLE_ROWS[PERMUTATION_UNION[boxCandidates] | ONE_COLUMN_BOXES[columns] << 9];",
                "    unsigned openRowsInBand = (state.openRows[digit] >> (B * 3)) & 0b111;",
                "    unsigned newSingleRows = singleRows & openRowsInBand;",
                "    if (newSingleRows) {",
                "        Mask placedCells = bandCells & ROWS_CELLS[newSingleRows];  // one cell per new single row",
                "        Mask digitMaskNow = state.valueToBand[digit][B];",
                "        for (int other = 0; other < 9; other++) state.valueToBand[other][B] &= ~placedCells;",
                "        state.valueToBand[digit][B] = digitMaskNow;",
                "        state.unsolved[B] &= ~placedCells;",
                "        state.openRows[digit] &= ~(newSingleRows << (B * 3));",
                "    }",
                "    return true;",
                "}"])
board_grid(24.6, Y - 7.4, six_board(VALUE_TO_BAND[DIGIT]), digits=CLUES,
           caption=rf'before the call: where a {VALUE} can go (green), and the clues')
note(24.0, Y - 7.95, rf"green: \texttt{{valueToBand[{DIGIT}][0..2]}}, the cells where a {VALUE} can still go\\yellow: a {VALUE} already placed\\"
     r"band 0 is the band this call works on", 6.8)

# ---------------------------------------------------------------- step 1: read
yy = Y - 13.0
section(yy + 0.6, rf"Step 1, read: \ \texttt{{digit = {DIGIT}}} (the value {VALUE}), \ \texttt{{B = 0}} (board rows 0--2)")
yy -= 0.9
row(yy, START, r"\texttt{bandCells} $=$", rf"\texttt{{valueToBand[{DIGIT}][0]}}: the cells of band 0 where a {VALUE} can still go", labels=band_label(0), fills=cell_fill)
yy -= 0.9
row(yy, LAST_CHECKED, r"\texttt{lastChecked} $=$", rf"\texttt{{checked[{DIGIT}][0]}}: the mask the last time \texttt{{updateBand}} ran on it", labels=band_label(0), fills=cell_fill,
    top=False, red=LAST_CHECKED & ~START)
yy -= 0.65
note(X - 5.4, yy, rf"They differ (red: {names(LAST_CHECKED & ~START)} have lost the {VALUE} since then), so \texttt{{update}} made this call.", 27)

# ---------------------------------------------------------------- step 2: band rule
yy -= 1.8
section(yy + 0.6, rf"Step 2, the band rule: \ each row has the {VALUE} once and each box has it once, so the rows pair up one to one with the boxes")
yy -= 0.9
RX = X + 9 * W + 2 * G3 + G9   # where a row's 9 bits sit in the 27-bit strip, from the left: row 2, row 1, row 0
for r in (0, 1, 2):
    x = X + (2 - r) * (9 * W + 2 * G3 + G9)
    strip(x, yy, ROWS[r], 9, labels=lambda b, r=r: f"r{r}c{b}", fills=lambda b, r=r: ROWC[r], boxbg=lambda b: BOXC[b // 3], top=False)
    lab(x + (9 * W + 2 * G3) / 2, yy - 0.42, rf"row {r} $\to$ \texttt{{BOXES\_OF\_ROW}} $=$ \texttt{{{lit(ROW_BOXES[r], 3)}}}", 'center', r'\scriptsize')
lab(X - 0.25, yy + W / 2, r"\texttt{bandCells}, by row", font=r'\scriptsize')
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"one lookup per row: the boxes (bit \texttt{box}) where the row has a cell", 'west', r'\scriptsize')
yy -= 1.4
row(yy, BOX_CANDIDATES, r"\texttt{boxCandidates} $=$", rf"\texttt{{{lit(BOX_CANDIDATES, 9)}}}: the three results packed, bit \texttt{{row * 3 + box}}",
    n=9, labels=box_label, fills=lambda b: ROWC[b // 3], boxbg=lambda b: BOXC[b % 3], all_labels=True)
yy -= 1.15
row(yy, START, r"\texttt{bandCells}", "from step 1", labels=band_label(0), fills=cell_fill)
yy -= 0.75
row(yy, POSSIBLE, rf"\texttt{{\& POSSIBLE\_CELLS[{lit(BOX_CANDIDATES, 9)}]}}",
    rf"the triads on some pairing of rows with boxes: row 1 can only pair with box 1 (rows 0 and 2 need boxes 0 and 2), so row 1 loses boxes 0 and 2",
    top=False, fills=lambda b: 'gray!30')
rule(yy - 0.2)
yy -= 0.95
row(yy, BAND_CELLS, r"\texttt{bandCells} $=$", rf"removed: {names(BAND_RULE_REMOVED)}. Not zero, so no contradiction",
    top=False, labels=band_label(0), green=BAND_CELLS, red=BAND_RULE_REMOVED)
yy -= 0.7
note(X - 5.4, yy, rf"\texttt{{valueToBand[{DIGIT}][0] = checked[{DIGIT}][0] = bandCells}}: the mask is written back, and remembered as checked.", 27)

# ---------------------------------------------------------------- step 3: stack rule
yy -= 1.5
section(yy + 0.6, r"Step 3, the stack rule: \ only if the band's set of columns changed since \texttt{lastChecked}, because the stack rule reads nothing else")
yy -= 0.9
row(yy, OLD_COLUMNS, r"\texttt{bandColumns(lastChecked)}", r"the columns where band 0 had a cell for the value: the three rows ORed together",
    n=9, labels=lambda b: f"c{b}", boxbg=lambda b: BOXC[b // 3], all_labels=True)
yy -= 0.9
row(yy, COLUMNS, r"\texttt{columns = bandColumns(bandCells)}", rf"\texttt{{{lit(COLUMNS, 9)}}}: {', '.join(f'c{b}' for b in range(9) if CHANGED_COLUMNS >> b & 1)} gone, so \texttt{{stackRule(state, {DIGIT})}} runs",
    n=9, labels=lambda b: f"c{b}", boxbg=lambda b: BOXC[b // 3], red=CHANGED_COLUMNS, all_labels=True, top=False)
yy -= 0.85
note(X - 5.4, yy, STACK_NOTE, 27)
yy -= 1.75
for b in range(3):
    row(yy, KEPT_COLUMNS[b], rf"\texttt{{keptColumns{b}}}",
        rf"band {b}: \texttt{{{lit(STACK_COLUMNS[b], 9)}}} before" + (rf", loses {', '.join(f'c{k}' for k in range(9) if STACK_REMOVED_COLUMNS[b] >> k & 1)}" if STACK_REMOVED_COLUMNS[b] else ", nothing lost"),
        n=9, labels=lambda k: f"c{k}", boxbg=lambda k: BOXC[k // 3], red=STACK_REMOVED_COLUMNS[b], top=(b == 0))
    yy -= 0.8
yy -= 0.15
row(yy, BEFORE_STACK[1], rf"\texttt{{valueToBand[{DIGIT}][1]}}", "band 1 (board rows 3--5), before", labels=band_label(1), fills=cell_fill)
yy -= 0.75
row(yy, column_cells(KEPT_COLUMNS[1]), r"\texttt{\& columnCells(keptColumns1)}", "", top=False, fills=lambda b: 'gray!30')
rule(yy - 0.2)
yy -= 0.95
row(yy, AFTER_STACK[1], rf"\texttt{{valueToBand[{DIGIT}][1]}} $=$", rf"removed: {names(STACK_REMOVED[1], 1)}. Bands 0 and 2 keep every cell",
    top=False, labels=band_label(1), green=AFTER_STACK[1], red=STACK_REMOVED[1])

# ---------------------------------------------------------------- step 4: row singles
yy -= 1.5
section(yy + 0.6, rf"Step 4, row singles: \ a row of the band where the {VALUE} has one cell left gets it placed there")
yy -= 1.5
KX = X + 3 * W + 0.55
strip(X, yy, ONE_COLUMN, 3, green=ONE_COLUMN, boxbg=lambda b: BOXC[b], top=False, labels=lambda b: f"b{b}", all_labels=True)
for j in range(3): lab(X + j * W + W / 2, yy + W + 0.13, f"{11 - j}", 'center', r'\fontsize{4.5}{5}\selectfont')
strip(KX, yy, KEPT_BOXES, 9, green=KEPT_BOXES, boxbg=lambda b: BOXC[b % 3], labels=lambda b: box_label(b) if KEPT_BOXES >> b & 1 else '')
w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({X},{yy + W + 0.32}) -- ({X + 3 * W},{yy + W + 0.32}) node[midway,above=2pt,font=\scriptsize] {{\texttt{{ONE\_COLUMN\_BOXES[columns]}}}};")
w(rf"\draw[decorate,decoration={{brace,amplitude=3pt}}] ({KX},{yy + W + 0.32}) -- ({strip_end(KX, 9)},{yy + W + 0.32}) node[midway,above=2pt,font=\scriptsize] {{\texttt{{PERMUTATION\_UNION[boxCandidates]}}}};")
lab(X - 0.25, yy + W / 2, r"\texttt{SINGLE\_ROWS} index", font=r'\scriptsize')
lab(strip_end(KX, 9) + 0.25, yy + W / 2, r"low 9 bits: the kept box candidates (bit \texttt{row * 3 + box}); high 3: the boxes of \texttt{columns} with one column left", 'west', r'\scriptsize')
yy -= 0.85
note(X - 5.4, yy, rf"Row 1 has one kept box, box 1, and box 1 has one column left (c3), so row 1 is down to one cell. Rows 0 and 2 have two kept boxes each, so two cells or more.", 27)
yy -= 1.35
SX = X
row(yy, SINGLE, r"\texttt{singleRows} $=$", rf"\texttt{{{lit(SINGLE, 3)}}}: \texttt{{SINGLE\_ROWS}} at that index (bit \texttt{{row}})", n=3, labels=lambda b: f"r{b}", all_labels=True, green=SINGLE)
yy -= 0.85
row(yy, OPEN_ROWS_5, rf"\texttt{{openRows[{DIGIT}]}}", rf"\texttt{{{lit(OPEN_ROWS_5, 9)}}}: the board rows where the {VALUE} is not placed yet", n=9, labels=lambda b: f"r{b}", all_labels=True,
    top=False)
yy -= 0.85
row(yy, OPEN_IN_BAND, r"\texttt{openRowsInBand} $=$", rf"\texttt{{(openRows[{DIGIT}] >> (0 * 3)) \& 0b111}}: band 0's three rows; none has the {VALUE} yet", n=3, labels=lambda b: f"r{b}",
    all_labels=True, top=False)
yy -= 0.85
row(yy, NEW_SINGLE, r"\texttt{newSingleRows} $=$", rf"\texttt{{singleRows \& openRowsInBand = {lit(NEW_SINGLE, 3)}}}: row 1, not zero, so a cell is placed", n=3,
    labels=lambda b: f"r{b}", all_labels=True, top=False, green=NEW_SINGLE)
yy -= 1.1
row(yy, BAND_CELLS, r"\texttt{bandCells}", "from step 2", labels=band_label(0), fills=cell_fill)
yy -= 0.75
row(yy, rows_cells(NEW_SINGLE), rf"\texttt{{\& ROWS\_CELLS[{lit(NEW_SINGLE, 3)}]}}", "row 1's cells", top=False, fills=lambda b: 'gray!30')
rule(yy - 0.2)
yy -= 0.95
row(yy, PLACED, r"\texttt{placedCells} $=$", rf"{PLACED_NAME}: the {VALUE} goes there", top=False, labels=band_label(0), fills=lambda b: 'yellow!70')
yy -= 0.85
note(X - 5.4, yy, rf"\texttt{{digitMaskNow = valueToBand[{DIGIT}][0]}} $=$ \texttt{{{lit(DIGIT_MASK_NOW, 27)}}}: the mask as it is now, after the stack rule "
     r"(which happens to leave band 0 alone here). Then every value loses the cell, and the loop gives the value its own mask back:", 27)
yy -= 1.6
for o in LOSERS:
    row(yy, state[o][0], rf"\texttt{{valueToBand[{o}][0]}} $=$", rf"the value {o + 1} loses {PLACED_NAME}" + (r"; the other 6 values did not have it, so the \texttt{\&=} changes nothing for them" if o == LOSERS[-1] else ""),
        labels=lambda b, o=o: band_label(0)(b) if PLACED >> b & 1 else '', red=PLACED, top=(o == LOSERS[0]))
    yy -= 0.8
row(yy, unsolved0, r"\texttt{unsolved[0]} $=$", rf"{PLACED_NAME} is solved", labels=lambda b: band_label(0)(b) if PLACED >> b & 1 else '', red=PLACED, top=False)
yy -= 0.9
row(yy, openRows5, rf"\texttt{{openRows[{DIGIT}]}} $=$", rf"\texttt{{{lit(openRows5, 9)}}}: the {VALUE} is done in row 1, so it is never placed there again", n=9,
    labels=lambda b: f"r{b}", all_labels=True, top=False, red=NEW_SINGLE << (B * 3))

# ---------------------------------------------------------------- the result
yy -= 1.4
section(yy + 0.6, r"The result, and what \texttt{update} does next")
yy -= 4.6
fills = six_board(state[DIGIT])
for band, removed in ((0, BAND_RULE_REMOVED), (1, STACK_REMOVED[1])):
    for bit in range(27):
        if removed >> bit & 1: fills[(band * 3 + bit // 9, bit % 9)] = 'red!30' if band == 0 else 'violet!35'
fills[(PLACED_BIT // 9, PLACED_BIT % 9)] = 'yellow!70'
board_grid(1.0, yy, fills, digits={**CLUES, (PLACED_BIT // 9, PLACED_BIT % 9): str(VALUE)}, caption=rf'after the call: where a {VALUE} can go')
note(6.0, yy + 3.7, rf"green: still a candidate \\ red: removed by the band rule (step 2) \\ violet: removed by the stack rule (step 3) \\ yellow: a {VALUE} placed, {PLACED_NAME} is new (step 4)\\[6pt]"
     rf"\textbf{{Now differing from \texttt{{checked}}}}, so \texttt{{update}} calls \texttt{{updateBand}} on them later in this pass or in the next:\\"
     rf"\texttt{{valueToBand[{DIGIT}][1]}}, changed by the stack rule;\\"
     + r"".join(rf"\texttt{{valueToBand[{o}][0]}}, which lost {PLACED_NAME} (the value {o + 1});\\" for o in LOSERS) +
     rf"\textbf{{Not}} \texttt{{valueToBand[{DIGIT}][0]}}: it still equals \texttt{{checked[{DIGIT}][0]}}, because the stack rule left it alone and the placement "
     r"gave it its own mask back. Had the stack rule shrunk it, it would differ from \texttt{checked} and run again.", 20)
render('updateband')
