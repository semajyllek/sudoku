#!/usr/bin/env python3
# The whole solver as a call tree: every function of fastbandsolver.hpp in the order it runs, what it does to the
# state, and the lookup tables it reads. Writes calltree.png next to this script.
import subprocess, os, shutil, tempfile

here = os.path.dirname(os.path.abspath(__file__))
INDENT, WIDTH, GAP = 1.1, 21.0, 0.32   # cm per tree level, width of a level-0 box, vertical gap between boxes

L = [r"\documentclass[border=12pt]{standalone}",
     r"\usepackage[T1]{fontenc}\usepackage{lmodern}\usepackage{tikz}\usepackage{xcolor}",
     r"\usetikzlibrary{calc}",
     r"\newcommand{\q}{\textquotesingle{}}",
     r"\newcommand{\tbl}[1]{{\setlength{\fboxsep}{1pt}\colorbox{orange!25}{\texttt{#1}}}}",            # a lookup table
     r"\newcommand{\st}[1]{\textcolor{blue!60!black}{\texttt{#1}}}",               # a state field
     r"\begin{document}\begin{tikzpicture}[font=\small,",
     r"  fn/.style={draw=gray!70,fill=#1,rounded corners=2pt,inner sep=5pt,anchor=north west,align=left},",
     r"  link/.style={gray!70!black,thick,->,>=stealth}]"]
w = L.append

# ---------------------------------------------------------------- title and the state
w(r"\node[anchor=west,font=\Large\bfseries] at (0,1.2) {The whole solver: the call tree of \texttt{FastBandSolver}};")
w(r"\node[fn=blue!4,draw=blue!50!black,text width=" + f"{WIDTH + 8.6}" + r"cm] (state) at (0,0.5) {"
  r"\textbf{The state} (246 bytes, copied into the next slot of \texttt{stack} at each guess; all masks use bit \texttt{9 * row + col} of the band)\\[2pt]"
  r"\st{valueToBand[9][3]} \ 27-bit mask per (value, band): the band's cells where the value can still go\\"
  r"\st{checked[9][3]} \ \texttt{valueToBand} as it was the last time the band rules ran on it; \texttt{valueToBand != checked} means ``needs checking''\\"
  r"\st{unsolved[3]} \ 27-bit mask per band: cells not given a digit yet\\"
  r"\st{openRows[9]} \ 9 bits per value: rows (\texttt{band * 3 + row}) where the value is not placed yet\\[3pt]"
  r"Legend: \st{blue} = a state field, \tbl{orange} = a lookup table built at compile time. A line down from a box = that function calls the one below."
  r"};")

# ---------------------------------------------------------------- the tree, in the order things run
# (name, level, fill, body); a body is LaTeX, one \\ per line
TREE = [
    ("solve", 0, 'gray!8',
     r"\textbf{\texttt{solve(in, out)}} \ / \ \textbf{\texttt{countSolutions(in, limit = 2)}}\\"
     r"\texttt{limit = 1} (solve) or 2 (is the solution unique?); \texttt{found = 0}, \texttt{guesses = 0}\\"
     r"\texttt{if (load(stack[0], in)) search(\&stack[0]);} \ then return the solution (solve) or \texttt{found} (countSolutions)"),
    ("load", 1, 'green!6',
     r"\textbf{\texttt{load(state, in)}}: start from the empty board, then put in the clues\\"
     r"for each clue: if its value can no longer go in its cell, two clues clash $\Rightarrow$ \texttt{false}; "
     r"else \texttt{place} it (\texttt{place} clears its row, box and column, so a repeated clue finds its bit already gone)"),
    ("reset", 2, 'green!6',
     r"\textbf{\texttt{reset(state)}}: the empty board\\"
     r"every \st{valueToBand} $=$ \texttt{ALL\_CELLS}, every \st{checked} $= 0$ (so every mask gets checked once), "
     r"every \st{unsolved} $=$ \texttt{ALL\_CELLS}, every \st{openRows} $=$ \texttt{0b111\q111\q111}"),
    ("place1", 2, 'green!6',
     r"\textbf{\texttt{place(state, value, band, cellBitMask)}}: put the value in the cell (clues and guesses)\\"
     r"clear the cell from all 9 values' \st{valueToBand}, give it back to this value, then \texttt{clearPeers}"),
    ("clearPeers", 3, 'green!6',
     r"\textbf{\texttt{clearPeers(state, value, band, cellBitMask)}}: the rest of placing; also used by the naked singles in \texttt{propagate}\\"
     r"\texttt{\&=} \tbl{AFTER\_PLACING[bitIndex]}: clear the cell's row and box in its own band\\"
     r"\texttt{\&=} \tbl{OTHER\_BANDS\_AFTER\_PLACING[bitIndex]} in each other band: clear the cell's column there\\"
     r"\st{unsolved[band]} \texttt{\&= \textasciitilde{}cellBitMask}; \ \st{openRows[value]} loses the cell's row"),
    ("search", 1, 'yellow!10',
     r"\textbf{\texttt{search(state)}}: depth first; \texttt{state} is the slot for this depth, \texttt{state + 1} the slot below\\"
     r"\texttt{progress = propagate(*state, pairs)}: \ \texttt{Contradiction} $\Rightarrow$ return \ $|$ \ \texttt{Solved} $\Rightarrow$ \texttt{record}, return \ $|$ \ \texttt{Open} $\Rightarrow$ guess"),
    ("propagate", 2, 'red!5',
     r"\textbf{\texttt{propagate(state, pairs)}}: everything that follows without guessing; loops until no naked single is left\\"
     r"1. \texttt{update(state)}; false $\Rightarrow$ return \texttt{Contradiction}\\"
     r"2. per band, count the values each cell admits, all 27 cells at once: bit-sliced counters \texttt{once}, \texttt{twice}, \texttt{thrice}\\"
     r"\hspace*{1em}\texttt{once != ALL\_CELLS} $\Rightarrow$ a cell no value can go in: return \texttt{Contradiction}\\"
     r"\hspace*{1em}\texttt{once \& \textasciitilde{}twice \&} \st{unsolved} $=$ naked singles: \texttt{clearPeers} on each "
     r"(the other values are already gone from the cell, so \texttt{place}'s first step is not needed)\\"
     r"\hspace*{1em}\texttt{twice \& \textasciitilde{}thrice} $=$ \texttt{pairs[band]}: the two-candidate cells, kept for guessing\\"
     r"3. nothing placed $\Rightarrow$ return \texttt{Open} if some cell still has two or more candidates, else \texttt{Solved}"),
    ("update", 3, 'red!5',
     r"\textbf{\texttt{update(state)}}: sweep all 27 (value, band) masks, again and again until a sweep changes nothing\\"
     r"for each value, for band 0, 1, 2: \ if \st{valueToBand[value][band]} \texttt{!=} \st{checked[value][band]} "
     r"$\Rightarrow$ \texttt{updateBand<band>(state, value)}; false $\Rightarrow$ contradiction"),
    ("updateBand", 4, 'red!5',
     r"\textbf{\texttt{updateBand<B>(state, value)}}: \texttt{bandCells =} \st{valueToBand[value][B]}, \texttt{lastChecked =} \st{checked[value][B]}\\"
     r"\textbf{1. band rule.} \texttt{boxCandidates} $=$ \tbl{BOXES\_OF\_ROW} of each row, packed (bit \texttt{row * 3 + box})\\"
     r"\hspace*{1em}\texttt{bandCells \&=} \tbl{POSSIBLE\_CELLS[boxCandidates]}: keep only triads on some permutation; empty $\Rightarrow$ false\\"
     r"\hspace*{1em}\st{valueToBand[value][B]} $=$ \st{checked[value][B]} $=$ \texttt{bandCells}\\"
     r"\textbf{2. stack rule}, only if \texttt{bandColumns(bandCells) != bandColumns(lastChecked)}: \texttt{stackRule(state, value)}\\"
     r"\textbf{3. row singles.} \texttt{singleRows =} \tbl{SINGLE\_ROWS}\texttt{[}\tbl{PERMUTATION\_UNION[boxCandidates]}"
     r"\texttt{ | }\tbl{ONE\_COLUMN\_BOXES[columns]}\texttt{ <{}< 9]}\\"
     r"\hspace*{1em}\texttt{newSingleRows = singleRows \&} \st{openRows}; \ \texttt{placedCells = bandCells \&} \tbl{ROWS\_CELLS[newSingleRows]}: one cell per new single row\\"
     r"\hspace*{1em}clear \texttt{placedCells} from the other 8 values of the band, from \st{unsolved[B]}; \st{openRows[value]} loses the rows"),
    ("stackRule", 5, 'red!5',
     r"\textbf{\texttt{stackRule(state, value)}}: the band rule turned sideways, all three bands of the value at once\\"
     r"\texttt{columnsN = bandColumns(digitBands[N])}; per stack: \texttt{columnCandidates} (3 columns $\times$ 3 bands) $\to$ "
     r"\texttt{kept =} \tbl{PERMUTATION\_UNION[columnCandidates]}\\"
     r"\texttt{digitBands[N] \&= columnCells(keptColumnsN)}: may shrink any band, which then no longer matches \st{checked} "
     r"and gets swept again by \texttt{update}"),
    ("record", 2, 'yellow!10',
     r"\textbf{\texttt{record(state)}}: \texttt{found++}; the first solution is written out by "
     r"\textbf{\texttt{writeSolution}}: each value goes into the cells of its \st{valueToBand} masks"),
    ("chooseGuessCell", 2, 'yellow!10',
     r"\textbf{\texttt{chooseGuessCell(state, pairs)}}: of the cells in \texttt{pairs}, the one with the highest \textbf{\texttt{peerScore}} "
     r"(first in board order among ties); band $= -1$ if there are none\\"
     r"\texttt{peerScore} $=$ unsolved peers: \texttt{popcount(}\st{unsolved[band]} \texttt{\&} \tbl{BAND\_PEERS[bitIndex]}\texttt{)} (14 in the band)"
     r" $+$ the cell's column in the other two bands (6)"),
    ("fewestCandidatesCell", 2, 'yellow!10',
     r"\textbf{\texttt{fewestCandidatesCell(state)}}, only when no cell has two candidates (rare): "
     r"the \st{unsolved} cell with the fewest candidates, \texttt{peerScore} breaking ties"),
    ("guess", 2, 'yellow!10',
     r"\textbf{guess}, two candidates: \texttt{first = nextValueIn(..., 0)}, \texttt{second = nextValueIn(..., first + 1)}; \ \texttt{guesses++}\\"
     r"\texttt{memcpy(state + 1, state)}; \ \texttt{place(state + 1, first)}; \ \texttt{search(state + 1)} \hfill $\leftarrow$ recursion\\"
     r"if \texttt{found < limit}: \ \texttt{place(state, second)}; \ \texttt{search(state)} \hfill $\leftarrow$ reuses this slot: its copy is no longer needed\\"
     r"(fewest-candidates fallback: \texttt{guesses += guess.candidates - 1}; copy, \texttt{place}, \texttt{search} for each candidate from \texttt{nextValueIn}, until \texttt{found == limit})"),
]

prev, parents = 'state', {}
for name, level, fill, body in TREE:
    x = level * INDENT
    w(rf"\node[fn={fill},text width={WIDTH - x + 8.6 - 0.2}cm] ({name}) at ($(prev.south -| 0,0) + ({x},{-GAP})$) {{{body}}};"
      .replace('prev', prev))
    parents[level] = name
    if level > 0:
        p = parents[level - 1]
        w(rf"\draw[link] ([xshift=0.35cm]{p}.south west) |- ({name}.west);")
    prev = name

# the recursion: guess calls search again
w(r"\draw[link,dashed,blue!60!black] (guess.east) -- ++(0.6,0) |- node[pos=0.25,right,font=\scriptsize,align=left]"
  r" {recursion:\\a guess runs\\\texttt{search} again\\one level down} (search.east);")

w(r"\end{tikzpicture}\end{document}")
with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, 'calltree.tex'), 'w').write('\n'.join(L))
    r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'calltree.tex'], cwd=tmp, capture_output=True, text=True)
    if r.returncode:
        print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('!') or 'line' in l)[:3000]); raise SystemExit(1)
    subprocess.run(['pdftoppm', '-r', '170', '-png', '-singlefile', 'calltree.pdf', 'calltree'], cwd=tmp, check=True)
    shutil.copy(os.path.join(tmp, 'calltree.png'), os.path.join(here, 'calltree.png'))
