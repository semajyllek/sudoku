/*
Sudoku solver built on TinyBitSet.

Search: always branch on the empty cell with the fewest candidates, unless some row/col/box has a digit
that fits in only one of its cells (a hidden single), in which case place that first.

The same search both solves (stop at the first solution) and counts solutions (stop at a limit),
so checking a generated puzzle has exactly one answer is countSolutions(puzzle) == 1.

Stopping at the limit is immediate: the search returns without undoing its placements, so the grid is left
holding the solution it just found. That is how solve() gets its answer, with no copying during the search.
*/
#pragma once
#include "../tinybitset/tinybitset.h"
#include <array>
#include <optional>
#include <span>
#include <utility>

using Digits = TinyBitSet<9>;


// optional hook for watching a search, e.g. to visualize it: told about every digit the search places and removes
class SearchObserver {
	public:
		virtual ~SearchObserver() = default;
		virtual void placed(int cell, int digit, bool guessed) = 0;  // guessed: the cell had 2+ candidates
		virtual void removed(int cell, int digit) = 0;
};


class SudokuSolver {
	public:
		// fills out with a solution. false if the clues conflict or there is no solution
		bool solve(const int in[9][9], int out[9][9]);

		// number of solutions, stopping once limit is reached. limit 2 is enough to test uniqueness
		int countSolutions(const int in[9][9], int limit = 2);

		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

		// report every search step to observer from now on. nullptr stops it
		void watch(SearchObserver *observer) { this->observer = observer; }

	private:
		static constexpr Digits ALL{1, 2, 3, 4, 5, 6, 7, 8, 9};
		static constexpr int NUM_UNITS = 27;  // units 0-8 are rows, 9-17 columns, 18-26 boxes

		// a cell to branch on and the digits to try there. no digits means a dead end
		struct Branch {
			int cell;
			Digits digits;
		};

		// for each unit, the digits that fit in at least one / at least two of its unfilled cells
		struct UnitTally {
			Digits once[NUM_UNITS];
			Digits twice[NUM_UNITS];
		};

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
			std::array<int, NUM_UNITS> count{};
			for (int cell = 0; cell < 81; cell++) {
				for (int unit : UNITS_OF[cell]) {
					cells[unit][count[unit]++] = cell;
				}
			}
			return cells;
		}();

		Digits used[NUM_UNITS];  // digits already placed in each unit
		int grid[81] = {};  // 0 = empty. after a search that reached its limit, the last solution found

		// the cells that were empty in the puzzle. during search, empties[0..filled) hold the cells filled so far,
		// in the order they were filled, and empties[filled..numEmpty) the ones still empty
		int empties[81] = {};
		int slotOf[81] = {};     // empties[slotOf[cell]] == cell
		int numEmpty = 0;

		SearchObserver *observer = nullptr;

		bool load(const int in[9][9]);
		int startSearch(int limit);
		template <bool Watched> int search(int filled, int limit);
		std::span<const int> unfilled(int filled) const;
		void moveToSlot(int cell, int slot);

		Branch chooseBranch(int filled) const;
		Branch fewestCandidates(int filled) const;
		UnitTally tallyCandidates(int filled) const;
		bool canPlaceAll(UnitTally const &tally, int unit) const;
		std::optional<Branch> hiddenSingle(UnitTally const &tally, int unit) const;
		int cellFor(int unit, int digit) const;

		Digits candidates(int cell) const;
		void place(int cell, int digit);
		void unplace(int cell, int digit);
};



inline bool SudokuSolver::solve(const int in[9][9], int out[9][9]) {
	if (!load(in) || startSearch(1) == 0) {
		return false;
	}
	// the search stopped at its first solution, so grid still holds it
	for (int cell = 0; cell < 81; cell++) {
		out[cell / 9][cell % 9] = grid[cell];
	}
	return true;
}


inline int SudokuSolver::countSolutions(const int in[9][9], int limit) {
	return load(in) ? startSearch(limit) : 0;
}


inline bool SudokuSolver::load(const int in[9][9]) {
	SearchObserver *watching = observer;  // the reset below shouldn't stop the watching
	*this = SudokuSolver();
	observer = watching;
	for (int cell = 0; cell < 81; cell++) {
		int digit = in[cell / 9][cell % 9];
		if (digit == 0) {
			slotOf[cell] = numEmpty;
			empties[numEmpty++] = cell;
		} else if (candidates(cell).contains(digit)) {
			place(cell, digit);
		} else {
			return false;  // clue repeats a digit already in its row, column or box
		}
	}
	return true;
}



// two compiled versions of search, so the unwatched one has no observer code in it at all
inline int SudokuSolver::startSearch(int limit) {
	return observer ? search<true>(0, limit) : search<false>(0, limit);
}


// fills the unfilled cells, returning how many solutions it found (at most limit)
template <bool Watched>
inline int SudokuSolver::search(int filled, int limit) {
	if (filled == numEmpty) {
		return 1;
	}
	Branch branch = chooseBranch(filled);
	moveToSlot(branch.cell, filled);

	[[maybe_unused]] bool guessing = branch.digits.getSetSize() > 1;
	int found = 0;
	for (int digit : branch.digits) {
		place(branch.cell, digit);
		if constexpr (Watched) observer->placed(branch.cell, digit, guessing);
		found += search<Watched>(filled + 1, limit - found);
		if (found == limit) {
			return found;  // stop right here, leaving the solution in grid
		}
		unplace(branch.cell, digit);
		if constexpr (Watched) observer->removed(branch.cell, digit);
	}
	return found;
}


inline std::span<const int> SudokuSolver::unfilled(int filled) const {
	return {empties + filled, empties + numEmpty};
}


inline void SudokuSolver::moveToSlot(int cell, int slot) {
	int other = empties[slot];
	std::swap(empties[slot], empties[slotOf[cell]]);
	std::swap(slotOf[cell], slotOf[other]);
}



// a hidden single (or a unit where some digit fits nowhere) beats any cell with 2+ candidates
inline SudokuSolver::Branch SudokuSolver::chooseBranch(int filled) const {
	Branch best = fewestCandidates(filled);
	if (best.digits.getSetSize() <= 1) {
		return best;
	}
	UnitTally tally = tallyCandidates(filled);
	for (int unit = 0; unit < NUM_UNITS; unit++) {
		if (!canPlaceAll(tally, unit)) {
			return {unfilled(filled).front(), Digits()};  // dead end
		}
		if (std::optional<Branch> forced = hiddenSingle(tally, unit)) {
			return *forced;
		}
	}
	return best;
}


// stops early at a cell with 0 or 1 candidates, since nothing can beat that
inline SudokuSolver::Branch SudokuSolver::fewestCandidates(int filled) const {
	std::span<const int> cells = unfilled(filled);
	Branch best{cells.front(), candidates(cells.front())};
	for (int cell : cells.subspan(1)) {
		if (best.digits.getSetSize() <= 1) {
			break;
		}
		Digits digits = candidates(cell);
		if (digits.getSetSize() < best.digits.getSetSize()) {
			best = {cell, digits};
		}
	}
	return best;
}


inline SudokuSolver::UnitTally SudokuSolver::tallyCandidates(int filled) const {
	UnitTally tally;
	for (int cell : unfilled(filled)) {
		Digits digits = candidates(cell);
		for (int unit : UNITS_OF[cell]) {
			tally.twice[unit] |= tally.once[unit] & digits;
			tally.once[unit] |= digits;
		}
	}
	return tally;
}


// every digit is either already in the unit or fits in one of its unfilled cells
inline bool SudokuSolver::canPlaceAll(UnitTally const &tally, int unit) const {
	return (used[unit] | tally.once[unit]) == ALL;
}


// a digit that fits in exactly one unfilled cell of the unit must go there
inline std::optional<SudokuSolver::Branch> SudokuSolver::hiddenSingle(UnitTally const &tally, int unit) const {
	Digits onlyOnce = tally.once[unit] - tally.twice[unit];
	if (onlyOnce.isempty()) {
		return std::nullopt;
	}
	int digit = *onlyOnce.begin();
	return Branch{cellFor(unit, digit), Digits{digit}};
}


// the unfilled cell in the unit where digit fits. only called when there is exactly one
inline int SudokuSolver::cellFor(int unit, int digit) const {
	for (int cell : CELLS_OF[unit]) {
		if (grid[cell] == 0 && candidates(cell).contains(digit)) {
			return cell;
		}
	}
	return -1;
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
