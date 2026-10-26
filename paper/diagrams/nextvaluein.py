#!/usr/bin/env python3
# nextValueIn, traced on the two real calls search makes after chooseGuessCell in chooseguesscell.py (magictour puzzle
# 96, three guesses deep): from digit 0, then from first + 1. Every mask is drawn as its full bit string, high bit on
# the left. The code shown is read from fastbandsolver.hpp. Writes nextvaluein.png next to this script.
from search_common import *

J = DATA['guess']
state = State(J)
BAND, CELL_MASK = J['result'][0], J['result'][1]
BIT = countr_zero(CELL_MASK)
NAME = cell_name(BAND, BIT)

# ---------------------------------------------------------------- the code, step by step, in the same order
def trace(startDigit):
    """(digits tested, with whether the cell's bit is set, and the digit returned)"""
    tested, digit = [], startDigit
    while digit < 9 and (state.valueToBand[digit][BAND] & CELL_MASK) == 0:
        tested.append((digit, False))
        digit += 1
    if digit < 9: tested.append((digit, True))
    return tested, digit
TESTED1, FIRST = trace(0)
TESTED2, SECOND = trace(FIRST + 1)
assert (FIRST, SECOND) == (J['first'], J['second'])
assert next_value_in(state, BAND, CELL_MASK, 0) == FIRST and next_value_in(state, BAND, CELL_MASK, FIRST + 1) == SECOND
assert state.candidates(BAND, BIT) == [FIRST, SECOND]
TESTED3, THIRD = trace(SECOND + 1)   # what a third call would do: nothing left, so 9
assert THIRD == 9

# ---------------------------------------------------------------- drawing
Y = 2.9
header(Y, r"\texttt{nextValueIn}: the next digit, from \texttt{startDigit} on, that can still go in a cell",
       r"\textbf{What it is for.} After choosing a cell, \texttt{search} needs its candidates in order. A cell's candidates are not stored together: digit $d$ can go in the cell exactly when bit \texttt{bitIndex} is set in \texttt{valueToBand[d][band]}, one mask per digit. "
       r"So this tests the nine masks in order, starting at \texttt{startDigit} (included), and returns the first digit whose mask has the cell, or 9 if none does. "
       r"For a two-candidate cell \texttt{search} calls it twice, from 0 and from \texttt{first + 1}; after \texttt{fewestCandidatesCell} it is the step of a \texttt{for} loop over all the cell's candidates, which ends at 9.\\[3pt]"
       rf"\textbf{{The calls drawn here}} are the two \texttt{{search}} makes for {NAME}, the cell \texttt{{chooseGuessCell}} picks in its diagram (magictour puzzle {DATA['index'] + 1}, {J['depth']} guesses deep). Digits are 0--8; the value is the digit $+ 1$.")
code(Y - 3.4, source('FastBandSolver::nextValueIn('), 20)
note(-0.3, Y - 5.6, r"Called from \texttt{search} as:\\" r"\texttt{" + r"\\".join(tt(x) for x in [
    "int first = nextValueIn(*state, guess.band, guess.cellBitMask, 0);",
    "int second = nextValueIn(*state, guess.band, guess.cellBitMask, first + 1);"]) + "}", 20)

GX, GY, CS = 23.2, Y - 10.0, 0.68
board(GX, GY, state, CS, fills={(3 * BAND + BIT // 9, BIT % 9): 'green!40'})
note(GX - 1.2, GY - 0.25, rf"\colorbox{{green!40}}{{{NAME}}}: its small digits {FIRST + 1} and {SECOND + 1} are its candidates, the values of digits {FIRST} and {SECOND}.", 8.4)

# ---------------------------------------------------------------- 1. the nine masks
yy = Y - 12.4
section(yy, rf"1. \ The nine masks of band {BAND}, \texttt{{state.valueToBand[digit][{BAND}]}}, and \texttt{{cellBitMask}} $=$ \texttt{{Mask(1) << {BIT}}} ({NAME}); the cell's bit has a yellow background")
yy -= 1.75
COLX = strip_end(X, 27) + 0.4
lab(COLX + 0.1, yy + 0.95, r"\texttt{\& cellBitMask}", 'west', r'\scriptsize')
lab(COLX + 2.0, yy + 0.95, r"call 1: \texttt{startDigit = 0}", 'west', r'\scriptsize\bfseries')
lab(COLX + 6.4, yy + 0.95, rf"call 2: \texttt{{startDigit = first + 1 = {FIRST + 1}}}", 'west', r'\scriptsize\bfseries')
def verdict(tested, digit, startDigit):
    if digit < startDigit: return r"\textcolor{gray}{below \texttt{startDigit}: not tested}"
    for d, hit in tested:
        if d == digit:
            return (rf"\textcolor{{green!45!black}}{{\textbf{{set}}: return {d}}} (value {d + 1})" if hit
                    else r"$0$: \texttt{digit++}")
    return r"\textcolor{gray}{not reached}"
for digit in range(9):
    m = state.valueToBand[digit][BAND]
    hl = lambda bit: 'yellow!60' if bit == BIT else cell_bg(bit)
    strip(X, yy, m, 27, labels=band_label(BAND), fills=lambda bit: 'blue!25', boxbg=hl, top=(digit == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{valueToBand[{digit}][{BAND}]}} (value {digit + 1})")
    hit = m & CELL_MASK
    lab(COLX + 0.1, yy + W / 2, r"$\neq 0$" if hit else r"$= 0$", 'west', r'\scriptsize')
    lab(COLX + 2.0, yy + W / 2, verdict(TESTED1, digit, 0), 'west', r'\scriptsize')
    lab(COLX + 6.4, yy + W / 2, verdict(TESTED2, digit, FIRST + 1), 'west', r'\scriptsize')
    yy -= 0.8

# ---------------------------------------------------------------- 2. one test, bit by bit
yy -= 0.4
section(yy, rf"2. \ One test, bit by bit: \texttt{{(state.valueToBand[digit][band] \& cellBitMask) == 0}} for \texttt{{digit}} $= {FIRST}$, where call 1 stops")
yy -= 1.4
m = state.valueToBand[FIRST][BAND]
strip(X, yy, m, 27, labels=band_label(BAND), fills=lambda bit: 'blue!25', boxbg=cell_bg, top=True)
lab(X - 0.25, yy + W / 2, rf"\texttt{{valueToBand[{FIRST}][{BAND}]}}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(m, 27)}}}$", 'west', r'\scriptsize')
yy -= 0.8
strip(X, yy, CELL_MASK, 27, labels=band_label(BAND), fills=lambda bit: 'green!40', boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"\texttt{\& cellBitMask}")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(CELL_MASK, 27)}}}$", 'west', r'\scriptsize')
w(rf"\draw[thick] ({X - 3.0},{yy - 0.2}) -- ({strip_end(X, 27)},{yy - 0.2});")
yy -= 0.95
strip(X, yy, m & CELL_MASK, 27, labels=band_label(BAND), green=m & CELL_MASK, boxbg=cell_bg, top=False)
lab(X - 0.25, yy + W / 2, r"result")
lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"not 0, so the \texttt{{while}} stops and \texttt{{nextValueIn}} returns {FIRST}", 'west', r'\scriptsize')
yy -= 1.3

# ---------------------------------------------------------------- 3. the results
section(yy, r"3. \ The results")
note(-0.3, yy - 0.45,
     rf"Call 1 tests digits 0 to {FIRST} ({len(TESTED1)} tests) and returns \texttt{{first}} $= {FIRST}$ (value {FIRST + 1}). "
     rf"Call 2 starts at {FIRST + 1}, tests digits {FIRST + 1} to {SECOND} ({len(TESTED2)} tests) and returns \texttt{{second}} $= {SECOND}$ (value {SECOND + 1}). "
     rf"\texttt{{search}} places {FIRST + 1} in a copy of the state, and if that branch does not stop the search, {SECOND + 1} in the state itself. "
     rf"A third call, from {SECOND + 1}, would test the {9 - SECOND - 1} digit{'s' if 9 - SECOND - 1 != 1 else ''} left, find nothing, and return 9: that is how the \texttt{{for}} loop after \texttt{{fewestCandidatesCell}} ends.", 30)

render('nextvaluein')
