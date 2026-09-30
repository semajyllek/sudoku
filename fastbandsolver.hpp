/*
FastBandSolver: a band solver with a stack rule and peer-count branching.

The board is stored by digit and band: a 27-bit mask per (digit, band) of the cells where the digit can still go, bit
row * 9 + column within the band. This layout and the idea of updating one (digit, band) at a time with table lookups
are zhouyundong's (2012), as used in JCZSolve (JasonLion, champagne and others) and rust_sudoku; this is an independent
implementation.

Rules, applied to a (digit, band) whenever its mask changed:
- band rule: the digit's three rows in the band use three different boxes. Keep only mini-rows (row, box) that lie on
  such an arrangement (a perfect matching of rows to boxes).
- stack rule: within each stack the three bands use three different columns for the digit. Keep only (band, column)
  pairs that lie on such an arrangement. This generalizes locked columns; tdoku gets the same effect from its
  vertical bands. It only depends on which columns the bands have, so it runs when those change.
- row singles: a row down to one cell places the digit there and takes the cell from the other digits.
Then naked singles (cells down to one digit), until nothing changes.

Branching: the cell with two candidates that has the most unsolved cells in its row, column and box (fsss2 describes
similar peer-count choices). With no such cell, a cell with the fewest candidates (the usual minimum remaining values
rule), with the same tie-break.

Same interface as SudokuSolver.
*/
#pragma once
#include <array>
#include <bit>
#include <cstdint>
#include <cstring>

class FastBandSolver {
	public:
		bool solve(const int in[9][9], int out[9][9]);
		int countSolutions(const int in[9][9], int limit = 2);
		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

		// binary decisions made by the last call: 1 per two-candidate branch, n - 1 for an n-candidate cell
		long long guesses = 0;

	private:
		using Mask = uint32_t;
		static constexpr Mask ALL_CELLS = (1u << 27) - 1;

		struct State {
			Mask cells[27];     // [digit * 3 + band]
			Mask checked[27];   // cells[] when the band rules last ran on it
			Mask unsolved[3];   // cells without a digit, per band
			uint16_t openRows[9];  // per digit: rows (band * 3 + row) where it isn't placed yet
		};

		// the boxes (3 bits) a 9-bit row touches
		static constexpr std::array<uint8_t, 512> BOXES_OF_ROW = [] {
			std::array<uint8_t, 512> t{};
			for (int r = 0; r < 512; r++) t[r] = (r & 07 ? 1 : 0) | (r & 070 ? 2 : 0) | (r & 0700 ? 4 : 0);
			return t;
		}();

		// 3x3 0-1 matrix, bit row * 3 + column -> its entries that lie on some perfect matching
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

		// mini-rows (bit row * 3 + box) -> the band cells of the mini-rows that lie on some arrangement
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

		// boxes (3 bits) whose cells in a band are all in one column, from the band's columns
		static constexpr std::array<uint8_t, 512> ONE_COLUMN_BOXES = [] {
			std::array<uint8_t, 512> t{};
			for (int c = 0; c < 512; c++) {
				for (int box = 0; box < 3; box++) {
					if (std::popcount(unsigned((c >> (box * 3)) & 07)) == 1) t[c] |= 1 << box;
				}
			}
			return t;
		}();

		// rows (3 bits) down to one cell, from the matchable mini-rows (bit row * 3 + box) and ONE_COLUMN_BOXES << 9:
		// a row with one matchable box has that box to itself, so it has one cell when the box has one column
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

		static constexpr Mask columnCells(Mask columns) { return columns | columns << 9 | columns << 18; }

		// what's left of the digit's band after placing it at a cell: the cell, and nothing else in its row or box
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

		// what's left of the digit's other bands after placing it at a cell: everything but the cell's column
		static constexpr std::array<Mask, 27> OTHER_BANDS_AFTER_PLACING = [] {
			std::array<Mask, 27> t{};
			for (int cell = 0; cell < 27; cell++) t[cell] = ALL_CELLS & ~((1u | 1u << 9 | 1u << 18) << (cell % 9));
			return t;
		}();

		// rows (3 bits) -> their cells
		static constexpr std::array<Mask, 8> ROWS_CELLS = [] {
			std::array<Mask, 8> t{};
			for (int r = 0; r < 8; r++) t[r] = (r & 1 ? 0777u : 0) | (r & 2 ? 0777u << 9 : 0) | (r & 4 ? 0777u << 18 : 0);
			return t;
		}();

		// the cell's row and box within its band, the cell excluded
		static constexpr std::array<Mask, 27> BAND_PEERS = [] {
			std::array<Mask, 27> t{};
			for (int cell = 0; cell < 27; cell++) t[cell] = ~AFTER_PLACING[cell] & ALL_CELLS;
			return t;
		}();

		static constexpr Mask presence(Mask m) { return (m | m >> 9 | m >> 18) & 0777; }

		int limit = 0;
		int found = 0;
		int *solutionOut = nullptr;
		State stack[82];  // one state per guess depth

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


// puts the digit in the cell: removes the other digits from the cell, and the digit from the rest of the cell's row,
// column and box
inline void FastBandSolver::place(State &s, int digit, int band, Mask cell) {
	int index = std::countr_zero(cell);
	for (int other = 0; other < 9; other++) s.cells[other * 3 + band] &= ~cell;
	s.cells[digit * 3 + band] |= cell;
	s.cells[digit * 3 + band] &= AFTER_PLACING[index];
	s.cells[digit * 3 + (band == 0 ? 1 : 0)] &= OTHER_BANDS_AFTER_PLACING[index];
	s.cells[digit * 3 + (band == 2 ? 1 : 2)] &= OTHER_BANDS_AFTER_PLACING[index];
	s.unsolved[band] &= ~cell;
	s.openRows[digit] &= ~(1u << (band * 3 + index / 9));
}


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


// keeps the (band, column) pairs of each stack that lie on an arrangement of the three bands onto three columns
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
// always_inline: clang otherwise keeps it a call, which costs about 9% on the hard sets
template <int B> [[gnu::always_inline]] inline bool FastBandSolver::updateBand(State &s, int digit) {
	int i = digit * 3 + B;
	Mask cells = s.cells[i];
	Mask before = s.checked[i];
	int miniRows = BOXES_OF_ROW[cells & 0777] | BOXES_OF_ROW[(cells >> 9) & 0777] << 3 | BOXES_OF_ROW[cells >> 18] << 6;
	cells &= POSSIBLE_CELLS[miniRows];
	if (!cells) return false;
	s.cells[i] = s.checked[i] = cells;
	// the stack rule covers locked columns, and both depend only on which columns the band has left
	Mask columns = presence(cells);
	if (columns != presence(before)) stackRule(s, digit);

	// rows down to one cell, where the digit isn't placed yet
	unsigned single = SINGLE_ROWS[MATCHABLE[miniRows] | ONE_COLUMN_BOXES[columns] << 9];
	unsigned open = (s.openRows[digit] >> (B * 3)) & 07;
	unsigned newly = single & open;
	if (newly) {
		Mask placed = cells & ROWS_CELLS[newly];
		for (int other = 0; other < 9; other++) s.cells[other * 3 + B] &= ~placed;
		s.cells[i] = cells;
		s.unsolved[B] &= ~placed;
		s.openRows[digit] &= ~(newly << (B * 3));
	}
	return true;
}


// the band rules on every (digit, band) that changed since they last ran on it, until nothing changes
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


// everything that follows without guessing. 0: contradiction, 1: open (cells with two candidates in pairs), 2: solved
inline int FastBandSolver::propagate(State &s, Mask pairs[3]) {
	while (true) {
		if (!update(s)) return 0;
		bool placed = false;
		Mask multiple = 0;
		for (int band = 0; band < 3; band++) {
			Mask once = 0, twice = 0, thrice = 0;
			for (int digit = 0; digit < 9; digit++) {
				Mask c = s.cells[digit * 3 + band];
				thrice |= twice & c;
				twice |= once & c;
				once |= c;
			}
			if (once != ALL_CELLS) return 0;
			pairs[band] = twice & ~thrice;
			multiple |= twice;
			for (Mask singles = once & ~twice & s.unsolved[band]; singles; singles &= singles - 1) {
				Mask cell = singles & -singles;
				int digit = 0;
				while (digit < 9 && !(s.cells[digit * 3 + band] & cell)) digit++;
				if (digit == 9) return 0;  // an earlier single in this band took the cell's only digit
				int index = std::countr_zero(cell);
				s.cells[digit * 3 + band] &= AFTER_PLACING[index];
				s.cells[digit * 3 + (band == 0 ? 1 : 0)] &= OTHER_BANDS_AFTER_PLACING[index];
				s.cells[digit * 3 + (band == 2 ? 1 : 2)] &= OTHER_BANDS_AFTER_PLACING[index];
				s.unsolved[band] &= ~cell;
				s.openRows[digit] &= ~(1u << (band * 3 + index / 9));
				placed = true;
			}
		}
		if (!placed) return multiple ? 1 : 2;  // every cell down to one digit: solved
	}
}


inline void FastBandSolver::search(State *s) {
	Mask pairs[3];
	int progress = propagate(*s, pairs);
	if (progress == 0) return;
	if (progress == 2) {
		record(*s);
		return;
	}
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

	// no cell with two candidates: every candidate of a cell with the fewest
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


// unsolved cells in the cell's row, column and box
inline int FastBandSolver::peerScore(State const &s, int band, int index) {
	Mask column = columnCells(Mask(1) << (index % 9));
	int b1 = band == 0 ? 1 : 0, b2 = band == 2 ? 1 : 2;
	uint64_t others = uint64_t(s.unsolved[b1] & column) | uint64_t(s.unsolved[b2] & column) << 32;
	return std::popcount(s.unsolved[band] & BAND_PEERS[index]) + std::popcount(others);
}


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
