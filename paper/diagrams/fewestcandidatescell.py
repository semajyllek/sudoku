#!/usr/bin/env python3
# fewestCandidatesCell, traced on one real call: the first state, over the magictour, forum_hardest_1905 and
# forum_hardest_1106 sets in order, where no cell has two candidates and the first unsolved cell has more than the
# fewest (see search_states.cpp). Every
# mask is drawn as its full bit string, high bit on the left. The code shown is read from fastbandsolver.hpp. Writes
# fewestcandidatescell.png next to this script.
from search_common import *

J = DATA['fallback']
state = State(J)
SET = os.path.basename(J['file']).split('_', 1)[1]

# ---------------------------------------------------------------- the code, step by step, in the same order
ROWS = []   # (band, bitIndex, candidates, skipped, score, fewer, higher, best after, best before)
best, bestScore = (-1, 0, 10), -1
for band in range(3):
    u = state.unsolved[band]
    while u:
        bitIndex = countr_zero(u)
        candidates = sum(state.valueToBand[digit][band] >> bitIndex & 1 for digit in range(9))
        if candidates > best[2]:
            ROWS.append((band, bitIndex, candidates, True, None, False, False, best, best))
            u &= u - 1
            continue
        score = peer_score(state, band, bitIndex)
        fewer, higher = candidates < best[2], score > bestScore
        before = best
        if fewer or higher:
            bestScore = score
            best = (band, u & -u, candidates)
        ROWS.append((band, bitIndex, candidates, False, score, fewer, higher, best, before))
        u &= u - 1
assert list(best) == J['result']
WIN_BAND, WIN_BIT = best[0], countr_zero(best[1])
WIN = cell_name(WIN_BAND, WIN_BIT)
assert [d for d in range(9) if state.valueToBand[d][WIN_BAND] >> WIN_BIT & 1] == J['digits']
assert all(len(state.candidates(b, i)) != 2 for b in range(3) for i in range(27) if state.unsolved[b] >> i & 1)
SCORED = [r for r in ROWS if not r[3]]
SKIPPED = [r for r in ROWS if r[3]]

# ---------------------------------------------------------------- drawing
Y = 2.9
header(Y, r"\texttt{fewestCandidatesCell}: the guess when no cell has two candidates",
       r"\textbf{What it is for.} \texttt{search} falls back on it when \texttt{chooseGuessCell} finds no two-candidate cell. It takes the unsolved cell with the fewest candidates, because a cell with $n$ candidates means $n$ branches; among those, the one with the most unsolved peers (\texttt{peerScore}); then the first in board order. "
       r"It is rare, about 1\% of guesses on the hardest puzzles, but tends to happen near the top of the tree, where a cell with five candidates instead of three multiplies the work below it.\\[3pt]"
       rf"\textbf{{The call drawn here}} is a real one: the first state in the magictour, forum\_hardest\_1905 and forum\_hardest\_1106 sets where no cell has two candidates and the first unsolved cell has more candidates than the fewest, so that both halves of the \texttt{{||}} get to replace \texttt{{best}}. It is in {SET.replace('_', chr(92) + '_')} puzzle {J['index'] + 1}, " + ("at the root, before any guess" if J['depth'] == 0 else f"{J['depth']} guess{'es' if J['depth'] != 1 else ''} deep") + rf", with {len(ROWS)} unsolved cells.")
code(Y - 3.4, source('FastBandSolver::fewestCandidatesCell('), 21)

GX, GY, CS = 23.2, Y - 10.0, 0.68
fills, corner = {}, {}
for band, bitIndex, candidates, skipped, score, *_ in ROWS:
    rc = (3 * band + bitIndex // 9, bitIndex % 9)
    if skipped: fills[rc] = 'gray!15'
    else:
        fills[rc] = 'yellow!45'
        corner[rc] = str(score)
fills[(3 * WIN_BAND + WIN_BIT // 9, WIN_BIT % 9)] = 'green!40'
board(GX, GY, state, CS, fills=fills, corner=corner)
note(GX - 1.2, GY - 0.25,
     rf"\colorbox{{gray!15}}{{Gray}}: more candidates than the best so far, skipped by the \texttt{{continue}} with no score ({len(SKIPPED)} cells). "
     rf"\colorbox{{yellow!45}}{{Yellow}}: scored ({len(SCORED)} cells), with its candidates and, in red, its \texttt{{peerScore}}. \colorbox{{green!40}}{{Green}}: the winner, {WIN}.", 8.4)

# ---------------------------------------------------------------- 1. counting one cell's candidates
yy = Y - 13.0
section(yy, rf"1. \ \texttt{{candidates += (state.valueToBand[digit][band] >> bitIndex) \& 1}} for the nine digits, shown for {WIN} (\texttt{{band}} $= {WIN_BAND}$, \texttt{{bitIndex}} $= {WIN_BIT}$)")
note(-0.3, yy - 0.45, r"Unlike \texttt{chooseGuessCell}, which gets its cells from \texttt{propagate}'s counters, this has to count each cell's candidates itself: nine loads per cell. "
     r"That is why it is only the fallback, and why a cell that already has more candidates than the best skips the \texttt{peerScore}.", 30)
yy -= 1.9
for digit in range(9):
    m = state.valueToBand[digit][WIN_BAND]
    hl = lambda bit: 'yellow!60' if bit == WIN_BIT else cell_bg(bit)
    strip(X, yy, m, 27, labels=band_label(WIN_BAND), fills=lambda bit: 'blue!25', boxbg=hl, top=(digit == 0))
    lab(X - 0.25, yy + W / 2, rf"\texttt{{valueToBand[{digit}][{WIN_BAND}]}} (value {digit + 1})")
    lab(strip_end(X, 27) + 0.25, yy + W / 2, rf"\texttt{{>> {WIN_BIT} \& 1}} $= {m >> WIN_BIT & 1}$", 'west', r'\scriptsize')
    yy -= 0.78
lab(strip_end(X, 27) + 0.25, yy + 0.4, rf"sum: \texttt{{candidates}} $= {best[2]}$ (values {', '.join(str(d + 1) for d in J['digits'])})", 'west', r'\scriptsize\bfseries')
yy -= 0.6

# ---------------------------------------------------------------- 2. the loop
section(yy, r"2. \ The loop over every unsolved cell, in board order: one row per cell that gets a score, the skipped cells listed between them")
yy -= 0.9
C = [-0.3, 3.0, 5.4, 7.8, 22.4]
heads = [r"cell (\texttt{bitIndex})", r"\texttt{candidates}", r"\texttt{peerScore}",
         r"\texttt{candidates < best.candidates || score > bestScore}?", r"\texttt{best} after"]
for x, t in zip(C, heads): lab(x, yy, t, 'west', r'\scriptsize\bfseries')
yy -= 0.5
pending = []
def flush():
    global yy
    if not pending: return
    txt = ', '.join(rf"{cell_name(b, i)} ({c})" for b, i, c, _ in pending)
    w(rf"\node[font=\scriptsize,text=gray!70!black,anchor=north west,align=left,text width=30.5cm] at (-0.3,{yy + 0.2}) "
      rf"{{\textit{{skipped by the \texttt{{continue}}}} ({len(pending)} cell{'s' if len(pending) != 1 else ''}, candidates in brackets, all more than the best's {pending[0][3]}): {txt}}};")
    yy -= 0.42 * (1 + len(txt) // 230) + 0.15
    pending.clear()
for band, bitIndex, candidates, skipped, score, fewer, higher, bestNow, before in ROWS:
    if skipped:
        pending.append((band, bitIndex, candidates, bestNow[2]))
        continue
    flush()
    prevScore = peer_score(state, before[0], countr_zero(before[1])) if before[0] >= 0 else -1
    lab(C[0], yy, rf"{cell_name(band, bitIndex)} (band {band}, bit {bitIndex})", 'west', r'\scriptsize')
    lab(C[1], yy, str(candidates), 'west', r'\scriptsize')
    lab(C[2], yy, str(score), 'west', r'\scriptsize')
    if fewer:
        t = (rf"\textcolor{{green!45!black}}{{\textbf{{yes}}}}: {candidates} $<$ {before[2]}"
             + (r" (the starting 10: the first cell checked always replaces it)" if before[0] == -1 else ""))
    elif higher:
        t = rf"\textcolor{{green!45!black}}{{\textbf{{yes}}}}: same {candidates} candidates, and {score} $>$ \texttt{{bestScore}} $= {prevScore}$"
    else:
        t = rf"\textcolor{{red!70!black}}{{no}}: same {candidates} candidates, and {score} is not $>$ \texttt{{bestScore}} $= {prevScore}$"
    lab(C[3], yy, t, 'west', r'\scriptsize')
    lab(C[4], yy, rf"{cell_name(bestNow[0], countr_zero(bestNow[1]))}, {bestNow[2]} candidates", 'west', r'\scriptsize')
    yy -= 0.45
flush()

# ---------------------------------------------------------------- 3. the result
yy -= 0.3
section(yy, r"3. \ \texttt{return best;}")
note(-0.3, yy - 0.45,
     rf"\texttt{{best}} $=$ \{{\texttt{{band}} $= {best[0]}$, \texttt{{cellBitMask}} $=$ \texttt{{{lit(best[1], 27)}}} (bit {WIN_BIT}, {WIN}), \texttt{{candidates}} $= {best[2]}$\}}. "
     rf"No cell has fewer than {best[2]} candidates, and among the {sum(1 for r in SCORED if r[2] == best[2])} scored cells that have {best[2]}, {WIN} has the most unsolved peers ({bestScore}) and comes first. "
     rf"\texttt{{search}} adds \texttt{{candidates - 1}} $= {best[2] - 1}$ to \texttt{{guesses}} ($n$ candidates are $n - 1$ guesses) and tries the values "
     rf"{', '.join(str(d + 1) for d in J['digits'])} in order, each in a copy of the state, with \texttt{{nextValueIn}} as the step of the \texttt{{for}} loop.", 30)

render('fewestcandidatescell')
