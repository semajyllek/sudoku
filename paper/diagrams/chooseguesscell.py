#!/usr/bin/env python3
# chooseGuessCell, traced on one real call: a state three guesses deep in magictour puzzle 96 (the puzzle of the
# updateBand and stack rule diagrams) with six two-candidate cells, two of them tied for the best score. Every mask is
# drawn as its full bit string, high bit on the left. The code shown is read from fastbandsolver.hpp. Writes
# chooseguesscell.png next to this script.
from search_common import *

J = DATA['guess']
state = State(J)
PAIRS = J['pairs']

# ---------------------------------------------------------------- the code, step by step, in the same order
ITERATIONS = []   # (band, p, bitIndex, p & -p, score, replaced, bestScore after, best after)
best, bestScore = (-1, 0, 2), -1
for band in range(3):
    p = PAIRS[band]
    while p:
        bitIndex = countr_zero(p)
        score = peer_score(state, band, bitIndex)
        replaced = score > bestScore
        if replaced:
            bestScore = score
            best = (band, p & -p, 2)
        ITERATIONS.append((band, p, bitIndex, p & -p, score, replaced, bestScore, best))
        p &= p - 1
assert list(best) == J['result']
assert [[b, i, s] for b, _, i, _, s, *_ in ITERATIONS] == J['scores']
WIN_BAND, WIN_BIT = best[0], countr_zero(best[1])
TIES = [(b, i) for b, _, i, _, s, rep, *_ in ITERATIONS if s == bestScore and not rep]
assert TIES

# ---------------------------------------------------------------- drawing
Y = 2.9
header(Y, r"\texttt{chooseGuessCell}: the two-candidate cell to guess on",
       r"\textbf{What it is for.} When \texttt{propagate} stops with the grid still open, \texttt{search} has to guess. A cell with exactly two candidates is the cheapest guess: two branches, and the second one reuses the state. "
       r"\texttt{propagate} already hands over those cells as \texttt{pairs[band]} (its \texttt{twice \& \textasciitilde{}thrice}). Among them this picks the one with the most unsolved peers (\texttt{peerScore}), because placing a value there removes the most candidates, "
       r"so the next \texttt{propagate} gets the furthest. Ties go to the first cell in board order. If there are no pairs, it returns \texttt{band = -1} and \texttt{search} uses \texttt{fewestCandidatesCell} instead.\\[3pt]"
       rf"\textbf{{The call drawn here}} is a real one: magictour puzzle {DATA['index'] + 1}, {J['depth']} guesses deep. It has {len(ITERATIONS)} two-candidate cells.")
code(Y - 3.4, source('FastBandSolver::chooseGuessCell('), 21)

GX, GY, CS = 23.2, Y - 10.0, 0.68
fills, corner = {}, {}
for band, _, bitIndex, _, score, *_ in ITERATIONS:
    rc = (3 * band + bitIndex // 9, bitIndex % 9)
    fills[rc] = 'yellow!45'
    corner[rc] = str(score)
for band, bitIndex in TIES: fills[(3 * band + bitIndex // 9, bitIndex % 9)] = 'orange!40'
fills[(3 * WIN_BAND + WIN_BIT // 9, WIN_BIT % 9)] = 'green!40'
board(GX, GY, state, CS, fills=fills, corner=corner)
note(GX - 1.2, GY - 0.25,
     r"Large digits are solved cells, small digits are the candidates of the others."
     r" \colorbox{yellow!45}{Yellow}: the two-candidate cells, each with its two values and, in red, its \texttt{peerScore}."
     rf" \colorbox{{green!40}}{{Green}}: the winner, {cell_name(WIN_BAND, WIN_BIT)}."
     rf" \colorbox{{orange!40}}{{Orange}}: {', '.join(cell_name(b, i) for b, i in TIES)}, the same score but later in board order.", 8.4)

# ---------------------------------------------------------------- 1. the input
yy = Y - 13.4
section(yy, r"1. \ The input: \texttt{pairs[band]}, the cells with exactly two candidates, from \texttt{propagate}")
yy -= 1.4
for band in range(3):
    strip(X, yy, PAIRS[band], 27, labels=band_label(band), fills=lambda bit: 'yellow!45', boxbg=cell_bg, top=(band == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{pairs[{band}]}} (rows {3 * band}--{3 * band + 2})")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"$\texttt{{{lit(PAIRS[band], 27)}}}$ \ ({popcount(PAIRS[band])} cell{'s' if popcount(PAIRS[band]) != 1 else ''})", 'west', r'\scriptsize')
    yy -= 0.85

# ---------------------------------------------------------------- 2. the bit tricks, on the first iteration
yy -= 0.4
section(yy, r"2. \ How the inner loop visits each 1 of \texttt{p}, shown on the first iteration (\texttt{Mask} is 32 bits, so all 32 are drawn)")
note(-0.3, yy - 0.45,
     r"\texttt{std::countr\_zero(p)} is the number of 0s below the lowest 1: that 1's bit number, which is the cell's \texttt{bitIndex}."
     r" \texttt{-p} is the two's complement \texttt{\textasciitilde{}p + 1}: every bit above the lowest 1 flips, so \texttt{p \& -p} keeps only the lowest 1, the cell's one-bit mask."
     r" \texttt{p - 1} turns the lowest 1 into 0 and the 0s below it into 1s, so \texttt{p \&= p - 1} clears the lowest 1 and the next pass finds the next cell.", 30)
yy -= 1.9
G32 = [(5, 0.26)] + groups27()
_, band0p, bi0, low0, *_ = ITERATIONS[0]
neg = (-band0p) & 0xFFFFFFFF
rows32 = [(band0p, r"\texttt{p} $=$ \texttt{pairs[0]}", ''),
          (neg, r"\texttt{-p}", r"every bit above the lowest 1 flipped"),
          (low0, r"\texttt{p \& -p}", rf"only the lowest 1: bit {bi0}, so \texttt{{countr\_zero(p)}} $= {bi0}$ ({cell_name(0, bi0)})"),
          ((band0p - 1) & 0xFFFFFFFF, r"\texttt{p - 1}", r"the lowest 1 became 0, the 0s below it became 1s"),
          (band0p & (band0p - 1), r"\texttt{p \& (p - 1)}", r"the lowest 1 cleared: what \texttt{p \&= p - 1} leaves for the next pass")]
for k, (v, name, why) in enumerate(rows32):
    _, xend = bit_strip(X, yy, v, G32, labels=(lambda bit: cell_name(0, bit) if bit < 27 else '') if k in (0, 2, 4) else None, fills=lambda bit: 'yellow!45', top=(k == 0), bw=0.44,
                        green=low0 if k == 2 else 0)
    lab(X - 0.25, yy + 0.22, name)
    lab(xend + 0.2, yy + 0.22, why, 'west', r'\scriptsize')
    yy -= 0.78

# ---------------------------------------------------------------- 3. the loop
yy -= 0.4
section(yy, r"3. \ The loops, one row per pass: each two-candidate cell gets a \texttt{peerScore}; only a \emph{strictly} higher score replaces \texttt{best}")
yy -= 1.1
PX, LX = 1.9, 12.5
SMALL = 0.28
lab(PX + 4.3, yy + 0.55, r"\texttt{p} at the top of the pass", 'center', r'\scriptsize')
lab(LX + 4.3, yy + 0.55, r"\texttt{p \& -p}: the cell's one-bit mask", 'center', r'\scriptsize')
lab(22.0, yy + 0.55, r"\texttt{countr\_zero(p)}, \texttt{score}", 'west', r'\scriptsize')
lab(25.8, yy + 0.55, r"\texttt{score > bestScore}?", 'west', r'\scriptsize')
yy -= 0.35
lastBand = None
for band, p, bitIndex, low, score, replaced, bestAfter, bestNow in ITERATIONS:
    if band != lastBand:
        lab(-0.3, yy + 0.14, rf"\texttt{{band = {band}}}", 'west', r'\scriptsize\bfseries')
        lastBand = band
    bit_strip(PX, yy, p, groups27(), fills=lambda bit: 'yellow!45', top=False, bw=SMALL)
    bit_strip(LX, yy, low, groups27(), labels=band_label(band), green=low, top=False, bw=SMALL)
    lab(22.0, yy + 0.14, rf"{bitIndex} ({cell_name(band, bitIndex)}), \ \texttt{{peerScore}} $= {score}$", 'west', r'\scriptsize')
    before = bestAfter if not replaced else None
    if replaced:
        verdict = rf"\textcolor{{green!45!black}}{{\textbf{{yes}}}}: \texttt{{bestScore}} $\gets {score}$, \texttt{{best}} $\gets$ \{{{band}, \texttt{{p \& -p}}, 2\}}"
    else:
        verdict = rf"\textcolor{{red!70!black}}{{no}} (${score}$ is not $> {bestAfter}$): \texttt{{best}} stays {cell_name(bestNow[0], countr_zero(bestNow[1]))}"
    lab(25.8, yy + 0.14, verdict, 'west', r'\scriptsize')
    yy -= 0.62
    if p & (p - 1) == 0:
        lab(PX, yy + 0.14, r"\texttt{p \&= p - 1} leaves \texttt{p} $= 0$: the inner loop ends", 'west', r'\scriptsize\itshape')
        yy -= 0.55

# ---------------------------------------------------------------- 4. the result
yy -= 0.3
section(yy, r"4. \ \texttt{return best;}")
yy -= 1.0
note(-0.3, yy + 0.3,
     rf"\texttt{{best}} $=$ \{{\texttt{{band}} $= {best[0]}$, \texttt{{cellBitMask}} $=$ \texttt{{{lit(best[1], 27)}}} (bit {WIN_BIT}, {cell_name(WIN_BAND, WIN_BIT)}), \texttt{{candidates}} $= 2$\}}. "
     rf"{cell_name(WIN_BAND, WIN_BIT)} and {', '.join(cell_name(b, i) for b, i in TIES)} both have {bestScore} unsolved peers; {cell_name(WIN_BAND, WIN_BIT)} comes first in board order "
     r"(bands 0 to 2, and inside a band bit $9\times\text{row}+\text{column}$ upward, which is row by row), and the strict \texttt{>} keeps it. "
     rf"\texttt{{search}} then calls \texttt{{nextValueIn}} twice for its two values, {J['first'] + 1} and {J['second'] + 1}, and tries {J['first'] + 1} first. "
     r"\texttt{candidates} is always 2 here; \texttt{search} only reads it after \texttt{fewestCandidatesCell}, to count the guesses.", 30)

render('chooseguesscell')
