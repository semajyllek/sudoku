#!/usr/bin/env python3
# record and writeSolution, traced on the real solved state of magictour puzzle 96 (the puzzle of the other search
# diagrams): every mask drawn as its full bit string, high bit on the left, one mask's loop traced step by step, and
# the grid it writes. The code shown is read from fastbandsolver.hpp. Writes record.png next to this script.
from search_common import *

J = DATA['solved']
state = State(J)

# ---------------------------------------------------------------- the code, step by step, in the same order
out = [[0] * 9 for _ in range(9)]
for digit in range(9):
    for band in range(3):
        remaining = state.valueToBand[digit][band]
        while remaining:
            bitIndex = countr_zero(remaining)
            out[band * 3 + bitIndex // 9][bitIndex % 9] = digit + 1
            remaining &= remaining - 1
assert sum(out, []) == J['grid']
assert state.unsolved == [0, 0, 0]
for band in range(3):   # solved: each cell in exactly one digit's mask, so each band's nine masks are a partition
    assert sum(popcount(state.valueToBand[d][band]) for d in range(9)) == 27
    union = 0
    for d in range(9): union |= state.valueToBand[d][band]
    assert union == ALL_CELLS
TRACE_DIGIT, TRACE_BAND = 0, 0
STEPS = []
remaining = state.valueToBand[TRACE_DIGIT][TRACE_BAND]
while remaining:
    bitIndex = countr_zero(remaining)
    STEPS.append((remaining, bitIndex))
    remaining &= remaining - 1

# ---------------------------------------------------------------- drawing
Y = 2.9
header(Y, r"\texttt{record} and \texttt{writeSolution}: counting a solution and writing out the first one",
       r"\textbf{What it is for.} When \texttt{propagate} returns \textbf{solved}, \texttt{search} calls \texttt{record}. It counts the solution in \texttt{found}, and only for the first one, and only if the caller passed a grid (\texttt{solutionOut}), writes it out. "
       r"It keeps counting after the first because with \texttt{limit} $= 2$ (the uniqueness test, \texttt{countSolutions(in, 2)}) a second solution proves the puzzle is not unique; \texttt{search} stops once \texttt{found >= limit}. \texttt{solve} uses \texttt{limit} $= 1$.\\[3pt]"
       r"\textbf{How the grid is written.} A solved state still holds the 27 masks, one per (digit, band), and every cell is in exactly one of them. So \texttt{writeSolution} walks each mask's 1s and writes that digit $+ 1$ into those cells, "
       r"instead of scanning up to nine masks for each of the 81 cells.\\[3pt]"
       rf"\textbf{{The state drawn here}} is the real solved state of magictour puzzle {DATA['index'] + 1} (the puzzle of the other search diagrams), found {J['depth']} guess{'es' if J['depth'] != 1 else ''} deep.")
code(Y - 4.1, source('FastBandSolver::record(') + [''] + source('FastBandSolver::writeSolution('), 21)

# ---------------------------------------------------------------- 1. one mask, step by step
yy = Y - 10.2
section(yy, rf"1. \ One mask's inner loop: \texttt{{digit}} $= {TRACE_DIGIT}$ (value {TRACE_DIGIT + 1}), \texttt{{band}} $= {TRACE_BAND}$")
yy -= 1.4
for k, (rem, bitIndex) in enumerate(STEPS):
    low = rem & -rem
    strip(X, yy, rem, 27, labels=band_label(TRACE_BAND), fills=lambda bit: DIGITC[TRACE_DIGIT], green=low, boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, r"\texttt{remaining} $=$ \texttt{valueToBand[0][0]}" if k == 0 else r"\texttt{remaining \&= remaining - 1}")
    r, c = TRACE_BAND * 3 + bitIndex // 9, bitIndex % 9
    lab(strip_end(X, 27) + 0.25, yy + W / 2,
        rf"\texttt{{bitIndex = countr\_zero(remaining)}} $= {bitIndex}$ \ $\to$ \ \texttt{{out[{TRACE_BAND} * 3 + {bitIndex} / 9][{bitIndex} \% 9]}} $=$ \texttt{{out[{r}][{c}] = {TRACE_DIGIT + 1}}}", 'west', r'\scriptsize')
    yy -= 0.85
strip(X, yy, 0, 27, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{remaining \&= remaining - 1}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, r"$= 0$: the inner loop ends. The green 1 in each row is the lowest one, the cell written on that pass.", 'west', r'\scriptsize')
yy -= 1.2

# ---------------------------------------------------------------- 2. all 27 masks, and the grid
section(yy, r"2. \ All 27 masks of the solved state, \texttt{valueToBand[digit][band]}, and the grid they write. Bit $9\times\text{row}+\text{column}$ of band $b$ is board row $3b+\text{row}$")
yy -= 1.25
SX = [2.7, 11.3, 19.9]
for band in range(3): lab(SX[band] + 3.9, yy + 0.55, rf"band {band} (board rows {3 * band}--{3 * band + 2})", 'center', r'\scriptsize\bfseries')
yy -= 0.2
for digit in range(9):
    lab(SX[0] - 0.2, yy + 0.13, rf"digit {digit} (value {digit + 1})", 'east', r'\scriptsize')
    for band in range(3):
        bit_strip(SX[band], yy, state.valueToBand[digit][band], groups27(0.05, 0.18), fills=lambda bit, d=digit: DIGITC[d], top=(digit == 0), bw=0.27,
                  labels=band_label(band))
    yy -= 0.62
GX, GY, CS = 23.4, yy - 6.6, 0.68
fills = {(r, c): DIGITC[out[r][c] - 1] for r in range(9) for c in range(9)}
board(GX, GY, state, CS, fills=fills, marks={(r, c): str(out[r][c]) for r in range(9) for c in range(9)})
note(-0.3, yy - 0.2,
     r"Each 1 is drawn in its digit's colour, and the grid on the right uses the same colours: every cell of the grid comes from exactly one 1 above. "
     r"In each band the nine masks have 27 ones between them, one per cell, and no cell is in two masks: that is what being solved means for the masks. "
     rf"\texttt{{writeSolution}} visits the masks in order, digit 0 to 8 and band 0 to 2 within each digit, and writes the 81 cells in that order, not in board order.\\[4pt]"
     r"The clues of the puzzle are among these cells: \texttt{load} placed them with \texttt{place}, so they are in the masks like every other solved cell.", 21)

render('record')
