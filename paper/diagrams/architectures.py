#!/usr/bin/env python3
# Why the processor decides FastBandSolver vs tdoku: cycles per puzzle = instructions per puzzle / IPC, split into what
# the instruction set does to each solver's instruction count and what the core does to its IPC. Every number is read
# from the raw counter logs in bench/results through bench/results/counters.py, the script that builds the paper's
# tab:instructions and tab:cycles, and the headline ratios are checked against paper.tex. Forum hardest 1106, limit 2.
# Writes architectures.png next to this script.
import glob, math, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'tables.py')).read()
exec(src.split('# ======================================================================== ONE_COLUMN_BOXES')[0])
RESULTS = os.path.join(here, '..', '..', 'bench', 'results')
sys.path.insert(0, RESULTS)
import counters as C

# ---------------------------------------------------------------- the data
def hard(path):
    return {(b, s): d for (b, s, st), d in C.parse(path)[1].items() if st == C.HARD}

M4 = hard(os.path.join(RESULTS, 'm4-counters.txt'))
COUNTED = [hard(f) for f in glob.glob(os.path.join(RESULTS, 'counters', C.COUNTED))]
def counted(build, solver, measure): return sum(d[(build, solver)][measure] for d in COUNTED) / len(COUNTED)

INSTR = {('NEON', 'fastband'): M4[('build', 'fastband')]['instructions'], ('NEON', 'tdoku'): M4[('build', 'tdoku')]['instructions'],
         ('AVX2', 'fastband'): counted('build_v3', 'fastband', 'instructions'), ('AVX2', 'tdoku'): counted('build_v3', 'tdoku', 'instructions'),
         ('AVX-512', 'fastband'): counted('build', 'fastband', 'instructions'), ('AVX-512', 'tdoku'): counted('build', 'tdoku', 'instructions')}
BRANCH = {('M4', s): (M4[('build', s)]['branches'], M4[('build', s)]['branch-misses']) for s in ('fastband', 'tdoku')}
BRANCH.update({('x86', s): (counted('build', s, 'branches'), counted('build', s, 'branch-misses')) for s in ('fastband', 'tdoku')})
L1D = max(d[(b, s)]['l1d-read-misses'] for d in [M4] + COUNTED for (b, s) in d if s in ('fastband', 'tdoku') and 'l1d-read-misses' in d[(b, s)])

def family(name): return 'Intel' if 'Intel' in name else 'AMD'
ROWS = []   # (label, family, counted?, AVX2 cycles fb, td, native cycles fb, td)
m4c = (M4[('build', 'fastband')]['cycles'], M4[('build', 'tdoku')]['cycles'])
ROWS.append(('Apple M4 Max', 'Apple', True, None, None) + m4c)
for name, ext, files in C.MACHINES:
    c, _ = C.machine(files, RESULTS)
    ROWS.append((name.replace('~', ' '), family(name), any('perf' in f for f in files),
                 c[('build_v3', 'fastband')], c[('build_v3', 'tdoku')], c[('build', 'fastband')], c[('build', 'tdoku')]))

# checks against the paper's text and tables
paper = open(os.path.join(here, '..', 'paper.tex')).read()
k = lambda x: f"{x / 1000:.0f}k"
for key, cell in [(('NEON', 'fastband'), '594k'), (('AVX2', 'fastband'), '692k'), (('AVX-512', 'fastband'), '666k'),
                  (('NEON', 'tdoku'), '768k'), (('AVX2', 'tdoku'), '460k'), (('AVX-512', 'tdoku'), '401k')]:
    assert k(INSTR[key]) == cell, (key, k(INSTR[key]))
assert re.search(r'FastBandSolver & 594k & 692k & 666k', paper) and re.search(r'tdoku & 768k & 460k & 401k', paper)
for label, fam, _, fv, tv, fn, tn in ROWS[1:]:
    row = rf"{label.replace('Zen ', 'Zen~')} & {k(fv)} & {k(tv)} & {INSTR[('AVX2', 'fastband')] / fv:.2f} & {INSTR[('AVX2', 'tdoku')] / tv:.2f} & {tv / fv:.2f} & {k(fn)} & {k(tn)} & {tn / fn:.2f}"
    assert row in paper, row
assert abs(m4c[1] / m4c[0] - 1.18) < 0.005   # "a ratio of 1.18, which is its measured lead"

# ---------------------------------------------------------------- drawing
def span(vals, fmt='.2f'):
    """'a--b' over vals, or just 'a' when both ends print the same"""
    lo, hi = format(min(vals), fmt), format(max(vals), fmt)
    return lo if lo == hi else f"{lo}--{hi}"
FB, TD = 'orange!70', 'blue!55'          # FastBandSolver, tdoku
FBL, TDL = 'orange!25', 'blue!18'
GOOD, BAD = 'green!45', 'red!40'
def cell(x, y, wdt, hgt, fill, text='', font=r'\fontsize{5}{6}\selectfont'):
    w(rf"\fill[{fill}] ({x:.3f},{y:.3f}) rectangle ++({wdt:.3f},{hgt:.3f}); \draw[gray!60] ({x:.3f},{y:.3f}) rectangle ++({wdt:.3f},{hgt:.3f});")
    if text: w(rf"\node[font={font}] at ({x + wdt / 2:.3f},{y + hgt / 2:.3f}) {{{text}}};")
def legend(x, y):
    cell(x, y, 0.35, 0.3, FB); lab(x + 0.45, y + 0.15, r"FastBandSolver", 'west', r'\scriptsize')
    cell(x + 3.0, y, 0.35, 0.3, TD); lab(x + 3.45, y + 0.15, r"tdoku", 'west', r'\scriptsize')

Y = 2.9
header(Y, r"Why the processor decides: what each instruction set and each core does with tdoku's and FastBandSolver's code",
       r"\textbf{The equation.} Time per puzzle $=$ instructions per puzzle $\div$ IPC (instructions per cycle) $\div$ clock. The clock says nothing about the code, so this compares \textbf{cycles} $=$ instructions $\div$ IPC. "
       r"Two different things change between machines: the \textbf{instruction set} (NEON, AVX2, AVX-512) decides how many instructions each solver needs, and the \textbf{core} decides how many of them it runs per cycle. "
       r"Every number here is forum hardest 1106 at limit 2, read from the raw counter logs in \texttt{bench/results} through \texttt{counters.py}, the script that makes the paper's instruction and cycle tables (section 8.2), and checked against those tables.\\[3pt]"
       r"\textbf{The answer in one line.} On the M4, NEON's 128-bit registers cost tdoku instructions, so FastBandSolver wins (1.18). On x86, tdoku needs only two thirds of FastBandSolver's instructions, and FastBandSolver has to make that up with a higher IPC: "
       r"AMD cores let it (about level), Intel cores do not, and AVX-512 widens Intel's lead further (0.68--0.71).")

# ---------------------------------------------------------------- 1. the two programs
yy = Y - 4.4
section(yy, r"1. \ What each solver asks of the processor")
yy -= 0.8
# tdoku: one box in a 256-bit register, 16 lanes of 16 bits as a 4 x 4 matrix
lab(-0.3, yy, r"\textbf{tdoku: SIMD, branch-free.} Each box is one 256-bit vector of sixteen 16-bit lanes:", 'west', r'\scriptsize')
TX, TY, LS = 0.2, yy - 3.0, 0.62
for r in range(4):
    for c in range(4):
        inner = r < 3 and c < 3
        cell(TX + c * LS, TY + (3 - r) * LS, LS, LS, TDL if inner else 'gray!15',
             (f"cell {r * 3 + c}" if inner else "triads"), r'\fontsize{4.5}{5}\selectfont')
lab(TX + 4 * LS + 0.2, TY + 2 * LS, r"\begin{tabular}{l}$3\times 3$: the nine cells' candidate sets\\(9 bits each, one bit per digit)\\grey: the box's triad variables\end{tabular}", 'west', r'\fontsize{6}{7}\selectfont')
note(-0.3, TY - 0.15,
     r"Propagation is message passing between boxes and bands, written as vector AND, OR, shuffle, compare and min across lanes, run over the grid \emph{every time, without asking} whether anything changed: few branches. "
     r"\\[2pt]\textbf{How it uses each instruction set.} AVX2: one 256-bit instruction per operation. AVX-512 (on 128/256-bit vectors, never 512-bit registers): three-input logic, compares into mask registers, vector bit counts, so fewer instructions again. "
     r"NEON (M4): registers are 128 bits, so every 256-bit operation becomes two instructions, and some x86 operations, such as pulling a bit mask out of a vector, take several.", 14.6)
# FastBandSolver: one (digit, band) in a 32-bit register
FX = 15.6
lab(FX, yy, r"\textbf{FastBandSolver: scalar, skips work with branches.} One (digit, band) is one 32-bit integer:", 'west', r'\scriptsize')
BX, BY, BW = FX + 0.3, yy - 1.2, 0.38
for i in range(32):
    bit = 31 - i
    x = BX + i * BW + (0.12 if i >= 5 else 0) + 0.12 * max(0, (i - 5) // 9)
    used = bit < 27
    fill = ['blue!25', 'orange!35', 'teal!30'][bit // 9] if used else 'gray!15'
    cell(x, BY, BW, BW, fill, str(bit), r'\fontsize{4}{5}\selectfont')
lab(BX, BY - 0.3, r"bits 31--27 always 0", 'west', r'\fontsize{5.5}{6}\selectfont')
lab(BX + 5 * BW + 0.6, BY - 0.3, r"row 2 of the band \hspace{1.6cm} row 1 \hspace{2.4cm} row 0: bit $9\times$row$+$column", 'west', r'\fontsize{5.5}{6}\selectfont')
note(FX - 0.3, BY - 0.6,
     r"Operations are 32-bit AND, OR, shifts, \texttt{std::popcount} and small table loads, which every instruction set has: the same code compiles unchanged for ARM and x86, and the instruction set barely changes it. "
     r"\\[2pt]\textbf{How it saves work.} \texttt{update} runs a band only if its mask changed since it was last checked:\\"
     r"\hspace*{1em}\texttt{if (state.valueToBand[digit][0] != state.checked[digit][0])}\\"
     r"It asks this 22{,}540 times per puzzle and the answer is yes only 15\% of the time, so it skips 85\% of band updates. That is why it needs few instructions. "
     r"The price: which bands changed follows no pattern a predictor can learn, so these branches mispredict (section 5).", 15.0)

# ---------------------------------------------------------------- 2. instructions per puzzle
yy -= 6.6
section(yy, r"2. \ The instruction set decides the instruction count: instructions per puzzle")
legend(25.0, yy - 0.05)
yy -= 0.95
SC = 15.0 / 800e3   # cm per instruction
GROUPS = [('NEON', r"ARM NEON (M4)"), ('AVX2', r"x86 AVX2 build (one binary for every x86 machine)"), ('AVX-512', r"x86 AVX-512 build (native, counted on the c4)")]
for g, name in GROUPS:
    lab(5.4, yy - 0.2, name, 'east', r'\scriptsize')
    for s, col, dy in (('fastband', FB, 0), ('tdoku', TD, -0.4)):
        v = INSTR[(g, s)]
        w(rf"\fill[{col}] (5.6,{yy + dy - 0.35:.2f}) rectangle ({5.6 + v * SC:.3f},{yy + dy - 0.05:.2f});")
        lab(5.7 + v * SC, yy + dy - 0.2, rf"{v / 1000:.0f}k", 'west', r'\scriptsize')
    yy -= 1.0
for x in (0, 200e3, 400e3, 600e3, 800e3):
    w(rf"\draw[gray!50] ({5.6 + x * SC:.2f},{yy + 0.2}) -- ++(0,0.1); \node[font=\fontsize{{5}}{{6}}\selectfont,text=gray] at ({5.6 + x * SC:.2f},{yy + 0.02}) {{{x / 1000:.0f}k}};")
ratioN = INSTR[('NEON', 'tdoku')] / INSTR[('AVX2', 'tdoku')]
note(22.0, yy + 3.15,
     rf"tdoku needs \textbf{{{ratioN:.2f}$\times$}} the instructions on NEON as with AVX2, and {INSTR[('NEON', 'tdoku')] / INSTR[('AVX-512', 'tdoku')]:.2f}$\times$ as with AVX-512: this is where vector width matters. "
     rf"FastBandSolver goes the other way, {INSTR[('NEON', 'fastband')] / 1000:.0f}k on ARM against {INSTR[('AVX2', 'fastband')] / 1000:.0f}k on x86 (the paper does not break down why). "
     rf"So tdoku needs {INSTR[('NEON', 'tdoku')] / INSTR[('NEON', 'fastband')]:.2f}$\times$ FastBandSolver's instructions on the M4, but only {INSTR[('AVX2', 'tdoku')] / INSTR[('AVX2', 'fastband')]:.2f}$\times$ (AVX2) and {INSTR[('AVX-512', 'tdoku')] / INSTR[('AVX-512', 'fastband')]:.2f}$\times$ (AVX-512) on x86.", 9.0)

# ---------------------------------------------------------------- 3. IPC
yy -= 0.9
section(yy, r"3. \ The core decides the IPC: the \emph{same} AVX2 binary, so the same instructions, on every x86 machine (M4: its own build)")
legend(25.0, yy - 0.05)
yy -= 1.2
IX0, ISC, LO, HI = 7.0, 9.0, 1.3, 2.7
def ix(v): return IX0 + (v - LO) * ISC
for v in [1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6]:
    w(rf"\draw[gray!25] ({ix(v):.2f},{yy + 0.3}) -- ({ix(v):.2f},{yy - 0.42 * len(ROWS) - 0.1});")
    lab(ix(v), yy + 0.45, f"{v:.1f}", 'center', r'\fontsize{5}{6}\selectfont')
lab(ix(HI) + 0.1, yy + 0.45, r"IPC", 'west', r'\scriptsize')
IPC = []
prevfam = None
for label, fam, cnt, fv, tv, fn, tn in ROWS:
    if fam != prevfam and prevfam is not None:
        w(rf"\draw[gray!50,dashed] (-0.3,{yy + 0.21}) -- ({ix(HI)},{yy + 0.21});")
    prevfam = fam
    if fam == 'Apple': fi, ti = INSTR[('NEON', 'fastband')] / fn, INSTR[('NEON', 'tdoku')] / tn
    else: fi, ti = INSTR[('AVX2', 'fastband')] / fv, INSTR[('AVX2', 'tdoku')] / tv
    IPC.append((label, fam, fi, ti))
    lab(IX0 - 0.3, yy, label + ('' if cnt else r'$^*$'), 'east', r'\scriptsize')
    w(rf"\draw[gray!60] ({ix(min(fi, ti)):.3f},{yy}) -- ({ix(max(fi, ti)):.3f},{yy});")
    for v, col in ((fi, FB), (ti, TD)):
        w(rf"\fill[{col}] ({ix(v):.3f},{yy}) circle (0.11);")
    lab(ix(max(fi, ti)) + 0.25, yy, rf"{fi / ti:.2f}$\times$", 'west', r'\fontsize{6}{7}\selectfont')
    yy -= 0.42
amd = [r for r in IPC if r[1] == 'AMD']; intel = [r for r in IPC if r[1] == 'Intel']
rng = lambda rows, i: f"{min(r[i] for r in rows):.2f}--{max(r[i] for r in rows):.2f}"
note(ix(HI) + 1.4, yy + 0.42 * len(ROWS) + 0.2,
     rf"Each line joins the two solvers' IPC; the number is FastBandSolver's IPC over tdoku's. "
     rf"tdoku: \textbf{{{rng(intel, 3)}}} on Intel against {rng(amd, 3)} on AMD. FastBandSolver: {rng(intel, 2)} on Intel against \textbf{{{rng(amd, 2)}}} on AMD. "
     rf"So the same two instruction streams are run very differently: Intel cores favour tdoku's vector stream, AMD cores FastBandSolver's branchy scalar one. "
     rf"FastBandSolver needs an IPC {INSTR[('AVX2', 'fastband')] / INSTR[('AVX2', 'tdoku')]:.2f}$\times$ tdoku's just to break even; on AMD it gets {min(r[2] / r[3] for r in amd):.2f}--{max(r[2] / r[3] for r in amd):.2f}$\times$, on Intel only {min(r[2] / r[3] for r in intel):.2f}--{max(r[2] / r[3] for r in intel):.2f}$\times$.\\[3pt]"
     r"\textbf{Measured, not explained:} the paper has not isolated which features of the Intel cores run tdoku's stream faster per cycle.\\[3pt]"
     r"$^*$ cycles derived from time $\times$ the measured clock; others counted (M4 by \texttt{kperf}, the 8581C by \texttt{perf}).", 9.6)

# ---------------------------------------------------------------- 4. putting them together
yy -= 0.5
section(yy, r"4. \ Cycles $=$ instructions $\div$ IPC: the two factors multiply into the result. Ratio above 1: FastBandSolver takes fewer cycles")
yy -= 0.7
CHARTS = [(8.6, r"fewer instructions:\\tdoku instr.\ $\div$ FastBand instr."), (14.6, r"$\times$ \ higher IPC:\\FastBand IPC $\div$ tdoku IPC"),
          (20.6, r"$=$ \ cycle ratio, same binary\\(AVX2 build; M4 native)"), (26.6, r"native build\\(AVX-512 where the processor has it)")]
LK = 3.2   # cm per doubling
for cx, t in CHARTS:
    lab(cx, yy, rf"\begin{{tabular}}{{c}}{t}\end{{tabular}}", 'center', r'\fontsize{6}{7}\selectfont')
yy -= 0.65
top = yy + 0.25
for label, fam, cnt, fv, tv, fn, tn in ROWS:
    if fam == 'Apple':
        fI = INSTR[('NEON', 'tdoku')] / INSTR[('NEON', 'fastband')]
        fP = (INSTR[('NEON', 'fastband')] / fn) / (INSTR[('NEON', 'tdoku')] / tn)
        same, native = tn / fn, tn / fn
    else:
        fI = INSTR[('AVX2', 'tdoku')] / INSTR[('AVX2', 'fastband')]
        fP = (INSTR[('AVX2', 'fastband')] / fv) / (INSTR[('AVX2', 'tdoku')] / tv)
        same, native = tv / fv, tn / fn
    assert abs(fI * fP - same) < 1e-9
    lab(5.6, yy, label + ('' if cnt else r'$^*$'), 'east', r'\scriptsize')
    for (cx, _), v in zip(CHARTS, (fI, fP, same, native)):
        x1 = cx + LK * math.log2(v)
        w(rf"\fill[{GOOD if v >= 1 else BAD}] ({min(cx, x1):.3f},{yy - 0.15}) rectangle ({max(cx, x1):.3f},{yy + 0.15});")
        lab(x1 + (0.1 if v >= 1 else -0.1), yy, f"{v:.2f}", 'west' if v >= 1 else 'east', r'\fontsize{6}{7}\selectfont')
    yy -= 0.42
for cx, _ in CHARTS:
    w(rf"\draw[black!70] ({cx},{top}) -- ({cx},{yy + 0.2});")
    lab(cx, yy + 0.05, "1", 'center', r'\fontsize{5}{6}\selectfont')
yy -= 0.2
note(-0.3, yy,
     r"Bars are on a log scale, so the first two multiply into the third by adding lengths. Green favours FastBandSolver, red tdoku. "
     r"\textbf{M4:} more instructions for tdoku (NEON) outweigh its slightly higher IPC. "
     r"\textbf{AMD:} tdoku's fewer instructions and FastBandSolver's higher IPC about cancel. "
     r"\textbf{Intel:} the IPC advantage is too small to cover the instructions. "
     rf"\textbf{{Last column:}} the native build gives tdoku AVX-512 on Zen 4/5 and Intel. It removes {span([100 * (1 - r[6] / r[4]) for r in ROWS if r[1] == 'Intel'], '.0f')}\% of tdoku's cycles on Intel and {span([100 * (1 - r[6] / r[4]) for r in ROWS if 'Zen 4' in r[0] or 'Zen 5' in r[0]], '.0f')}\% on Zen 4/5, "
     rf"and changes FastBandSolver's by at most {max(abs(r[3] / r[5] - 1) for r in ROWS[1:]) * 100:.0f}\%. So on Intel the ratio falls to the measured {span([r[6] / r[5] for r in ROWS if r[1] == 'Intel'])}. "
     r"Vector width is the ARM story, not the x86 one: Zen 3 runs tdoku's 256-bit vectors natively and is still level.", 30)

# ---------------------------------------------------------------- 5. branches
yy -= 2.0
section(yy, r"5. \ The price of skipping work: branches and mispredictions per puzzle (native builds; x86 counted on the c4)")
legend(25.0, yy - 0.05)
yy -= 0.95
BSC = 7.0 / 55e3
MSC = 7.0 / 7e3
lab(5.0, yy + 0.4, r"branches", 'center', r'\scriptsize\bfseries')
lab(15.5, yy + 0.4, r"branch mispredictions", 'center', r'\scriptsize\bfseries')
for m, name in (('M4', 'M4'), ('x86', 'x86 (Emerald Rapids)')):
    lab(1.3, yy - 0.2, name, 'east', r'\scriptsize')
    for s, col, dy in (('fastband', FB, 0), ('tdoku', TD, -0.4)):
        br, mis = BRANCH[(m, s)]
        w(rf"\fill[{col}] (1.5,{yy + dy - 0.35:.2f}) rectangle ({1.5 + br * BSC:.3f},{yy + dy - 0.05:.2f});")
        lab(1.6 + br * BSC, yy + dy - 0.2, rf"{br / 1000:.1f}k", 'west', r'\scriptsize')
        w(rf"\fill[{col}] (12.0,{yy + dy - 0.35:.2f}) rectangle ({12.0 + mis * MSC:.3f},{yy + dy - 0.05:.2f});")
        lab(12.1 + mis * MSC, yy + dy - 0.2, rf"{mis / 1000:.1f}k \ (MPKI {1000 * mis / INSTR[('NEON' if m == 'M4' else 'AVX-512', s)]:.1f})", 'west', r'\scriptsize')
    yy -= 1.0
fbm, tdm = BRANCH[('x86', 'fastband')][1], BRANCH[('x86', 'tdoku')][1]
note(21.8, yy + 2.15,
     rf"FastBandSolver mispredicts {fbm / tdm:.1f}$\times$ as often as tdoku on x86 and {BRANCH[('M4', 'fastband')][1] / BRANCH[('M4', 'tdoku')][1]:.1f}$\times$ on the M4: about the same on both, so it is the algorithm, not the processor. "
     r"84\% of them are in \texttt{update}'s ``has this band changed?'' tests. Removing those branches made nothing faster (\cref{sec:negative}): they are the price of skipping 85\% of the band updates. "
     rf"Memory plays no part: fewer than {math.ceil(L1D)} L1 data cache misses per puzzle for either solver, against about 300k cycles.".replace(r'\cref{sec:negative}', 'section 10'), 9.2)

# ---------------------------------------------------------------- 6. summary
yy -= 0.6
section(yy, r"6. \ Per architecture: what tdoku gets from it, what FastBandSolver gets from it")
yy -= 0.8
SC6 = [-0.3, 4.2, 12.4, 20.6, 27.6]
for x, t in zip(SC6, ["processor", "tdoku", "FastBandSolver", "why the result", "cycles ratio"]):
    lab(x, yy, t, 'west', r'\scriptsize\bfseries')
yy -= 0.55
zen3 = [r for r in ROWS if 'Zen 3' in r[0]]; zen45 = [r for r in ROWS if 'Zen 4' in r[0] or 'Zen 5' in r[0]]
intelR = [r for r in ROWS if r[1] == 'Intel']
ipcs = {lab_: (fi, ti) for lab_, _, fi, ti in IPC}
def ipc(rows, i): return span([ipcs[r[0]][i] for r in rows])
def ipcratio(rows): return span([ipcs[r[0]][0] / ipcs[r[0]][1] for r in rows])
def native(rows): return span([r[6] / r[5] for r in rows])
def cut(rows): return span([100 * (1 - r[6] / r[4]) for r in rows], '.0f')
fm4, tm4 = ipcs['Apple M4 Max']
x86min = min(r[5] for r in ROWS[1:])
SUMMARY = [
    ("Apple M4 (NEON)", rf"256-bit operations split in two: {INSTR[('NEON', 'tdoku')] / 1000:.0f}k instructions; IPC {tm4:.2f}",
     rf"{m4c[0] / 1000:.0f}k cycles, its fewest anywhere ({100 * (1 - m4c[0] / x86min):.0f}\% under its best x86 native build); IPC {fm4:.2f}",
     rf"instructions favour FastBand {INSTR[('NEON', 'tdoku')] / INSTR[('NEON', 'fastband')]:.2f}$\times$; IPC favours tdoku {fm4 / tm4:.2f}$\times$", f"{m4c[1] / m4c[0]:.2f}"),
    ("AMD Zen 3 (AVX2)", rf"native 256-bit vectors: {INSTR[('AVX2', 'tdoku')] / 1000:.0f}k instructions, but IPC only {ipc(zen3, 1)}",
     rf"IPC {ipc(zen3, 0)}, {ipcratio(zen3)}$\times$ tdoku's", r"the two factors cancel", native(zen3)),
    ("AMD Zen 4/5 (AVX-512)", rf"IPC {ipc(zen45, 1)}; AVX-512 instructions cut its cycles {cut(zen45)}\%", rf"IPC {ipc(zen45, 0)}, {ipcratio(zen45)}$\times$ tdoku's",
     rf"near level on the AVX2 build ({span([r[4] / r[3] for r in zen45])}); AVX-512 tips it to tdoku", native(zen45)),
    ("Intel (AVX-512)", rf"IPC {ipc(intelR, 1)} on its vector stream, and AVX-512 cuts {cut(intelR)}\% more", rf"IPC {ipc(intelR, 0)}: only {ipcratio(intelR)}$\times$ tdoku's",
     rf"IPC too small to cover {INSTR[('AVX2', 'tdoku')] / INSTR[('AVX2', 'fastband')]:.2f}$\times$ the instructions (which core features cause it is not isolated)", native(intelR)),
]
for row in SUMMARY:
    for x, t, wd in zip(SC6, row, [4.3, 8.0, 8.0, 6.8, 2.5]):
        w(rf"\node[font=\scriptsize,anchor=north west,align=left,text width={wd}cm] at ({x},{yy + 0.15}) {{{t}}};")
    yy -= 0.75

render('architectures')
