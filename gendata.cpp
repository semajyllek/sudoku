/*
Generates the benchmark data in data/: PUZZLES_PER_FILE puzzles per clue count, every one with exactly one solution.

For each puzzle:
  1. make a random complete grid. the 3 diagonal boxes don't constrain each other, so they are filled
     with random permutations of 1-9, and the solver fills in the rest
  2. blank cells in random order, keeping each blank only if the puzzle still has exactly one solution,
     until it has the target number of clues. if no more cells can be blanked before reaching the target,
     start over with a new grid

usage: gendata [seed]    the same seed always produces the same files
*/
#include "sudokusolver.hpp"
#include "puzzles.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <optional>
#include <random>
#include <vector>


const unsigned DEFAULT_SEED = 1;

struct GeneratedFile {
	std::vector<Puzzle> puzzles;
	int gridsTried = 0;
};



// a puzzle with no clues yet, and a random complete grid as its solution
Puzzle randomSolvedPuzzle(SudokuSolver &solver, std::mt19937 &rng) {
	int diagonal[9][9] = {};
	for (int box = 0; box < 3; box++) {
		int digits[9];
		std::iota(digits, digits + 9, 1);
		std::shuffle(digits, digits + 9, rng);
		for (int k = 0; k < 9; k++) {
			diagonal[box * 3 + k / 3][box * 3 + k % 3] = digits[k];
		}
	}
	Puzzle p;
	p.hasSolution = solver.solve(diagonal, p.solution);  // always succeeds, the diagonal boxes can't conflict
	return p;
}


// blanks cells of the full grid in random order while the solution stays unique.
// false if it gets stuck with more than targetClues clues
bool blankToClueCount(int grid[9][9], int targetClues, SudokuSolver &solver, std::mt19937 &rng) {
	int order[81];
	std::iota(order, order + 81, 0);
	std::shuffle(order, order + 81, rng);

	int clues = 81;
	for (int cell : order) {
		if (clues == targetClues) {
			return true;
		}
		int &value = grid[cell / 9][cell % 9];
		int kept = value;
		value = 0;
		if (solver.hasUniqueSolution(grid)) {
			clues--;
		} else {
			value = kept;
		}
	}
	return clues == targetClues;
}


// one attempt from one random grid; nothing if that grid can't get down to targetClues
std::optional<Puzzle> tryGeneratePuzzle(int targetClues, SudokuSolver &solver, std::mt19937 &rng) {
	Puzzle p = randomSolvedPuzzle(solver, rng);
	std::copy(&p.solution[0][0], &p.solution[0][0] + 81, &p.grid[0][0]);
	if (!blankToClueCount(p.grid, targetClues, solver, rng)) {
		return std::nullopt;
	}
	return p;
}


GeneratedFile generateFile(int targetClues, SudokuSolver &solver, std::mt19937 &rng) {
	GeneratedFile file;
	while ((int)file.puzzles.size() < PUZZLES_PER_FILE) {
		file.gridsTried++;
		if (std::optional<Puzzle> p = tryGeneratePuzzle(targetClues, solver, rng)) {
			file.puzzles.push_back(*p);
		}
	}
	return file;
}



int main(int argc, char **argv) {
	unsigned seed = argc > 1 ? std::strtoul(argv[1], nullptr, 10) : DEFAULT_SEED;
	std::mt19937 rng(seed);
	SudokuSolver solver;

	for (int clues : CLUE_COUNTS) {
		auto start = std::chrono::steady_clock::now();
		GeneratedFile file = generateFile(clues, solver, rng);
		writePuzzleFile(dataPath(clues), file.puzzles);
		std::chrono::duration<double> elapsed = std::chrono::steady_clock::now() - start;
		std::printf("%s: %zu puzzles from %d grids in %.2f s\n", dataPath(clues).c_str(), file.puzzles.size(), file.gridsTried, elapsed.count());
	}
	return 0;
}
