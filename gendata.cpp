/*
Generates the benchmark data in data/: 1000 puzzles per clue count, every one with exactly one solution.

For each puzzle:
  1. make a random complete grid. the 3 diagonal boxes don't constrain each other, so they are filled
     with random permutations of 1-9, and the solver fills in the rest
  2. blank cells in random order, keeping each blank only if the puzzle still has exactly one solution,
     until it has the target number of clues. if no more cells can be blanked before reaching the target,
     start over with a new grid

usage: gendata [seed]    the same seed always produces the same files
*/
#include "sudokusolver.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <numeric>
#include <random>
#include <string>
#include <vector>


const int CLUE_COUNTS[] = {22, 29, 39, 49, 59, 69, 79};
const int PUZZLES_PER_FILE = 1000;
const unsigned DEFAULT_SEED = 1;

struct Grid {
	int cells[9][9] = {};
};

struct Generated {
	Grid puzzle;
	Grid solution;
};



Grid randomSolvedGrid(SudokuSolver &solver, std::mt19937 &rng) {
	Grid diagonal;
	for (int box = 0; box < 3; box++) {
		int digits[9];
		std::iota(digits, digits + 9, 1);
		std::shuffle(digits, digits + 9, rng);
		for (int k = 0; k < 9; k++) {
			diagonal.cells[box * 3 + k / 3][box * 3 + k % 3] = digits[k];
		}
	}
	Grid solved;
	solver.solve(diagonal.cells, solved.cells);  // always succeeds, the diagonal boxes can't conflict
	return solved;
}


// blanks cells of the solution in random order while the solution stays unique.
// false if it gets stuck with more than targetClues clues
bool blankToClueCount(Grid &puzzle, int targetClues, SudokuSolver &solver, std::mt19937 &rng) {
	int order[81];
	std::iota(order, order + 81, 0);
	std::shuffle(order, order + 81, rng);

	int clues = 81;
	for (int cell : order) {
		if (clues == targetClues) {
			return true;
		}
		int &value = puzzle.cells[cell / 9][cell % 9];
		int kept = value;
		value = 0;
		if (solver.hasUniqueSolution(puzzle.cells)) {
			clues--;
		} else {
			value = kept;
		}
	}
	return clues == targetClues;
}


Generated generatePuzzle(int targetClues, SudokuSolver &solver, std::mt19937 &rng, int &attempts) {
	while (true) {
		attempts++;
		Generated g;
		g.solution = randomSolvedGrid(solver, rng);
		g.puzzle = g.solution;
		if (blankToClueCount(g.puzzle, targetClues, solver, rng)) {
			return g;
		}
	}
}



void writeGrid(std::ofstream &file, Grid const &grid) {
	for (int r = 0; r < 9; r++) {
		for (int c = 0; c < 9; c++) {
			file << grid.cells[r][c] << (c < 8 ? "," : "\n");
		}
	}
}


// same layout ArrayBoard::saveBoard writes, which loadBoards in utils.hpp reads
void writeFile(std::string const &path, std::vector<Generated> const &puzzles) {
	std::ofstream file(path);
	for (auto const &g : puzzles) {
		file << "\nNew Board: \n";
		writeGrid(file, g.puzzle);
		file << "\nSolved Board:\n";
		writeGrid(file, g.solution);
	}
}


std::string dataPath(int clues) {
	return "data/board" + std::to_string(clues) + "__" + std::to_string(PUZZLES_PER_FILE) + ".txt";
}


int main(int argc, char **argv) {
	unsigned seed = argc > 1 ? std::strtoul(argv[1], nullptr, 10) : DEFAULT_SEED;
	std::mt19937 rng(seed);
	SudokuSolver solver;

	for (int clues : CLUE_COUNTS) {
		auto start = std::chrono::steady_clock::now();
		std::vector<Generated> puzzles;
		int attempts = 0;
		while ((int)puzzles.size() < PUZZLES_PER_FILE) {
			puzzles.push_back(generatePuzzle(clues, solver, rng, attempts));
		}
		writeFile(dataPath(clues), puzzles);
		std::chrono::duration<double> elapsed = std::chrono::steady_clock::now() - start;
		std::printf("%s: %d puzzles from %d grids in %.2f s\n", dataPath(clues).c_str(), PUZZLES_PER_FILE, attempts, elapsed.count());
	}
	return 0;
}
