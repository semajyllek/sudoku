/*
Sudoku solver built on TinyBitSet.

Search: always branch on the empty cell with the fewest candidates, unless some row/col/box has a digit
that fits in only one of its cells (a hidden single), in which case place that first.

The same search both solves (stop at the first solution) and counts solutions (stop at a limit),
so checking a generated puzzle has exactly one answer is countSolutions(puzzle) == 1.
*/
#pragma once
#include "../tinybitset/tinybitset.h"
#include <array>
#include <optional>
#include <utility>

using Digits = TinyBitSet<9>;


class SudokuSolver {
	public:
		// fills out with a solution. false if the clues conflict or there is no solution
		bool solve(const int in[9][9], int out[9][9]);

		// number of solutions, stopping once limit is reached. limit 2 is enough to test uniqueness
		int countSolutions(const int in[9][9], int limit = 2);

		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

	private:
		// a cell to branch on (as its position in empties) and the digits to try there.
		// no digits means a dead end
		struct Branch {
			int slot;
			Digits digits;
		};

		static constexpr Digits ALL{1, 2, 3, 4, 5, 6, 7, 8, 9};
		static constexpr int NUM_UNITS = 27;  // units 0-8 are rows, 9-17 columns, 18-26 boxes

		// the row, column and box each cell belongs to
		static constexpr std::array<std::array<int, 3>, 81> UNITS_OF = [] {
			std::array<std::array<int, 3>, 81> units{};
			for (int cell = 0; cell < 81; cell++) {
				units[cell] = {cell / 9, 9 + cell % 9, 18 + (cell / 27) * 3 + (cell % 9) / 3};
			}
			return units;
		}();

		// the 9 cells in each unit
		static constexpr std::array<std::array<int, 9>, NUM_UNITS> CELLS_OF = [] {
			std::array<std::array<int, 9>, NUM_UNITS> cells{};
			std::array<int, NUM_UNITS> filled{};
			for (int cell = 0; cell < 81; cell++) {
				for (int unit : UNITS_OF[cell]) {
					cells[unit][filled[unit]++] = cell;
				}
			}
			return cells;
		}();

		Digits used[NUM_UNITS];  // digits already placed in each unit
		int grid[81] = {};
		int empties[81] = {};    // empty cells; empties[0..k) are filled in during search at depth k
		int numEmpty = 0;

		bool load(const int in[9][9]);
		int search(int k, int limit);

		Branch chooseBranch(int k) const;
		Branch fewestCandidates(int k) const;
		std::optional<Branch> hiddenSingle(int k) const;
		int slotOf(int cell, int k) const;

		Digits candidates(int cell) const;
		void place(int cell, int digit);
		void unplace(int cell, int digit);
};



inline bool SudokuSolver::solve(const int in[9][9], int out[9][9]) {
	if (!load(in) || search(0, 1) == 0) {
		return false;
	}
	// search stops at the first solution without undoing it, so grid holds the answer
	for (int cell = 0; cell < 81; cell++) {
		out[cell / 9][cell % 9] = grid[cell];
	}
	return true;
}


inline int SudokuSolver::countSolutions(const int in[9][9], int limit) {
	return load(in) ? search(0, limit) : 0;
}


inline bool SudokuSolver::load(const int in[9][9]) {
	*this = SudokuSolver();
	for (int cell = 0; cell < 81; cell++) {
		int digit = in[cell / 9][cell % 9];
		if (digit == 0) {
			empties[numEmpty++] = cell;
		} else if (candidates(cell).contains(digit)) {
			place(cell, digit);
		} else {
			return false;  // clue repeats a digit already in its row, column or box
		}
	}
	return true;
}


// fills empties[k..], returning how many solutions it found (at most limit).
// on reaching the limit it returns immediately, leaving the last solution in grid
inline int SudokuSolver::search(int k, int limit) {
	if (k == numEmpty) {
		return 1;
	}
	Branch branch = chooseBranch(k);
	std::swap(empties[k], empties[branch.slot]);
	int cell = empties[k];

	int found = 0;
	for (int digit : branch.digits) {
		place(cell, digit);
		found += search(k + 1, limit - found);
		if (found == limit) {
			return found;
		}
		unplace(cell, digit);
	}
	return found;
}



inline SudokuSolver::Branch SudokuSolver::chooseBranch(int k) const {
	Branch best = fewestCandidates(k);
	if (best.digits.getSetSize() > 1) {
		if (std::optional<Branch> forced = hiddenSingle(k)) {
			return *forced;
		}
	}
	return best;
}


// stops early at a cell with 0 or 1 candidates, since nothing can beat that
inline SudokuSolver::Branch SudokuSolver::fewestCandidates(int k) const {
	Branch best{k, candidates(empties[k])};
	for (int slot = k + 1; slot < numEmpty && best.digits.getSetSize() > 1; slot++) {
		Digits digits = candidates(empties[slot]);
		if (digits.getSetSize() < best.digits.getSetSize()) {
			best = {slot, digits};
		}
	}
	return best;
}


// a digit missing from a unit that fits in exactly one of its empty cells must go there.
// returns a dead end if a missing digit fits nowhere, nothing if no unit has a hidden single
inline std::optional<SudokuSolver::Branch> SudokuSolver::hiddenSingle(int k) const {
	Digits once[NUM_UNITS], twice[NUM_UNITS];
	for (int slot = k; slot < numEmpty; slot++) {
		int cell = empties[slot];
		Digits digits = candidates(cell);
		for (int unit : UNITS_OF[cell]) {
			twice[unit] |= once[unit] & digits;
			once[unit] |= digits;
		}
	}

	for (int unit = 0; unit < NUM_UNITS; unit++) {
		if ((used[unit] | once[unit]) != ALL) {
			return Branch{k, Digits()};
		}
		Digits onlyOnce = once[unit] - twice[unit];
		if (!onlyOnce.isempty()) {
			int digit = *onlyOnce.begin();
			for (int cell : CELLS_OF[unit]) {
				if (grid[cell] == 0 && candidates(cell).contains(digit)) {
					return Branch{slotOf(cell, k), Digits{digit}};
				}
			}
		}
	}
	return std::nullopt;
}


inline int SudokuSolver::slotOf(int cell, int k) const {
	int slot = k;
	while (empties[slot] != cell) {
		slot++;
	}
	return slot;
}



inline Digits SudokuSolver::candidates(int cell) const {
	auto [row, col, box] = UNITS_OF[cell];
	return ALL - (used[row] | used[col] | used[box]);
}


inline void SudokuSolver::place(int cell, int digit) {
	grid[cell] = digit;
	for (int unit : UNITS_OF[cell]) {
		used[unit].insert(digit);
	}
}


inline void SudokuSolver::unplace(int cell, int digit) {
	grid[cell] = 0;
	for (int unit : UNITS_OF[cell]) {
		used[unit].remove(digit);
	}
}
