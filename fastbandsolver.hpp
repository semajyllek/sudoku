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
a box are a triad (tdoku's term; tdoku also has vertical triads, the band rule only needs these horizontal ones). A
candidate is a (cell, digit) pair not ruled out yet. A naked single is a cell with one candidate left; a row single is a
row where a digit has one cell left.


BIT LAYOUT

For each digit (0-8) and band (0-2), one 32-bit word holds the band's 27 cells where the digit can still go. Cell
(row r, column c) of the band is bit 9 * r + c:

    bit:  26 ........ 18   17 ......... 9   8 .......... 0
          row 2, col 8-0   row 1, col 8-0   row 0, col 8-0

Within each row, bits 3k to 3k + 2 are the triad of box k. Masks are written in binary with a ' between groups of
3 bits, so each group is one triad: 0b111 is one triad, 0b111'111'111 is one row, and (1 << 27) - 1 is the whole
band. A placed digit keeps its cell in its mask, so a solved grid is one where every cell is in exactly one digit's
mask.

Why one word per band and not one per row: taking a row out is a single shift and mask (one ubfx instruction on ARM),
about the cost of loading a separate row, while everything done to a whole band (the band rule's AND, the empty and
changed checks, placements, the candidate counters in propagate) stays one instruction instead of three.


THE TWO MATCHING RULES

Band rule. In the finished grid, a digit is once in each row of a band and once in each box of the band, so its three
cells pair the band's rows one-to-one with its boxes. There are only 6 such pairings (the permutations of 3 things).
Write A for the 3 x 3 table with A[r][k] = 1 when the digit still has a candidate in the triad of row r and box k.
A pairing that uses only 1-entries of A is a "perfect matching" of rows to boxes. A triad that is in no perfect
matching can never hold the digit, so its cells are removed, even if nothing inside the triad rules them out. This
covers locked candidates between rows and boxes. If no perfect matching exists, the position is a contradiction.

Example: row 0 can use boxes {0, 1}, row 1 only box {0}, row 2 boxes {1, 2}. Row 1 must take box 0, so row 0 must take
box 1 and row 2 box 2. The triads (row 0, box 0) and (row 2, box 1) are in no perfect matching and are cleared.

Stack rule. The same argument turned sideways: within a stack, a digit is once in each of the stack's three columns
and once in each of its three boxes, and the three boxes of a stack lie in the three different bands. So the digit
pairs the bands one-to-one with the stack's columns, and a (band, column) pair in no such pairing is cleared. This
generalizes "locked columns" (a box whose candidates for the digit lie in one column takes that column from the other
bands). It depends only on which columns each band still uses, so it only has to run when that changes.

Both rules look up a 512-entry table (PERMUTATION_UNION) indexed by the 9 bits of a 3 x 3 table.


ONE STEP OF PROPAGATION

For each (digit, band) mask that changed since the rules last ran on it (updateBand):
  1. band rule (three lookups build the table A, one lookup keeps the triads on some permutation)
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
	friend class ParallelBandSolver;  // reuses the propagation, placement and tables
	public:
		// fills out with a solution. false if the clues conflict or there is no solution
		bool solve(const int in[9][9], int out[9][9]);

		// number of solutions, stopping once limit is reached. limit 2 is enough to test uniqueness
		int countSolutions(const int in[9][9], int maxSolutions = 2);

		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

		// binary decisions made by the last call: 1 per two-candidate branch, n - 1 for an n-candidate cell
		long long guesses = 0;

	private:
		using Mask = uint32_t;
		static constexpr Mask ALL_CELLS = (1u << 27) - 1;  // 27 one-bits: every cell of a band

		// the search state, copied at each guess (246 bytes)
		struct State {
			Mask valueToBand[9][3];  // [digit][band]: the band's cells where the digit can still go (digit = value - 1)
			Mask checked[9][3];      // valueToBand as it was the last time the band rules ran on it; 0 at the start,
			                         // so every mask gets checked at least once. valueToBand != checked means
			                         // "needs checking"
			Mask unsolved[3];   // per band: cells not given a digit yet
			uint16_t openRows[9];  // per digit, 9 bits: rows (band * 3 + row) where it isn't placed yet, so each
			                       // placement is made once
		};


		// LOOKUP TABLES, all computed at compile time (8.5 KB in total)

		// 9-bit row of a band -> the boxes (3 bits, bit k for box k) it has candidates in. For example a row with a
		// candidate only in column 3, 0b000'001'000, gives box 1 only, 0b010
		static constexpr std::array<uint8_t, 512> BOXES_OF_ROW = [] {
			std::array<uint8_t, 512> t{};
			for (int r = 0; r < 512; r++) {
				t[r] = (r & 0b000'000'111 ? 0b001 : 0)    // any of columns 0-2 -> box 0
				     | (r & 0b000'111'000 ? 0b010 : 0)    // any of columns 3-5 -> box 1
				     | (r & 0b111'000'000 ? 0b100 : 0);   // any of columns 6-8 -> box 2
			}
			return t;
		}();

		// 3 x 3 table of 0s and 1s, bit i * 3 + j for entry (i, j) -> the union of the permutations that fit inside it,
		// where a permutation is a choice of three entries with one in each row and one in each column (a perfect
		// matching). Each of the 6 permutations whose three entries are all 1 contributes them. 0 if none fits.
		// Used by both rules: box candidates (rows x boxes) for the band rule, column candidates (bands x columns)
		// for the stack rule
		static constexpr std::array<uint16_t, 512> PERMUTATION_UNION = [] {
			constexpr int perms[6][3] = {{0, 1, 2}, {0, 2, 1}, {1, 0, 2}, {1, 2, 0}, {2, 0, 1}, {2, 1, 0}};
			std::array<uint16_t, 512> permutationUnion{};
			for (int candidates = 0; candidates < 512; candidates++) {
				for (auto const &p : perms) {
					int permutation = 1 << p[0] | 1 << (3 + p[1]) | 1 << (6 + p[2]);
					if ((candidates & permutation) == permutation) permutationUnion[candidates] |= permutation;
				}
			}
			return permutationUnion;
		}();

		// the band rule in one lookup: box candidates (bit row * 3 + box) -> the band cells of the triads that are in
		// some permutation. ANDing a mask with this removes every candidate no arrangement can use
		static constexpr std::array<Mask, 512> POSSIBLE_CELLS = [] {
			std::array<Mask, 512> possibleCells{};
			for (int boxCandidates = 0; boxCandidates < 512; boxCandidates++) {
				int kept = PERMUTATION_UNION[boxCandidates];
				for (int row = 0; row < 3; row++) {
					for (int box = 0; box < 3; box++) {
						if (kept >> (row * 3 + box) & 1) possibleCells[boxCandidates] |= Mask(0b111) << (row * 9 + box * 3);
					}
				}
			}
			return possibleCells;
		}();

		// a band's set of columns (9 bits) -> the boxes (3 bits) that have exactly one column left
		static constexpr std::array<uint8_t, 512> ONE_COLUMN_BOXES = [] {
			std::array<uint8_t, 512> t{};
			for (int columns = 0; columns < 512; columns++) {
				for (int box = 0; box < 3; box++) {
					if (std::popcount(unsigned((columns >> (box * 3)) & 0b111)) == 1) t[columns] |= 1 << box;
				}
			}
			return t;
		}();

		// rows (3 bits) that are down to one cell, indexed by the kept box candidates (9 bits, from PERMUTATION_UNION)
		// and ONE_COLUMN_BOXES << 9. Why this works, after the band rule has run: a row's cells are in its kept boxes.
		// A row with two kept boxes has at least two cells. A row with exactly one kept box k is paired with box k in
		// every permutation, so no other row has candidates in box k, and box k's candidates are
		// exactly the row's triad. So the row is down to one cell exactly when box k has one column left. This
		// replaces checking each row bit by bit
		static constexpr std::array<uint8_t, 4096> SINGLE_ROWS = [] {
			std::array<uint8_t, 4096> t{};
			for (int i = 0; i < 4096; i++) {
				int kept = i & 0b111'111'111, boxes = i >> 9;
				for (int row = 0; row < 3; row++) {
					int inRow = (kept >> (row * 3)) & 0b111;
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
			for (int bitIndex = 0; bitIndex < 27; bitIndex++) {
				int row = bitIndex / 9, box = bitIndex % 9 / 3;
				Mask rowCells = Mask(0b111'111'111) << (row * 9);
				Mask boxCells = (Mask(0b111) | Mask(0b111) << 9 | Mask(0b111) << 18) << (box * 3);
				t[bitIndex] = (ALL_CELLS & ~rowCells & ~boxCells) | Mask(1) << bitIndex;
			}
			return t;
		}();

		// what's left of the digit's other two bands after placing it at a cell: everything but the cell's column
		static constexpr std::array<Mask, 27> OTHER_BANDS_AFTER_PLACING = [] {
			std::array<Mask, 27> t{};
			for (int bitIndex = 0; bitIndex < 27; bitIndex++) t[bitIndex] = ALL_CELLS & ~((1u | 1u << 9 | 1u << 18) << (bitIndex % 9));
			return t;
		}();

		// rows of a band (3 bits) -> their cells
		static constexpr std::array<Mask, 8> ROWS_CELLS = [] {
			std::array<Mask, 8> t{};
			for (int r = 0; r < 8; r++) t[r] = (r & 1 ? 0b111'111'111u : 0) | (r & 2 ? 0b111'111'111u << 9 : 0) | (r & 4 ? 0b111'111'111u << 18 : 0);
			return t;
		}();

		// the cell's peers inside its band: its row and box, the cell excluded (the peers in the other bands are its
		// column)
		static constexpr std::array<Mask, 27> BAND_PEERS = [] {
			std::array<Mask, 27> t{};
			for (int bitIndex = 0; bitIndex < 27; bitIndex++) t[bitIndex] = ~AFTER_PLACING[bitIndex] & ALL_CELLS;
			return t;
		}();

		// the columns (9 bits) where a band mask has any cell: OR the three rows together
		static constexpr Mask bandColumns(Mask bandCells) { return (bandCells | bandCells >> 9 | bandCells >> 18) & 0b111'111'111; }

		// set at the start of each solve, and members so that the recursive search can read them without passing them
		// down at every level
		int limit = 0;                     // stop once this many solutions are found: 1 for solve, 2 to test uniqueness
		int found = 0;                     // solutions found so far
		int (*solutionOut)[9] = nullptr;   // the caller's 9 x 9 grid for the first solution; nullptr = only count
		State stack[82];  // one state per guess depth, so a solve allocates nothing

		// a cell to guess on: its band, a mask of that band with only the cell's bit set, and how many candidates it has
		struct GuessCell {
			int band;
			Mask cellBitMask;
			int candidates;
		};

		// what propagate ends with: a contradiction (no solution down this branch), an open position that needs a
		// guess, or a solved grid
		enum class Progress { Contradiction, Open, Solved };

		static void reset(State &state);
		bool load(State &state, const int in[9][9]);
		template <int B> bool updateBand(State &state, int digit);
		void stackRule(State &state, int digit);
		bool update(State &state);
		Progress propagate(State &state, Mask pairs[3]);
		void search(State *state);
		static void place(State &state, int digit, int band, Mask cellBitMask);
		static void clearPeers(State &state, int digit, int band, Mask cellBitMask);
		static GuessCell chooseGuessCell(State const &state, Mask const pairs[3]);
		static GuessCell fewestCandidatesCell(State const &state);
		static int nextValueIn(State const &state, int band, Mask cellBitMask, int startDigit);
		static int peerScore(State const &state, int band, int bitIndex);
		void record(State const &state);
		static void writeSolution(State const &state, int out[9][9]);
};


inline bool FastBandSolver::solve(const int in[9][9], int out[9][9]) {
	limit = 1;
	found = 0;
	guesses = 0;
	solutionOut = out;  // record writes the solution straight into the caller's grid
	if (load(stack[0], in)) search(&stack[0]);
	return found > 0;  // false: the clues clash, or the puzzle has no solution
}


inline int FastBandSolver::countSolutions(const int in[9][9], int maxSolutions) {
	limit = maxSolutions;
	found = 0;
	guesses = 0;
	solutionOut = nullptr;
	if (load(stack[0], in)) search(&stack[0]);
	return found;
}


// puts the digit in the cell (cellBitMask: a mask with only the cell's bit set): removes the other digits from the cell, and the digit from
// the rest of the cell's row and box (own band) and column (other two bands). Used for clues and guesses
[[gnu::always_inline]] inline void FastBandSolver::place(State &state, int digit, int band, Mask cellBitMask) {
	for (int other = 0; other < 9; other++) state.valueToBand[other][band] &= ~cellBitMask;
	state.valueToBand[digit][band] |= cellBitMask;
	clearPeers(state, digit, band, cellBitMask);
}


// the second half of placing the digit in the cell, once no other digit can go there: removes the digit from the rest
// of the cell's row and box (own band) and column (other two bands), and marks the cell and its row as done. Shared by
// place and the naked singles in propagate. always_inline: it is on the hot path, so it must not become a call
[[gnu::always_inline]] inline void FastBandSolver::clearPeers(State &state, int digit, int band, Mask cellBitMask) {
	int bitIndex = std::countr_zero(cellBitMask);                        // the cell's bit number, 0-26
	int otherBand1 = band == 0 ? 1 : 0, otherBand2 = band == 2 ? 1 : 2;  // the two bands that are not band
	int boardRow = band * 3 + bitIndex / 9;                              // the cell's row on the board, 0-8
	state.valueToBand[digit][band] &= AFTER_PLACING[bitIndex];
	state.valueToBand[digit][otherBand1] &= OTHER_BANDS_AFTER_PLACING[bitIndex];
	state.valueToBand[digit][otherBand2] &= OTHER_BANDS_AFTER_PLACING[bitIndex];
	state.unsolved[band] &= ~cellBitMask;
	state.openRows[digit] &= ~(1u << boardRow);
}


// the empty board: every digit can go in every cell, no cell or row is done, and checked is 0 so that every mask
// gets checked at least once
inline void FastBandSolver::reset(State &state) {
	for (int digit = 0; digit < 9; digit++) {
		for (int band = 0; band < 3; band++) {
			state.valueToBand[digit][band] = ALL_CELLS;
			state.checked[digit][band] = 0;
		}
	}
	for (int band = 0; band < 3; band++) state.unsolved[band] = ALL_CELLS;
	for (int digit = 0; digit < 9; digit++) state.openRows[digit] = 0b111'111'111;
}


// starts from the empty board and places the clues, without propagating them yet. false if a clue is no longer a
// candidate, which means it repeats a digit in a row, column or box
inline bool FastBandSolver::load(State &state, const int in[9][9]) {
	reset(state);
	for (int cell = 0; cell < 81; cell++) {
		int clue = in[cell / 9][cell % 9];  // 0 = empty square, 1-9 = the number given
		if (clue == 0) continue;            // empty square: every value is still allowed there
		int digit = clue - 1;               // 0-8, as everywhere else
		int band = cell / 27;               // 0-2: each band is 27 consecutive cells
		int bitIndex = cell % 27;           // the cell's bit number inside the band, 0-26
		Mask cellBitMask = Mask(1) << bitIndex;
		if ((state.valueToBand[digit][band] & cellBitMask) == 0) return false;  // an earlier clue removed it: a clash
		place(state, digit, band, cellBitMask);
	}
	return true;
}


// the stack rule for one digit: in each stack, keeps the (band, column) pairs that are in some one-to-one pairing of
// the three bands with the stack's three columns. For each stack, build the 3 x 3 table (row = band, column = one of the
// stack's columns) of column candidates from the bands' column sets, look up PERMUTATION_UNION, and keep only the
// columns on some permutation in each band.
// Branch-free: processing only the stacks that changed gave the same result but was slower, because the extra
// branches are hard to predict. If a stack has no pairing, the bands lose that stack entirely and the band rule then
// finds the contradiction
inline void FastBandSolver::stackRule(State &state, int digit) {
	Mask *digitBands = state.valueToBand[digit];  // the digit's three band masks
	Mask columns0 = bandColumns(digitBands[0]), columns1 = bandColumns(digitBands[1]), columns2 = bandColumns(digitBands[2]);
	Mask keptColumns0 = 0, keptColumns1 = 0, keptColumns2 = 0;
	for (int shift = 0; shift < 9; shift += 3) {  // shift = the stack's first column: 0, 3, 6
		Mask columnCandidates = (columns0 >> shift & 0b111) | (columns1 >> shift & 0b111) << 3 | (columns2 >> shift & 0b111) << 6;
		Mask kept = PERMUTATION_UNION[columnCandidates];
		keptColumns0 |= (kept & 0b111) << shift;
		keptColumns1 |= (kept >> 3 & 0b111) << shift;
		keptColumns2 |= (kept >> 6 & 0b111) << shift;
	}
	digitBands[0] &= columnCells(keptColumns0);
	digitBands[1] &= columnCells(keptColumns1);
	digitBands[2] &= columnCells(keptColumns2);
}


// band rule, stack rule and row singles for one (digit, band). false if the digit has no arrangement left in the band.
// B is a template parameter so the other two bands' positions are constants in each of the three copies.
// always_inline (a GCC/clang attribute): clang otherwise keeps this a function call, which costs about 9% on the hard
// sets
template <int B> [[gnu::always_inline]] inline bool FastBandSolver::updateBand(State &state, int digit) {
	Mask bandCells = state.valueToBand[digit][B];
	Mask lastChecked = state.checked[digit][B];

	// band rule: build the 3 x 3 table of box candidates (bit row * 3 + box) with one lookup per row, then keep only
	// the cells of triads on some permutation. Zero means no arrangement: a contradiction
	int boxCandidates = BOXES_OF_ROW[bandCells & 0b111'111'111]               // row 0's boxes, bits 0-2
	                  | BOXES_OF_ROW[(bandCells >> 9) & 0b111'111'111] << 3  // row 1's boxes, bits 3-5
	                  | BOXES_OF_ROW[bandCells >> 18] << 6;                  // row 2's boxes, bits 6-8
	bandCells &= POSSIBLE_CELLS[boxCandidates];
	if (!bandCells) return false;
	state.valueToBand[digit][B] = state.checked[digit][B] = bandCells;

	// stack rule, only when the band's set of columns changed (it depends on nothing else). It may clear more of this
	// band; checked keeps the value above, so this band then counts as changed and is checked again in the next pass.
	// The stack rule also covers locked columns, so there is no separate step for them
	Mask columns = bandColumns(bandCells);
	if (columns != bandColumns(lastChecked)) stackRule(state, digit);

	// row singles, found with SINGLE_ROWS (see there for why a table lookup is enough). Only rows where the digit
	// isn't placed yet count, so each placement happens once
	unsigned singleRows = SINGLE_ROWS[PERMUTATION_UNION[boxCandidates] | ONE_COLUMN_BOXES[columns] << 9];
	unsigned openRowsInBand = (state.openRows[digit] >> (B * 3)) & 0b111;
	unsigned newSingleRows = singleRows & openRowsInBand;
	if (newSingleRows) {
		Mask placedCells = bandCells & ROWS_CELLS[newSingleRows];  // one cell per new single row
		// take the placed cells from every digit of the band, then give this digit its mask back: cheaper than
		// testing "other != digit" in the loop. Restore the mask as it is now, not bandCells: the stack rule above may
		// have removed more of it, and restoring bandCells would put those candidates back. Masks must only shrink;
		// the correctness proof relies on it (an earlier version had this bug, which no test caught)
		Mask digitMaskNow = state.valueToBand[digit][B];
		for (int other = 0; other < 9; other++) state.valueToBand[other][B] &= ~placedCells;
		state.valueToBand[digit][B] = digitMaskNow;
		state.unsolved[B] &= ~placedCells;
		state.openRows[digit] &= ~(newSingleRows << (B * 3));
	}
	return true;
}


// runs updateBand on every (digit, band) that changed since it was last checked, until a whole pass changes nothing.
// Changes made during a pass (by the stack rule, or row singles clearing other digits) are picked up later in the pass
// or in the next one. Digits with every row placed are not skipped (JCZSolve skips them): skipping saved nothing and
// hid changes to them. The three bands are written out, not looped over, so that each updateBand<B> call has its band
// as a compile-time constant
inline bool FastBandSolver::update(State &state) {
	bool ranAnyCheck = true;  // whether this pass ran updateBand at all; true at first so that the first pass runs
	while (ranAnyCheck) {
		ranAnyCheck = false;
		for (int digit = 0; digit < 9; digit++) {
			if (state.valueToBand[digit][0] != state.checked[digit][0]) {
				if (updateBand<0>(state, digit) == false) return false;
				ranAnyCheck = true;
			}
			if (state.valueToBand[digit][1] != state.checked[digit][1]) {
				if (updateBand<1>(state, digit) == false) return false;
				ranAnyCheck = true;
			}
			if (state.valueToBand[digit][2] != state.checked[digit][2]) {
				if (updateBand<2>(state, digit) == false) return false;
				ranAnyCheck = true;
			}
		}
	}
	return true;
}


// everything that follows without guessing. Returns Contradiction, Solved, or Open, with the cells that have exactly
// two candidates in pairs.
//
// Counting candidates per cell, for all 27 cells of a band at once: once, twice and thrice are bit-sliced counters.
// Bit x of once is set when at least one digit admits cell x, of twice when at least two do, of thrice when at least
// three do. Adding a digit's mask updates them highest first, so each uses the old value of the one below it.
// Then once & ~twice is "exactly one" and twice & ~thrice "exactly two".
inline FastBandSolver::Progress FastBandSolver::propagate(State &state, Mask pairs[3]) {
	while (true) {
		if (!update(state)) return Progress::Contradiction;
		bool placed = false;
		Mask multiple = 0;  // cells with two or more candidates, in any band
		for (int band = 0; band < 3; band++) {
			Mask once = 0, twice = 0, thrice = 0;
			for (int digit = 0; digit < 9; digit++) {
				Mask bandCells = state.valueToBand[digit][band];
				thrice |= twice & bandCells;
				twice |= once & bandCells;
				once |= bandCells;
			}
			if (once != ALL_CELLS) return Progress::Contradiction;  // a cell no digit can go in
			pairs[band] = twice & ~thrice;
			multiple |= twice;
			// naked singles not placed yet. x & (x - 1) clears the lowest set bit, x & -x isolates it
			for (Mask singles = once & ~twice & state.unsolved[band]; singles; singles &= singles - 1) {
				Mask cellBitMask = singles & -singles;
				int digit = nextValueIn(state, band, cellBitMask, 0);
				if (digit == 9) return Progress::Contradiction;  // an earlier single in this band took the cell's only digit
				// the other digits are already gone from this cell, so only the digit's own masks change
				clearPeers(state, digit, band, cellBitMask);
				placed = true;
			}
		}
		// solved only when every cell is down to one digit and the rules have run to the end. Then each digit is in
		// every row, column and box (the band rule keeps it in every row and box, the stack rule in every column), and
		// with one digit per cell that makes each digit appear exactly once in each: a valid grid
		if (!placed) return multiple ? Progress::Open : Progress::Solved;
	}
}


// depth-first search. state is the state for this depth; a guess copies it into state + 1, and the second choice of a
// two-candidate cell reuses state itself, since it isn't needed afterwards
inline void FastBandSolver::search(State *state) {
	Mask pairs[3];
	Progress progress = propagate(*state, pairs);
	if (progress == Progress::Contradiction) return;
	if (progress == Progress::Solved) {
		record(*state);
		return;
	}

	GuessCell guess = chooseGuessCell(*state, pairs);
	if (guess.band >= 0) {
		int first = nextValueIn(*state, guess.band, guess.cellBitMask, 0);
		int second = nextValueIn(*state, guess.band, guess.cellBitMask, first + 1);
		guesses++;
		State *child = state + 1;
		std::memcpy(child, state, sizeof(State));
		place(*child, first, guess.band, guess.cellBitMask);
		search(child);
		if (found >= limit) return;
		place(*state, second, guess.band, guess.cellBitMask);
		search(state);
		return;
	}

	// no cell with two candidates: try every candidate of the cell with the fewest. n candidates are n - 1 guesses
	guess = fewestCandidatesCell(*state);
	guesses += guess.candidates - 1;
	for (int digit = nextValueIn(*state, guess.band, guess.cellBitMask, 0); digit < 9 && found < limit;
	     digit = nextValueIn(*state, guess.band, guess.cellBitMask, digit + 1)) {
		State *child = state + 1;
		std::memcpy(child, state, sizeof(State));
		place(*child, digit, guess.band, guess.cellBitMask);
		search(child);
	}
}


// the two-candidate cell with the most unsolved peers; the first one in board order among ties. band = -1 if no cell
// has two candidates
[[gnu::always_inline]] inline FastBandSolver::GuessCell FastBandSolver::chooseGuessCell(State const &state, Mask const pairs[3]) {
	GuessCell best = {-1, 0, 2};
	int bestScore = -1;
	for (int band = 0; band < 3; band++) {
		for (Mask p = pairs[band]; p; p &= p - 1) {
			int score = peerScore(state, band, std::countr_zero(p));
			if (score > bestScore) {
				bestScore = score;
				best = {band, p & -p, 2};
			}
		}
	}
	return best;
}


// the unsolved cell with the fewest candidates, the most unsolved peers breaking ties. Only used when no cell has two. This is rare (about 1% of guesses on the hardest puzzles) but tends to
// happen near the top of the tree, where a cell with five candidates instead of three multiplies the work below it
[[gnu::always_inline]] inline FastBandSolver::GuessCell FastBandSolver::fewestCandidatesCell(State const &state) {
	GuessCell best = {-1, 0, 10};  // 10: more than any cell can have, so the first cell checked replaces it
	int bestScore = -1;
	for (int band = 0; band < 3; band++) {
		for (Mask u = state.unsolved[band]; u; u &= u - 1) {
			int bitIndex = std::countr_zero(u), candidates = 0;
			for (int digit = 0; digit < 9; digit++) candidates += (state.valueToBand[digit][band] >> bitIndex) & 1;
			if (candidates > best.candidates) continue;
			int score = peerScore(state, band, bitIndex);
			if (candidates < best.candidates || score > bestScore) {
				bestScore = score;
				best = {band, u & -u, candidates};
			}
		}
	}
	return best;
}


// the first value, from startDigit on (startDigit itself included), that can still go in the cell; 9 if there is none
[[gnu::always_inline]] inline int FastBandSolver::nextValueIn(State const &state, int band, Mask cellBitMask, int startDigit) {
	int digit = startDigit;
	while (digit < 9 && (state.valueToBand[digit][band] & cellBitMask) == 0) digit++;
	return digit;
}


// unsolved cells among the cell's 20 peers: its row and box inside its band, plus its column in the other two bands.
// Packing the two other bands into one 64-bit word counts them with a single popcount. At guessing time the unsolved
// cells are exactly the ones with two or more candidates, so this is the number of peers still open
[[gnu::always_inline]] inline int FastBandSolver::peerScore(State const &state, int band, int bitIndex) {
	Mask column = columnCells(Mask(1) << (bitIndex % 9));
	int otherBand1 = band == 0 ? 1 : 0, otherBand2 = band == 2 ? 1 : 2;
	uint64_t others = uint64_t(state.unsolved[otherBand1] & column) | uint64_t(state.unsolved[otherBand2] & column) << 32;
	return std::popcount(state.unsolved[band] & BAND_PEERS[bitIndex]) + std::popcount(others);
}


// counts a solution, and copies out the first one: each cell's digit is the one whose mask has its bit
inline void FastBandSolver::record(State const &state) {
	if (found == 0 && solutionOut) writeSolution(state, solutionOut);
	found++;
}


// in a solved state each cell is in exactly one digit's mask: write each digit into the cells of its masks. (Looking
// up each cell's digit instead scans up to nine masks per cell, which cost about half a microsecond per puzzle.)
// Bit 9 * row + column of band b is board row b * 3 + row
inline void FastBandSolver::writeSolution(State const &state, int out[9][9]) {
	for (int digit = 0; digit < 9; digit++) {
		for (int band = 0; band < 3; band++) {
			for (Mask remaining = state.valueToBand[digit][band]; remaining; remaining &= remaining - 1) {
				int bitIndex = std::countr_zero(remaining);  // the cell's bit number, 0-26
				out[band * 3 + bitIndex / 9][bitIndex % 9] = digit + 1;
			}
		}
	}
}
