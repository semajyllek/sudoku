# Shared by the search helper diagrams (chooseguesscell.py, peerscore.py, nextvaluein.py, fewestcandidatescell.py,
# record.py): the real states from search_states.json, the helpers recomputed in Python exactly as the C++ does them
# (each diagram asserts its own results against the real run), and a 9 x 9 board drawer.
import json, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'tables.py')).read()
exec(src.split('# ======================================================================== ONE_COLUMN_BOXES')[0])

DATA = json.load(open(os.path.join(here, 'search_states.json')))
ALL_CELLS = (1 << 27) - 1


def countr_zero(m): return (m & -m).bit_length() - 1
def popcount(m): return bin(m).count('1')
def column_cells(columns): return columns | columns << 9 | columns << 18
def cell_name(band, bitIndex): return f"r{3 * band + bitIndex // 9}c{bitIndex % 9}"


def band_peers(bitIndex):
    """BAND_PEERS[bitIndex]: ~AFTER_PLACING[bitIndex] & ALL_CELLS, the cell's row and box without the cell."""
    row, box = bitIndex // 9, bitIndex % 9 // 3
    rowCells = M9 << (row * 9)
    boxCells = (0b111 | 0b111 << 9 | 0b111 << 18) << (box * 3)
    afterPlacing = (ALL_CELLS & ~rowCells & ~boxCells) | 1 << bitIndex
    return ~afterPlacing & ALL_CELLS


class State:
    def __init__(self, j):
        self.valueToBand = [list(m) for m in j['valueToBand']]
        self.unsolved = list(j['unsolved'])

    def candidates(self, band, bitIndex):
        return [digit for digit in range(9) if self.valueToBand[digit][band] >> bitIndex & 1]


def peer_score_parts(state, band, bitIndex):
    column = column_cells(1 << (bitIndex % 9))
    otherBand1 = 1 if band == 0 else 0
    otherBand2 = 1 if band == 2 else 2
    others = (state.unsolved[otherBand1] & column) | (state.unsolved[otherBand2] & column) << 32
    inBand = state.unsolved[band] & band_peers(bitIndex)
    return dict(column=column, otherBand1=otherBand1, otherBand2=otherBand2, others=others, inBand=inBand,
                score=popcount(inBand) + popcount(others))


def peer_score(state, band, bitIndex): return peer_score_parts(state, band, bitIndex)['score']


def next_value_in(state, band, cellBitMask, startDigit):
    digit = startDigit
    while digit < 9 and (state.valueToBand[digit][band] & cellBitMask) == 0: digit += 1
    return digit


# ---------------------------------------------------------------- drawing
DIGITC = ['red!30', 'orange!35', 'yellow!45', 'green!30', 'teal!30', 'cyan!25', 'blue!22', 'violet!25', 'magenta!22']


def board(GX, GY, state, cs=0.62, fills=None, marks=None, show_candidates=True, caption='', bits=False, corner=None):
    """The 9 x 9 grid of a state: a solved cell shows its value large, an unsolved one its candidates small (value
    1-9 in a 3 x 3 layout). fills = {(row, col): colour}; marks = {(row, col): text drawn large in the cell};
    corner = {(row, col): text drawn in red under the cell's candidates}."""
    fills, marks, corner = fills or {}, marks or {}, corner or {}
    for r in range(9):
        for c in range(9):
            band, bitIndex = r // 3, 9 * (r % 3) + c
            x, y = GX + c * cs, GY + (8 - r) * cs
            w(rf"\fill[{fills.get((r, c), 'white')}] ({x},{y}) rectangle ++({cs},{cs});")
            if bits:
                w(rf"\node[font=\fontsize{{4}}{{5}}\selectfont,text=gray] at ({x + cs - 0.1},{y + cs - 0.09}) {{{bitIndex}}};")
            if (r, c) in corner:  # its candidates on the top half, the corner text on the bottom half
                digits = [str(d + 1) for d in state.candidates(band, bitIndex)]
                values = ' '.join(digits) if len(digits) <= 3 else r'\,'.join(digits)
                size = 6 if len(digits) <= 3 else 5
                w(rf"\node[font=\fontsize{{{size}}}{{7}}\selectfont,inner sep=0pt] at ({x + cs / 2},{y + cs * 0.72}) {{{values}}};")
                w(rf"\node[font=\fontsize{{7}}{{8}}\selectfont\bfseries,text=red!70!black] at ({x + cs / 2},{y + cs * 0.3}) {{{corner[(r, c)]}}};")
            elif (r, c) in marks:
                w(rf"\node[font=\small\bfseries] at ({x + cs / 2},{y + cs / 2}) {{{marks[(r, c)]}}};")
            elif not state.unsolved[band] >> bitIndex & 1:
                value = state.candidates(band, bitIndex)[0] + 1
                w(rf"\node[font=\small\bfseries] at ({x + cs / 2},{y + cs / 2}) {{{value}}};")
            elif show_candidates:
                for digit in state.candidates(band, bitIndex):
                    dx, dy = (digit % 3 + 0.5) * cs / 3, (2.5 - digit // 3) * cs / 3
                    w(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont,text=black!75] at ({x + dx},{y + dy}) {{{digit + 1}}};")
    w(rf"\begin{{scope}}[shift={{({GX},{GY})}}]\draw[gray!50,step={cs}] (0,0) grid ({9 * cs},{9 * cs});\end{{scope}}")
    w(rf"\draw[thick] ({GX},{GY}) rectangle ++({9 * cs},{9 * cs});")
    for q in (3, 6):
        w(rf"\draw[thick] ({GX + q * cs},{GY}) -- ++(0,{9 * cs});")
        w(rf"\draw[very thick] ({GX},{GY + q * cs}) -- ++({9 * cs},0);")
    for c in range(9): lab(GX + (c + 0.5) * cs, GY + 9 * cs + 0.18, f"c{c}", 'center', r'\scriptsize')
    for r in range(9): lab(GX - 0.06, GY + (8.5 - r) * cs, f"r{r}", 'east', r'\scriptsize')
    for b in range(3):
        w(rf"\draw[decorate,decoration={{brace,amplitude=4pt,mirror}}] ({GX - 0.5},{GY + (9 - 3 * b) * cs - 0.05}) -- ({GX - 0.5},{GY + (6 - 3 * b) * cs + 0.05}) node[midway,left=4pt,font=\scriptsize] {{band {b}}};")
    if caption: lab(GX + 4.5 * cs, GY - 0.35, caption, 'center', r'\scriptsize')


def bit_strip(X, Y, val, groups, labels=None, fills=None, red=0, green=0, top=True, boxbg=None, bw=0.40):
    """A strip with its own grouping, for widths that are not 27 (the 64-bit word): groups = [(bits, gap after)], given
    from the high end, e.g. [(5, ...), (9, ...), ...]. Drawn like strip(): high bit on the left, every 0 shown."""
    n = sum(g for g, _ in groups)
    x, bit = X, n - 1
    pos = {}
    for size, gap in groups:
        for _ in range(size):
            pos[bit] = x
            x += bw
            bit -= 1
        x += gap
    end = x
    for bit, x in pos.items():
        bg = boxbg(bit) if boxbg else 'white'
        w(rf"\fill[{bg}] ({x:.3f},{Y}) rectangle ++({bw},{bw});")
        if red >> bit & 1:
            w(rf"\fill[red!22] ({x:.3f},{Y}) rectangle ++({bw},{bw}); \node[font=\scriptsize\bfseries,text=red!75!black] at ({x + bw / 2:.3f},{Y + bw / 2}) {{0}};")
        elif val >> bit & 1:
            f = 'green!40' if green >> bit & 1 else (fills(bit) if fills else 'blue!25')
            w(rf"\fill[{f}] ({x:.3f},{Y}) rectangle ++({bw},{bw}); \node[font=\scriptsize\bfseries] at ({x + bw / 2:.3f},{Y + bw / 2}) {{1}};")
        else:
            w(rf"\node[font=\scriptsize,text=gray!75] at ({x + bw / 2:.3f},{Y + bw / 2}) {{0}};")
        w(rf"\draw[gray!55] ({x:.3f},{Y}) rectangle ++({bw},{bw});")
        if top: w(rf"\node[font=\fontsize{{3.8}}{{4.5}}\selectfont,text=gray] at ({x + bw / 2:.3f},{Y + bw + 0.11}) {{{bit}}};")
        if labels:
            t = labels(bit)
            if t and val >> bit & 1: w(rf"\node[font=\fontsize{{4}}{{5}}\selectfont,text=black!70] at ({x + bw / 2:.3f},{Y - 0.12}) {{{t}}};")
    return pos, end


def band_label(band): return lambda bit: cell_name(band, bit)


def groups27(small=0.08, big=0.26):
    """bit_strip groups for a 27-bit band mask: 3-bit groups, a wider gap between rows (every 9 bits)."""
    return [(3, big if k % 3 == 2 else small) for k in range(9)]


def source(signature):
    """The lines of a function in fastbandsolver.hpp, from the line containing signature to its closing brace, so the
    code in a diagram is the code in the header."""
    lines = open(os.path.join(here, '..', '..', 'fastbandsolver.hpp')).read().split('\n')
    start = next(i for i, l in enumerate(lines) if signature in l)
    end = next(i for i in range(start, len(lines)) if lines[i] == '}')
    return [l.replace('\t', '    ') for l in lines[start:end + 1]]
