/*
Tests for SudokuSolver::solve and countSolutions. Run from the repo root (reads data/).

Solution counts are cross-checked against naiveCount below, a deliberately simple and independent
counter: plain ints, row-major order, no TinyBitSet, no fewest-candidates, no hidden singles.
*/
#include "../sudokusolver.hpp"
#include "../puzzles.hpp"
#include <cstdio>
#include <cstring>
#include <random>


static int failures = 0;

void check(bool passed, std::string const &name, std::string const &detail = "") {
	std::printf("%s %s", passed ? "passed" : "FAILED", name.c_str());
	std::printf(detail.empty() ? "\n" : " (%s)\n", detail.c_str());
	failures += !passed;
}


bool naiveFits(const int grid[81], int cell, int digit) {
	int row = cell / 9, col = cell % 9, boxRow = row / 3 * 3, boxCol = col / 3 * 3;
	for (int k = 0; k < 9; k++) {
		if (grid[row * 9 + k] == digit || grid[k * 9 + col] == digit || grid[(boxRow + k / 3) * 9 + boxCol + k % 3] == digit) {
			return false;
		}
	}
	return true;
}

int naiveCountFrom(int grid[81], int cell, int limit) {
	while (cell < 81 && grid[cell] != 0) cell++;
	if (cell == 81) return 1;
	int found = 0;
	for (int digit = 1; digit <= 9 && found < limit; digit++) {
		if (naiveFits(grid, cell, digit)) {
			grid[cell] = digit;
			found += naiveCountFrom(grid, cell + 1, limit - found);
			grid[cell] = 0;
		}
	}
	return found;
}

int naiveCount(const int in[9][9], int limit) {
	int grid[81] = {};  // cells not placed yet must read as empty
	for (int cell = 0; cell < 81; cell++) {
		int digit = in[cell / 9][cell % 9];
		if (digit != 0 && !naiveFits(grid, cell, digit)) return 0;  // conflicting clues
		grid[cell] = digit;
	}
	return naiveCountFrom(grid, 0, limit);
}



void testKnownUniquePuzzles() {
	SudokuSolver solver;
	int out[9][9];
	for (std::string name : {"inkala2012", "antiBacktrack"}) {
		Puzzle p = hardPuzzle(name);
		bool solved = solver.solve(p.grid, out) && validSolution(p.grid, out);
		check(solved && solver.countSolutions(p.grid) == 1 && solver.hasUniqueSolution(p.grid), name + " is solved and unique");
	}
}


void testNoSolution() {
	SudokuSolver solver;
	int out[9][9];
	Puzzle p = hardPuzzle("arraySegfaultBoard");
	check(!solver.solve(p.grid, out) && solver.countSolutions(p.grid, 100) == 0, "arraySegfaultBoard has no solution");
}


void testConflictingClues() {
	SudokuSolver solver;
	int out[9][9];
	int grid[9][9] = {};
	grid[4][0] = 2;
	grid[4][5] = 2;  // two 2s in one row, like arrayweirdBoard
	check(!solver.solve(grid, out) && solver.countSolutions(grid) == 0, "conflicting clues are rejected");
}


void testCompleteAndEmptyGrids() {
	SudokuSolver solver;
	int full[9][9];
	solver.solve(hardPuzzle("inkala2012").grid, full);
	int empty[9][9] = {};
	check(solver.countSolutions(full, 10) == 1, "a complete grid counts 1");
	check(solver.countSolutions(empty, 1000) == 1000, "the empty grid stops counting at the limit");
}


// two rows and two columns in different boxes holding  a b / b a.
// blanking those 4 cells in a complete grid leaves exactly 2 solutions (swap a and b)
bool isDeadlyRectangle(const int grid[9][9], int r1, int r2, int c1, int c2) {
	bool sameBand = r1 / 3 == r2 / 3 && r1 != r2;  // rows share boxes
	bool differentStacks = c1 / 3 != c2 / 3;       // columns don't
	return sameBand && differentStacks && grid[r1][c1] == grid[r2][c2] && grid[r1][c2] == grid[r2][c1];
}

bool blankDeadlyRectangle(int grid[9][9]) {
	for (int r1 = 0; r1 < 9; r1++) {
		for (int r2 = r1 + 1; r2 < 9; r2++) {
			for (int c1 = 0; c1 < 9; c1++) {
				for (int c2 = c1 + 1; c2 < 9; c2++) {
					if (isDeadlyRectangle(grid, r1, r2, c1, c2)) {
						grid[r1][c1] = grid[r1][c2] = grid[r2][c1] = grid[r2][c2] = 0;
						return true;
					}
				}
			}
		}
	}
	return false;
}

void testDeadlyRectangleHasTwoSolutions() {
	SudokuSolver solver;
	int grid[9][9];
	solver.solve(hardPuzzle("inkala2012").grid, grid);
	if (!blankDeadlyRectangle(grid)) {
		std::printf("skipped deadly rectangle: none in this grid\n");
		return;
	}
	check(solver.countSolutions(grid, 10) == 2 && naiveCount(grid, 10) == 2, "a deadly rectangle counts exactly 2");
}


// a data puzzle with extra random cells blanked, which usually leaves it with several solutions
Puzzle withExtraBlanks(Puzzle p, std::mt19937 &rng) {
	for (int blanks = 0; blanks < 25; blanks++) {
		p.grid[rng() % 9][rng() % 9] = 0;
	}
	return p;
}


// exact count matches the naive counter, and solve() finds a valid solution exactly when one exists
bool agreesWithNaiveCounter(SudokuSolver &solver, Puzzle const &p, std::string &mismatch) {
	int out[9][9];
	int mine = solver.countSolutions(p.grid, 5000);
	int naive = naiveCount(p.grid, 5000);
	bool solveAgrees = solver.solve(p.grid, out) == (mine > 0) && (mine == 0 || validSolution(p.grid, out));
	if (mine == naive && solveAgrees) {
		return true;
	}
	mismatch = p.name + ": " + std::to_string(mine) + " vs naive " + std::to_string(naive);
	return false;
}


// the 69/79-clue puzzles with extra blanks give puzzles with 1 to hundreds of solutions
void testCountsMatchNaiveCounter() {
	SudokuSolver solver;
	std::mt19937 rng(12345);
	int compared = 0, withSeveral = 0, mismatches = 0;
	std::string firstMismatch;
	for (int clues : {69, 79}) {
		for (Puzzle const &original : readPuzzleFile(dataPath(clues))) {
			Puzzle p = withExtraBlanks(original, rng);
			std::string mismatch;
			if (!agreesWithNaiveCounter(solver, p, mismatch)) {
				mismatches++;
				if (firstMismatch.empty()) firstMismatch = mismatch;
			}
			compared++;
			withSeveral += solver.countSolutions(p.grid) > 1;
		}
	}
	std::string name = "counts match the naive counter on " + std::to_string(compared) + " puzzles, " +
	                   std::to_string(withSeveral) + " with several solutions";
	check(compared > 0 && mismatches == 0, name, compared == 0 ? "no data found, run from the repo root" : firstMismatch);
}



int main() {
	testKnownUniquePuzzles();
	testNoSolution();
	testConflictingClues();
	testCompleteAndEmptyGrids();
	testDeadlyRectangleHasTwoSolutions();
	testCountsMatchNaiveCounter();

	std::printf("\n%s\n", failures == 0 ? "all tests passed" : (std::to_string(failures) + " test(s) failed").c_str());
	return failures == 0 ? 0 : 1;
}
