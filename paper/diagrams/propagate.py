#!/usr/bin/env python3
# propagate, traced on one real call: the first call in the search of magictour puzzle 96 (the puzzle of the other
# search diagrams) whose first pass finds two or more naked singles in a band that also has two-candidate cells (see
# search_states.cpp). The counters are recomputed here from the masks each band's counting read, and the singles and
# pairs asserted against the real run. Every mask is drawn as its full bit string, high bit on the left. The code
# shown is read from fastbandsolver.hpp. Writes propagate.png next to this script.
from search_common import *

P = DATA['propagate']
PASSES = P['passes']
BAND = 2   # the band traced in detail, in the first pass


# ---------------------------------------------------------------- the code, step by step, in the same order
def count(masks):
    """The counting loop of propagate for one band: once, twice, thrice after each digit."""
    once = twice = thrice = 0
    steps = []
    for bandCells in masks:
        thrice |= twice & bandCells
        twice |= once & bandCells
        once |= bandCells
        steps.append((bandCells, thrice, twice, once))
    return steps


RESULTS = []   # per pass, per band: (once, twice, thrice, singles, pairs)
for p in PASSES:
    row = []
    for b, B in enumerate(p['bands']):
        _, thrice, twice, once = count(B['masks'])[-1]
        assert once == ALL_CELLS
        row.append((once, twice, thrice, once & ~twice & B['unsolved'], twice & ~thrice))
    singlesFound = [(b, i) for b in range(3) for i in range(27) if row[b][3] >> i & 1]
    assert singlesFound == [(b, i) for b, i, _ in p['singles']]
    for b, i, digit in p['singles']:   # nextValueIn's answer is the cell's only digit, from the masks the band counted
        assert [d for d in range(9) if p['bands'][b]['masks'][d] >> i & 1] == [digit]
    RESULTS.append(row)
assert [RESULTS[-1][b][4] for b in range(3)] == P['realPairs']
assert not PASSES[-1]['singles'] and all(p['singles'] for p in PASSES[:-1])

B0 = PASSES[0]['bands'][BAND]
STEPS = count(B0['masks'])
ONCE, TWICE, THRICE, SINGLES, PAIRS = RESULTS[0][BAND]
UNSOLVED = B0['unsolved']
SOLVED_CELLS = ALL_CELLS & ~UNSOLVED
for b, i, digit in PASSES[0]['singles']:
    if b == BAND: assert [d for d in range(9) if B0['masks'][d] >> i & 1] == [digit]

# the board: the state at the start of the first pass, right after update
start = State({'valueToBand': PASSES[0]['start'], 'unsolved': [B['unsolved'] for B in PASSES[0]['bands']]})
# band 2's masks differ from the start only where band 1's single, placed earlier in the same pass, cleared them
EARLY = [(b, i, d) for b, i, d in PASSES[0]['singles'] if b < BAND]
changed = [(d, i) for d in range(9) for i in range(27) if (PASSES[0]['start'][d][BAND] ^ B0['masks'][d]) >> i & 1]
assert len(EARLY) == 1 and len(changed) == 1
EB, EI, ED = EARLY[0]
CD, CI = changed[0]
assert CD == ED and CI % 9 == EI % 9                      # the same digit, in the same column
assert len(start.candidates(BAND, CI)) == 2 and SINGLES >> CI & 1  # a pair at the start, a single when band 2 counts
LATE_SINGLE = cell_name(BAND, CI)
EARLY_NAME = cell_name(EB, EI)

# four cells of the band to follow through the counting: a solved cell, the late single, a pair, a 4+ cell
def ncand(i): return sum(m >> i & 1 for m in B0['masks'])
FOLLOW = [next(i for i in range(27) if SOLVED_CELLS >> i & 1), CI,
          next(i for i in range(27) if PAIRS >> i & 1),
          next(i for i in range(27) if ncand(i) >= 4)]


# ---------------------------------------------------------------- drawing
def depth_text(d): return "at the root, before any guess" if d == 0 else f"{d} guess{'es' if d != 1 else ''} deep"
Y = 2.9
header(Y, r"\texttt{propagate}: everything that follows without guessing, and the cells to guess on",
       r"\textbf{What it is for.} \texttt{search} calls it first on every state. It repeats a pass until a pass places nothing: \texttt{update} runs the band and stack rules on every mask that changed, "
       r"then, band by band, it counts how many digits can still go in each of the 27 cells, all 27 at once. A cell with exactly one (a naked single) gets that digit, with \texttt{clearPeers}; "
       r"a cell with none is a contradiction. When a pass places nothing it returns \textbf{Solved} if no cell has two or more candidates, else \textbf{Open}, with the cells that have exactly two in \texttt{pairs} for \texttt{chooseGuessCell}.\\[3pt]"
       r"\textbf{How it counts.} A cell's count lives in the same bit of three masks, \texttt{once}, \texttt{twice} and \texttt{thrice}: bit $x$ of \texttt{once} is 1 when at least one digit admits cell $x$, of \texttt{twice} at least two, of \texttt{thrice} at least three. "
       r"Adding a digit's mask moves each cell it contains up one step, saturating at three. So \texttt{once \& \textasciitilde{}twice} is ``exactly one'' and \texttt{twice \& \textasciitilde{}thrice} ``exactly two''.\\[3pt]"
       rf"\textbf{{The call drawn here}} is a real one: magictour puzzle {DATA['index'] + 1}, {depth_text(P['depth'])}, the first call in its search where a band has two or more naked singles and two-candidate cells. "
       rf"It makes {len(PASSES)} passes. Band {BAND} of the first pass is traced in detail.")
code(Y - 4.6, source('FastBandSolver::propagate('), 21)

GX, GY, CS = 23.2, Y - 11.4, 0.68
fills = {}
for b in range(3):
    _, _, _, s, pr = RESULTS[0][b]
    for i in range(27):
        rc = (3 * b + i // 9, i % 9)
        if pr >> i & 1: fills[rc] = 'yellow!45'
        if s >> i & 1: fills[rc] = 'green!40'
fills[(3 * BAND + CI // 9, CI % 9)] = 'orange!45'
fills[(3 * EB + EI // 9, EI % 9)] = 'green!40'
board(GX, GY, start, CS, fills=fills)
note(GX - 1.2, GY - 0.25,
     r"The state at the start of the first pass, right after \texttt{update}. Large digits: solved cells; small: candidates. "
     r"\colorbox{green!40}{Green}: naked singles the first pass places. \colorbox{yellow!45}{Yellow}: two candidates when its band is counted. "
     rf"\colorbox{{orange!45}}{{Orange}}: {LATE_SINGLE}, two candidates here, but a single by the time band {BAND} is counted (section 4).", 8.4)

# ---------------------------------------------------------------- 1. one cell's counter
yy = Y - 16.4
section(yy, rf"1. \ One cell at a time: the same bit of \texttt{{once}}, \texttt{{twice}} and \texttt{{thrice}} is a counter that stops at 3. Four cells of band {BAND}, through the nine digits")
note(-0.3, yy - 0.45,
     r"Each row adds one digit's mask. Where the cell's bit of \texttt{bandCells} is 1, the counter goes up one: \texttt{once} first becomes 1, then \texttt{twice}, then \texttt{thrice}; after three it stays. "
     r"The three lines run \emph{highest first}, so \texttt{thrice} is set from the \emph{old} \texttt{twice}, and \texttt{twice} from the old \texttt{once}: a digit moves a cell up one step, never two. A green bit has just been set.", 30)
yy -= 1.75
TW, TC = 7.6, 0.62
for k, i in enumerate(FOLLOW):
    tx = -0.3 + k * TW
    n = ncand(i)
    kind = ("solved" if not UNSOLVED >> i & 1 else
            "naked single" if SINGLES >> i & 1 else "two candidates" if PAIRS >> i & 1 else f"{n} candidates")
    lab(tx, yy + 0.25, rf"\textbf{{{cell_name(BAND, i)}}} (bit {i}): {kind}", 'west', r'\scriptsize')
    heads = [r"\texttt{bandCells}", r"\texttt{thrice}", r"\texttt{twice}", r"\texttt{once}", "count"]
    for c, h in enumerate(heads): lab(tx + 1.9 + c * 1.12, yy - 0.2, h, 'center', r'\fontsize{5.5}{6}\selectfont')
    prev = (0, 0, 0)
    for d, (bc, th, tw, on) in enumerate(STEPS):
        ry = yy - 0.75 - d * 0.42
        lab(tx + 1.2, ry + 0.17, rf"digit {d}", 'east', r'\fontsize{5.5}{6}\selectfont')
        bits = [bc >> i & 1, th >> i & 1, tw >> i & 1, on >> i & 1]
        for c, v in enumerate(bits):
            bx = tx + 1.9 + c * 1.12 - 0.18
            new = c > 0 and v and not prev[c - 1]
            f = ('green!40' if new else 'blue!25') if v else 'white'
            if c == 0 and v: f = 'yellow!60'
            w(rf"\fill[{f}] ({bx},{ry}) rectangle ++(0.36,0.36); \draw[gray!55] ({bx},{ry}) rectangle ++(0.36,0.36);")
            w(rf"\node[font=\scriptsize{r'\bfseries' if v else ''},text={'black' if v else 'gray!75'}] at ({bx + 0.18},{ry + 0.18}) {{{v}}};")
        cnt = bits[1] + bits[2] + bits[3]
        lab(tx + 1.9 + 4 * 1.12, ry + 0.18, "3+" if cnt == 3 else str(cnt), 'center', r'\scriptsize')
        prev = tuple(bits[1:])
    # check: the counter is min(number of digits, 3)
    assert cnt == min(n, 3)
yy -= 0.75 + 9 * 0.42 + 0.2
note(-0.3, yy,
     rf"After the nine digits: the solved cell and {LATE_SINGLE} have count 1 (\texttt{{once}} only), the pair 2, the cell with {ncand(FOLLOW[3])} candidates 3+. "
     r"A solved cell counts 1 too, since its own digit's mask still has it: that is why the singles are \texttt{once \& \textasciitilde{}twice \& state.unsolved[band]}, not just \texttt{once \& \textasciitilde{}twice}.", 30)

# ---------------------------------------------------------------- 2. all 27 cells at once
yy -= 1.3
section(yy, rf"2. \ All 27 cells at once: the counting loop for band {BAND}, one row per digit, as the 27-bit masks it really works on (bit 26 on the left, bit 0 on the right)")
yy -= 1.1
G = groups27(0.05, 0.18)
BW = 0.22
SX = [2.7, 9.8, 16.9, 24.0]
for x, h in zip(SX, [rf"\texttt{{bandCells = valueToBand[digit][{BAND}]}}", r"\texttt{thrice |= twice \& bandCells}",
                     r"\texttt{twice |= once \& bandCells}", r"\texttt{once |= bandCells}"]):
    lab(x + 3.3, yy + 0.55, h, 'center', r'\scriptsize')
prev = (0, 0, 0)
for d, (bc, th, tw, on) in enumerate(STEPS):
    lab(SX[0] - 0.2, yy + 0.11, rf"digit {d} (value {d + 1})", 'east', r'\scriptsize')
    bit_strip(SX[0], yy, bc, G, fills=lambda bit: 'yellow!60', top=False, bw=BW)
    for k, (v, old) in enumerate(zip((th, tw, on), prev)):
        bit_strip(SX[k + 1], yy, v, G, green=v & ~old, top=False, bw=BW)
    prev = (th, tw, on)
    yy -= 0.42
note(-0.3, yy - 0.05,
     r"Each row shows the three counters \emph{after} that digit. A green 1 was set by this digit. \texttt{once} fills up fastest; by the last row every cell is in it, or the cell would have no candidates at all. "
     rf"\texttt{{thrice}} ends with {popcount(THRICE)} cells, \texttt{{twice}} with {popcount(TWICE)}, \texttt{{once}} with all 27.", 30)

# ---------------------------------------------------------------- 3. reading the counters
yy -= 1.4
section(yy, rf"3. \ Reading the counters: the contradiction test, the naked singles and \texttt{{pairs[{BAND}]}}")
yy -= 1.4
labels = band_label(BAND)
rows = [(ONCE, r"\texttt{once}", rf"$=$ \texttt{{ALL\_CELLS}}, so no cell is empty: no \texttt{{Contradiction}}", None, 0),
        (ONCE & ~TWICE, r"\texttt{once \& \textasciitilde{}twice}", rf"exactly one candidate: {popcount(ONCE & ~TWICE)} cells, solved or not", None, 0),
        (UNSOLVED, rf"\texttt{{state.unsolved[{BAND}]}}", rf"{popcount(UNSOLVED)} unsolved cells", None, 0),
        (SINGLES, r"\texttt{singles}", rf"AND of the two above: {', '.join(cell_name(BAND, i) for i in range(27) if SINGLES >> i & 1)}, the naked singles", None, SINGLES),
        (TWICE, r"\texttt{twice}", r"two or more: \texttt{multiple |= twice} (Solved or Open)", None, 0),
        (THRICE, r"\texttt{thrice}", r"three or more", None, 0),
        (PAIRS, rf"\texttt{{pairs[{BAND}] = twice \& \textasciitilde{{}}thrice}}", rf"exactly two: {', '.join(cell_name(BAND, i) for i in range(27) if PAIRS >> i & 1)}", 'yellow!45', 0)]
for k, (v, name, why, fill, green) in enumerate(rows):
    strip(X, yy, v, 27, labels=labels, fills=(lambda bit, f=fill: f) if fill else None, green=green, boxbg=cell_bg, top=(k == 0))
    lab(X - 0.25, yy + W / 2, name)
    lab(strip_end(X, 27) + 0.25, yy + W / 2, why, 'west', r'\scriptsize')
    yy -= 0.85 if k not in (0, 3, 5) else 1.05
note(-0.3, yy + 0.2,
     rf"For each single, \texttt{{nextValueIn(state, band, cellBitMask, 0)}} finds its one digit and \texttt{{clearPeers}} places it: "
     + ', '.join(rf"{cell_name(b, i)} $=$ {d + 1}" for b, i, d in PASSES[0]['singles'] if b == BAND)
     + r". If it finds none (9), an earlier single in the same band has just taken the cell's only digit from it: a contradiction. "
     rf"\texttt{{pairs[{BAND}]}} is overwritten every pass; only the last pass's \texttt{{pairs}} reach \texttt{{chooseGuessCell}}.", 30)

# ---------------------------------------------------------------- 4. the passes
yy -= 1.4
section(yy, r"4. \ The passes of this call, until one places nothing")
yy -= 0.9
C = [-0.3, 1.8, 13.8, 22.0]
for x, t in zip(C, ["pass", r"naked singles placed (\texttt{clearPeers})", r"two-candidate cells per band", "then"]):
    lab(x, yy, t, 'west', r'\scriptsize\bfseries')
yy -= 0.5
for k, p in enumerate(PASSES):
    lab(C[0], yy, str(k + 1), 'west', r'\scriptsize')
    sing = ', '.join(rf"{cell_name(b, i)} $=$ {d + 1} (band {b})" for b, i, d in p['singles']) or r"none: \texttt{placed} stays \texttt{false}"
    lab(C[1], yy, sing, 'west', r'\scriptsize')
    lab(C[2], yy, ', '.join(f"{popcount(RESULTS[k][b][4])}" for b in range(3)), 'west', r'\scriptsize')
    nxt = (r"\texttt{update} again, then count again" if p['singles'] else
           r"\texttt{multiple} $\neq 0$: return \textbf{Open}, with these \texttt{pairs}")
    lab(C[3], yy, nxt, 'west', r'\scriptsize')
    yy -= 0.45
assert any(RESULTS[-1][b][1] for b in range(3))   # multiple != 0: Open
note(-0.3, yy - 0.1,
     rf"\textbf{{Bands are counted one after another, and each sees the singles placed before it.}} In pass 1, band {EB}'s single {EARLY_NAME} $=$ {ED + 1} is placed before band {BAND} is counted, and \texttt{{clearPeers}} removes {ED + 1} from column {EI % 9} in the other bands. "
     rf"So {LATE_SINGLE}, which had {' and '.join(str(d + 1) for d in start.candidates(BAND, CI))} at the start of the pass (orange on the board), has only {next(d for d in start.candidates(BAND, CI) if d != ED) + 1} left when band {BAND} counts it, and is placed in the same pass.\\[3pt]"
     r"Each pass's placements change masks, so the next \texttt{update} has work to do; its band and stack rules can make new singles, which the next count finds. "
     rf"The last pass finds none; its \texttt{{pairs}}, {', '.join(str(popcount(RESULTS[-1][b][4])) for b in range(3))} cells in bands 0, 1, 2, are what \texttt{{search}} hands to \texttt{{chooseGuessCell}}.", 30)

render('propagate')
