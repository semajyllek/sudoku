/*
FastBandSolver: a Sudoku solver that stores candidates by digit and band, prunes them with two matching rules, and
guesses on the most constrained cells. Same interface as SudokuSolver. paper/ describes it in more detail, with
measurements.

Credits. The layout below, and the idea of updating one (digit, band) at a time with table lookups, are zhouyundong's
(2012), as used in JCZSolve (zhouyundong, champagne and JasonLion) and rust_sudoku (Emerentius). This is an
independent implementation. The stack rule is our addition; tdoku (Tom Dillon) gets the same deductions from its
vertical bands. The fallback branching rule is the classic minimum-remaining-values heuristic.


TERMS

A band is a horizontal strip of three boxes (rows 1-3, 4-6 or 7-9, 27 cells); a stack is a vertical strip of three
boxes. Inside a band, rows and boxes are numbered 0-2 and columns 0-8. The three cells where a row of the band crosses
a box are a mini-row. A candidate is a (cell, digit) pair not ruled out yet. A naked single is a cell with one
candidate left; a row single is a row where a digit has one cell left.


BIT LAYOUT

For each digit (0-8) and band (0-2), one 32-bit word holds the band's 27 cells where the digit can still go. Cell
(row r, column c) of the band is bit 9 * r + c:

    bit:  26 ........ 18   17 ......... 9   8 .......... 0
          row 2, col 8-0   row 1, col 8-0   row 0, col 8-0

Within each row, bits 3k to 3k + 2 are the mini-row of box k. Masks are written in octal in this file because each
octal digit is 3 bits, one mini-row: 07 is one mini-row, 0777 is one row (nine 1-bits), and 0777777777 is the whole
band. A placed digit keeps its cell in its mask, so a solved grid is one where every cell is in exactly one digit's
mask.


THE TWO MATCHING RULES

Band rule. In the finished grid, a digit is once in each row of a band and once in each box of the band, so its three
cells pair the band's rows one-to-one with its boxes. There are only 6 such pairings (the permutations of 3 things).
Write A for the 3 x 3 table with A[r][k] = 1 when the digit still has a candidate in the mini-row of row r and box k.
A pairing that uses only 1-entries of A is a "perfect matching" of rows to boxes. A mini-row that is in no perfect
matching can never hold the digit, so its cells are removed, even if nothing inside the mini-row rules them out. This
covers locked candidates between rows and boxes. If no perfect matching exists, the position is a contradiction.

Example: row 0 can use boxes {0, 1}, row 1 only box {0}, row 2 boxes {1, 2}. Row 1 must take box 0, so row 0 must take
box 1 and row 2 box 2. The mini-rows (row 0, box 0) and (row 2, box 1) are in no perfect matching and are cleared.

Stack rule. The same argument turned sideways: within a stack, a digit is once in each of the stack's three columns
and once in each of its three boxes, and the three boxes of a stack lie in the three different bands. So the digit
pairs the bands one-to-one with the stack's columns, and a (band, column) pair in no such pairing is cleared. This
generalizes "locked columns" (a box whose candidates for the digit lie in one column takes that column from the other
bands). It depends only on which columns each band still uses, so it only has to run when that changes.

Both rules look up a 512-entry table (MATCHABLE) indexed by the 9 bits of a 3 x 3 table.


ONE STEP OF PROPAGATION

For each (digit, band) mask that changed since the rules last ran on it (updateBand):
  1. band rule (three lookups build the table A, one lookup keeps the matchable mini-rows)
  2. stack rule, if the band's set of columns changed
  3. row singles: rows down to one cell place the digit there and take the cell from the other eight digits
Repeat until a full pass changes nothing (update). Then, per band, count how many digits each cell admits
(propagate): a cell with none is a contradiction, a cell with one is a naked single to place, and cells with exactly
two are the candidates for guessing. Repeat the whole thing until no naked single is left.

Every rule only removes candidates that no solution can use, so the order in which they run doesn't change the end
state, and no solution is ever lost.


GUESSING

Pick the cell with two candidates that has the most unsolved cells among its 20 peers (its row, column and box), and
try both digits, depth first. If no cell has two candidates, pick a cell with the fewest candidates (same tie-break)
and try each of them. With a limit of 2 on a puzzle with one solution, the whole search tree is explored, so the tree
size is what matters, and this choice makes it much smaller than guessing on the first two-candidate cell.
*/
#pragma once
#include <array>
#include <bit>
#include <cstdint>
#include <cstring>

class FastBandSolver {
	public:
		// fills out with a solution. false if the clues conflict or there is no solution
		bool solve(const int in[9][9], int out[9][9]);

		// number of solutions, stopping once limit is reached. limit 2 is enough to test uniqueness
		int countSolutions(const int in[9][9], int limit = 2);

		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

		// binary decisions made by the last call: 1 per two-candidate branch, n - 1 for an n-candidate cell
		long long guesses = 0;

	private:
		using Mask = uint32_t;
		static constexpr Mask ALL_CELLS = (1u << 27) - 1;  // 0777777777: every cell of a band

		// the search state, copied at each guess (246 bytes)
		struct State {
			Mask cells[27];     // [digit * 3 + band]: cells where the digit can still go
			Mask checked[27];   // cells[] as it was the last time the band rules ran on it; 0 at the start, so every
			                    // mask gets checked at least once. cells[i] != checked[i] means "needs checking"
			Mask unsolved[3];   // per band: cells not given a digit yet
			uint16_t openRows[9];  // per digit, 9 bits: rows (band * 3 + row) where it isn't placed yet, so each
			                       // placement is made once
		};


		// LOOKUP TABLES, all computed at compile time (8.5 KB in total)

		// 9-bit row of a band -> the boxes (3 bits, bit k for box k) it has candidates in. For example a row with a
		// candidate only in column 3 gives box 1 only, the value 2
		static constexpr std::array<uint8_t, 512> BOXES_OF_ROW = [] {
			std::array<uint8_t, 512> t{};
			for (int r = 0; r < 512; r++) t[r] = (r & 07 ? 1 : 0) | (r & 070 ? 2 : 0) | (r & 0700 ? 4 : 0);
			return t;
		}();

		// 3 x 3 table of 0s and 1s, bit i * 3 + j for entry (i, j) -> the entries that are in some perfect matching,
		// that is, some choice of three 1-entries with one in each row and one in each column. Built by trying the 6
		// permutations: a permutation whose three entries are all set contributes them. 0 if there is none.
		// Used by both rules: rows x boxes for the band rule, bands x columns for the stack rule
		static constexpr std::array<uint16_t, 512> MATCHABLE = [] {
			constexpr int perms[6][3] = {{0, 1, 2}, {0, 2, 1}, {1, 0, 2}, {1, 2, 0}, {2, 0, 1}, {2, 1, 0}};
			std::array<uint16_t, 512> t{};
			for (int m = 0; m < 512; m++) {
				for (auto const &p : perms) {
					int e = 1 << p[0] | 1 << (3 + p[1]) | 1 << (6 + p[2]);
					if ((m & e) == e) t[m] |= e;
				}
			}
			return t;
		}();

		// the band rule in one lookup: table A of mini-rows (bit row * 3 + box) -> the band cells of the mini-rows that
		// are in some perfect matching. ANDing a mask with this removes every candidate no arrangement can use
		static constexpr std::array<Mask, 512> POSSIBLE_CELLS = [] {
			std::array<Mask, 512> t{};
			for (int m = 0; m < 512; m++) {
				int ok = MATCHABLE[m];
				for (int row = 0; row < 3; row++) {
					for (int box = 0; box < 3; box++) {
						if (ok >> (row * 3 + box) & 1) t[m] |= Mask(07) << (row * 9 + box * 3);
					}
				}
			}
			return t;
		}();

		// a band's set of columns (9 bits) -> the boxes (3 bits) that have exactly one column left
		static constexpr std::array<uint8_t, 512> ONE_COLUMN_BOXES = [] {
			std::array<uint8_t, 512> t{};
			for (int c = 0; c < 512; c++) {
				for (int box = 0; box < 3; box++) {
					if (std::popcount(unsigned((c >> (box * 3)) & 07)) == 1) t[c] |= 1 << box;
				}
			}
			return t;
		}();

		// rows (3 bits) that are down to one cell, indexed by the matchable mini-rows (9 bits, from MATCHABLE) and
		// ONE_COLUMN_BOXES << 9. Why this works, after the band rule has run: a row's cells are in its matchable
		// boxes. A row with two matchable boxes has at least two cells. A row with exactly one matchable box k is paired
		// with box k in every perfect matching, so no other row has candidates in box k, and box k's candidates are
		// exactly the row's mini-row. So the row is down to one cell exactly when box k has one column left. This
		// replaces checking each row bit by bit
		static constexpr std::array<uint8_t, 4096> SINGLE_ROWS = [] {
			std::array<uint8_t, 4096> t{};
			for (int i = 0; i < 4096; i++) {
				int miniRows = i & 0777, boxes = i >> 9;
				for (int row = 0; row < 3; row++) {
					int inRow = (miniRows >> (row * 3)) & 07;
					if (std::popcount(unsigned(inRow)) == 1 && (boxes & inRow)) t[i] |= 1 << row;
				}
			}
			return t;
		}();

		// a set of columns (9 bits) -> those columns' cells in a band (the same 9 bits in each of the three rows)
		static constexpr Mask columnCells(Mask columns) { return columns | columns << 9 | columns << 18; }

		// what's left of a digit's own band after placing it at a cell: the cell, and nothing else in its row or box
		static constexpr std::array<Mask, 27> AFTER_PLACING = [] {
			std::array<Mask, 27> t{};
			for (int cell = 0; cell < 27; cell++) {
				int row = cell / 9, box = cell % 9 / 3;
				Mask rowCells = Mask(0777) << (row * 9);
				Mask boxCells = (Mask(07) | Mask(07) << 9 | Mask(07) << 18) << (box * 3);
				t[cell] = (ALL_CELLS & ~rowCells & ~boxCells) | Mask(1) << cell;
			}
			return t;
		}();

		// what's left of the digit's other two bands after placing it at a cell: everything but the cell's column
		static constexpr std::array<Mask, 27> OTHER_BANDS_AFTER_PLACING = [] {
			std::array<Mask, 27> t{};
			for (int cell = 0; cell < 27; cell++) t[cell] = ALL_CELLS & ~((1u | 1u << 9 | 1u << 18) << (cell % 9));
			return t;
		}();

		// rows of a band (3 bits) -> their cells
		static constexpr std::array<Mask, 8> ROWS_CELLS = [] {
			std::array<Mask, 8> t{};
			for (int r = 0; r < 8; r++) t[r] = (r & 1 ? 0777u : 0) | (r & 2 ? 0777u << 9 : 0) | (r & 4 ? 0777u << 18 : 0);
			return t;
		}();

		// the cell's peers inside its band: its row and box, the cell excluded (the peers in the other bands are its
		// column)
		static constexpr std::array<Mask, 27> BAND_PEERS = [] {
			std::array<Mask, 27> t{};
			for (int cell = 0; cell < 27; cell++) t[cell] = ~AFTER_PLACING[cell] & ALL_CELLS;
			return t;
		}();

		// the columns (9 bits) where a band mask has any cell: OR the three rows together
		static constexpr Mask presence(Mask m) { return (m | m >> 9 | m >> 18) & 0777; }

		int limit = 0;
		int found = 0;
		int *solutionOut = nullptr;
		State stack[82];  // one state per guess depth, so a solve allocates nothing

		bool load(State &s, const int in[9][9]);
		template <int B> bool updateBand(State &s, int digit);
		void stackRule(State &s, int digit);
		bool update(State &s);
		int propagate(State &s, Mask pairs[3]);
		void search(State *s);
		static void place(State &s, int digit, int band, Mask cell);
		static int peerScore(State const &s, int band, int index);
		void record(State const &s);
};


inline bool FastBandSolver::solve(const int in[9][9], int out[9][9]) {
	int solution[81];
	limit = 1;
	found = 0;
	guesses = 0;
	solutionOut = solution;
	if (load(stack[0], in)) search(&stack[0]);
	if (!found) return false;
	for (int cell = 0; cell < 81; cell++) out[cell / 9][cell % 9] = solution[cell];
	return true;
}


inline int FastBandSolver::countSolutions(const int in[9][9], int maxSolutions) {
	limit = maxSolutions;
	found = 0;
	guesses = 0;
	solutionOut = nullptr;
	if (load(stack[0], in)) search(&stack[0]);
	return found;
}


// puts the digit in the cell (a single bit of the band): removes the other digits from the cell, and the digit from
// the rest of the cell's row and box (own band) and column (other two bands). Used for clues and guesses
inline void FastBandSolver::place(State &s, int digit, int band, Mask cell) {
	int index = std::countr_zero(cell);  // the cell's bit number, 0-26
	for (int other = 0; other < 9; other++) s.cells[other * 3 + band] &= ~cell;
	s.cells[digit * 3 + band] |= cell;
	s.cells[digit * 3 + band] &= AFTER_PLACING[index];
	s.cells[digit * 3 + (band == 0 ? 1 : 0)] &= OTHER_BANDS_AFTER_PLACING[index];
	s.cells[digit * 3 + (band == 2 ? 1 : 2)] &= OTHER_BANDS_AFTER_PLACING[index];
	s.unsolved[band] &= ~cell;
	s.openRows[digit] &= ~(1u << (band * 3 + index / 9));
}


// starts from every candidate and places the clues, without propagating them yet. false if a clue is no longer a
// candidate, which means it repeats a digit in a row, column or box
inline bool FastBandSolver::load(State &s, const int in[9][9]) {
	for (int i = 0; i < 27; i++) s.cells[i] = ALL_CELLS, s.checked[i] = 0;
	for (int band = 0; band < 3; band++) s.unsolved[band] = ALL_CELLS;
	for (int digit = 0; digit < 9; digit++) s.openRows[digit] = 0777;
	for (int cell = 0; cell < 81; cell++) {
		int digit = in[cell / 9][cell % 9];
		if (!digit) continue;
		Mask bit = Mask(1) << (cell % 27);
		if (!(s.cells[(digit - 1) * 3 + cell / 27] & bit)) return false;
		place(s, digit - 1, cell / 27, bit);
		// clues also clear their column right away, so repeated clues are caught here
		Mask column = columnCells(Mask(1) << (cell % 9));
		for (int band = 0; band < 3; band++) {
			if (band != cell / 27) s.cells[(digit - 1) * 3 + band] &= ~column;
		}
	}
	return true;
}


// the stack rule for one digit: in each stack, keeps the (band, column) pairs that are in some one-to-one pairing of
// the three bands with the stack's three columns. For stack s, build the 3 x 3 table (row = band, column = one of the
// stack's columns) from the bands' column sets, look up MATCHABLE, and keep only the matchable columns in each band.
// Branch-free: processing only the stacks that changed gave the same result but was slower, because the extra
// branches are hard to predict. If a stack has no pairing, the bands lose that stack entirely and the band rule then
// finds the contradiction
inline void FastBandSolver::stackRule(State &s, int digit) {
	Mask *c = &s.cells[digit * 3];
	Mask p0 = presence(c[0]), p1 = presence(c[1]), p2 = presence(c[2]);
	Mask keep0 = 0, keep1 = 0, keep2 = 0;
	for (int shift = 0; shift < 9; shift += 3) {
		Mask ok = MATCHABLE[(p0 >> shift & 07) | (p1 >> shift & 07) << 3 | (p2 >> shift & 07) << 6];
		keep0 |= (ok & 07) << shift;
		keep1 |= (ok >> 3 & 07) << shift;
		keep2 |= (ok >> 6 & 07) << shift;
	}
	c[0] &= columnCells(keep0);
	c[1] &= columnCells(keep1);
	c[2] &= columnCells(keep2);
}


// band rule, stack rule and row singles for one (digit, band). false if the digit has no arrangement left in the band.
// B is a template parameter so the other two bands' positions are constants in each of the three copies.
// always_inline (a GCC/clang attribute): clang otherwise keeps this a function call, which costs about 9% on the hard
// sets
template <int B> [[gnu::always_inline]] inline bool FastBandSolver::updateBand(State &s, int digit) {
	int i = digit * 3 + B;
	Mask cells = s.cells[i];
	Mask before = s.checked[i];

	// band rule: build the 3 x 3 table A (bit row * 3 + box) with one lookup per row, then keep only the cells of
	// matchable mini-rows. Zero means no arrangement: a contradiction
	int miniRows = BOXES_OF_ROW[cells & 0777] | BOXES_OF_ROW[(cells >> 9) & 0777] << 3 | BOXES_OF_ROW[cells >> 18] << 6;
	cells &= POSSIBLE_CELLS[miniRows];
	if (!cells) return false;
	s.cells[i] = s.checked[i] = cells;

	// stack rule, only when the band's set of columns changed (it depends on nothing else). It may clear more of this
	// band; checked[i] keeps the value above, so this band then counts as changed and is checked again in the next pass.
	// The stack rule also covers locked columns, so there is no separate step for them
	Mask columns = presence(cells);
	if (columns != presence(before)) stackRule(s, digit);

	// row singles, found with SINGLE_ROWS (see there for why a table lookup is enough). Only rows where the digit
	// isn't placed yet count, so each placement happens once
	unsigned single = SINGLE_ROWS[MATCHABLE[miniRows] | ONE_COLUMN_BOXES[columns] << 9];
	unsigned open = (s.openRows[digit] >> (B * 3)) & 07;
	unsigned newly = single & open;
	if (newly) {
		Mask placed = cells & ROWS_CELLS[newly];  // one cell per newly single row
		// take the placed cells from every digit of the band, then give this digit its cells back: cheaper than
		// testing "other != digit" in the loop
		for (int other = 0; other < 9; other++) s.cells[other * 3 + B] &= ~placed;
		s.cells[i] = cells;
		s.unsolved[B] &= ~placed;
		s.openRows[digit] &= ~(newly << (B * 3));
	}
	return true;
}


// runs updateBand on every (digit, band) that changed since it was last checked, until a whole pass changes nothing.
// Changes made during a pass (by the stack rule, or row singles clearing other digits) are picked up later in the pass
// or in the next one. Digits with every row placed are not skipped (JCZSolve skips them): skipping saved nothing and
// hid changes to them
inline bool FastBandSolver::update(State &s) {
	bool again = true;
	while (again) {
		again = false;
		for (int digit = 0; digit < 9; digit++) {
			int i = digit * 3;
			if (s.cells[i] != s.checked[i]) {
				if (!updateBand<0>(s, digit)) return false;
				again = true;
			}
			if (s.cells[i + 1] != s.checked[i + 1]) {
				if (!updateBand<1>(s, digit)) return false;
				again = true;
			}
			if (s.cells[i + 2] != s.checked[i + 2]) {
				if (!updateBand<2>(s, digit)) return false;
				again = true;
			}
		}
	}
	return true;
}


// everything that follows without guessing. Returns 0 for a contradiction, 2 for solved, and 1 for open, with the
// cells that have exactly two candidates in pairs.
//
// Counting candidates per cell, for all 27 cells of a band at once: once, twice and thrice are bit-sliced counters.
// Bit x of once is set when at least one digit admits cell x, of twice when at least two do, of thrice when at least
// three do. Adding a digit's mask c updates them highest first, so each uses the old value of the one below it.
// Then once & ~twice is "exactly one" and twice & ~thrice "exactly two".
inline int FastBandSolver::propagate(State &s, Mask pairs[3]) {
	while (true) {
		if (!update(s)) return 0;
		bool placed = false;
		Mask multiple = 0;  // cells with two or more candidates, in any band
		for (int band = 0; band < 3; band++) {
			Mask once = 0, twice = 0, thrice = 0;
			for (int digit = 0; digit < 9; digit++) {
				Mask c = s.cells[digit * 3 + band];
				thrice |= twice & c;
				twice |= once & c;
				once |= c;
			}
			if (once != ALL_CELLS) return 0;  // a cell no digit can go in
			pairs[band] = twice & ~thrice;
			multiple |= twice;
			// naked singles not placed yet. x & (x - 1) clears the lowest set bit, x & -x isolates it
			for (Mask singles = once & ~twice & s.unsolved[band]; singles; singles &= singles - 1) {
				Mask cell = singles & -singles;
				int digit = 0;
				while (digit < 9 && !(s.cells[digit * 3 + band] & cell)) digit++;
				if (digit == 9) return 0;  // an earlier single in this band took the cell's only digit
				// the other digits are already gone from this cell, so only the digit's own masks change
				int index = std::countr_zero(cell);
				s.cells[digit * 3 + band] &= AFTER_PLACING[index];
				s.cells[digit * 3 + (band == 0 ? 1 : 0)] &= OTHER_BANDS_AFTER_PLACING[index];
				s.cells[digit * 3 + (band == 2 ? 1 : 2)] &= OTHER_BANDS_AFTER_PLACING[index];
				s.unsolved[band] &= ~cell;
				s.openRows[digit] &= ~(1u << (band * 3 + index / 9));
				placed = true;
			}
		}
		// solved only when every cell is down to one digit and the rules have run to the end. Then each digit is in
		// every row, column and box (the band rule keeps it in every row and box, the stack rule in every column), and
		// with one digit per cell that makes each digit appear exactly once in each: a valid grid
		if (!placed) return multiple ? 1 : 2;
	}
}


// depth-first search. s is the state for this depth; a guess copies it into s + 1, and the second choice of a
// two-candidate cell reuses s itself, since it isn't needed afterwards
inline void FastBandSolver::search(State *s) {
	Mask pairs[3];
	int progress = propagate(*s, pairs);
	if (progress == 0) return;
	if (progress == 2) {
		record(*s);
		return;
	}

	// the two-candidate cell with the most unsolved peers; the first one in board order among ties
	int bestBand = -1, bestScore = -1;
	Mask bestCell = 0;
	for (int band = 0; band < 3; band++) {
		for (Mask p = pairs[band]; p; p &= p - 1) {
			int score = peerScore(*s, band, std::countr_zero(p));
			if (score > bestScore) bestScore = score, bestBand = band, bestCell = p & -p;
		}
	}
	if (bestBand >= 0) {
		int first = 0;
		while (!(s->cells[first * 3 + bestBand] & bestCell)) first++;
		int second = first + 1;
		while (!(s->cells[second * 3 + bestBand] & bestCell)) second++;
		guesses++;
		State *child = s + 1;
		std::memcpy(child, s, sizeof(State));
		place(*child, first, bestBand, bestCell);
		search(child);
		if (found >= limit) return;
		place(*s, second, bestBand, bestCell);
		search(s);
		return;
	}

	// no cell with two candidates: every candidate of a cell with the fewest, the most unsolved peers breaking ties.
	// This is rare (about 1% of guesses on the hardest puzzles) but tends to happen near the top of the tree, where a
	// cell with five candidates instead of three multiplies the work below it
	int fewest = 10;
	for (int band = 0; band < 3; band++) {
		for (Mask u = s->unsolved[band]; u; u &= u - 1) {
			int index = std::countr_zero(u), n = 0;
			for (int digit = 0; digit < 9; digit++) n += (s->cells[digit * 3 + band] >> index) & 1;
			if (n > fewest) continue;
			int score = peerScore(*s, band, index);
			if (n < fewest || score > bestScore) fewest = n, bestScore = score, bestBand = band, bestCell = u & -u;
		}
	}
	guesses += fewest - 1;
	for (int digit = 0; digit < 9 && found < limit; digit++) {
		if (!(s->cells[digit * 3 + bestBand] & bestCell)) continue;
		State *child = s + 1;
		std::memcpy(child, s, sizeof(State));
		place(*child, digit, bestBand, bestCell);
		search(child);
	}
}


// unsolved cells among the cell's 20 peers: its row and box inside its band, plus its column in the other two bands.
// Packing the two other bands into one 64-bit word counts them with a single popcount. At guessing time the unsolved
// cells are exactly the ones with two or more candidates, so this is the number of peers still open
inline int FastBandSolver::peerScore(State const &s, int band, int index) {
	Mask column = columnCells(Mask(1) << (index % 9));
	int b1 = band == 0 ? 1 : 0, b2 = band == 2 ? 1 : 2;
	uint64_t others = uint64_t(s.unsolved[b1] & column) | uint64_t(s.unsolved[b2] & column) << 32;
	return std::popcount(s.unsolved[band] & BAND_PEERS[index]) + std::popcount(others);
}


// counts a solution, and copies out the first one: each cell's digit is the one whose mask has its bit
inline void FastBandSolver::record(State const &s) {
	if (found++ == 0 && solutionOut) {
		for (int cell = 0; cell < 81; cell++) {
			Mask bit = Mask(1) << (cell % 27);
			int digit = 0;
			while (!(s.cells[digit * 3 + cell / 27] & bit)) digit++;
			solutionOut[cell] = digit + 1;
		}
	}
}
