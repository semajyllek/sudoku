/*
Compares sudokusolver and fastbandsolver with tdoku, jsolve and kudoku on tdoku's standard data sets.

All five run through tdoku's solver interface, with a limit of 2 solutions (so each also checks the solution is
unique), as in tdoku's published benchmarks. Before timing, every solver must solve every puzzle with a valid
solution and agree with sudokusolver on how many solutions it has.

Built by `make sota`, which needs a tdoku checkout at ../tdoku (see the README).

usage: sota <reps> <data file>...
the solution limit is 2, or the LIMIT environment variable (1: find one solution, without checking uniqueness)
*/
#include "../sudokusolver.hpp"
#include "../fastbandsolver.hpp"
#include "jsolve/JSolve.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

using SolverFn = size_t (*)(const char *puzzle, size_t limit, uint32_t configuration, char *solution, size_t *guesses);

extern "C" size_t TdokuSolverDpllTriadSimd(const char *, size_t, uint32_t, char *, size_t *);
extern "C" size_t OtherSolverKudoku(const char *, size_t, uint32_t, char *, size_t *);

size_t JSolve_guesses;  // JSolve.c counts guesses into this (tdoku's patch)

extern "C" size_t OtherSolverJSolve(const char *puzzle, size_t limit, uint32_t, char *solution, size_t *guesses) {
	JSolve_guesses = 0;
	int count = JSolve(puzzle, solution, (int) limit);
	*guesses = JSolve_guesses;
	return count;
}

// reading the puzzle string is part of each call, as it is for the other solvers
extern "C" size_t SudokuSolverAdapter(const char *puzzle, size_t limit, uint32_t, char *solution, size_t *guesses) {
	static SudokuSolver solver;
	int grid[9][9];
	for (int cell = 0; cell < 81; cell++) {
		grid[cell / 9][cell % 9] = puzzle[cell] == '.' ? 0 : puzzle[cell] - '0';
	}
	*guesses = 0;
	if (limit != 1) {
		return solver.countSolutions(grid, (int) limit);
	}
	int out[9][9];
	if (!solver.solve(grid, out)) {
		return 0;
	}
	for (int cell = 0; cell < 81; cell++) {
		solution[cell] = char('0' + out[cell / 9][cell % 9]);
	}
	return 1;
}

extern "C" size_t FastBandSolverAdapter(const char *puzzle, size_t limit, uint32_t, char *solution, size_t *guesses) {
	static FastBandSolver solver;
	int grid[9][9];
	for (int cell = 0; cell < 81; cell++) {
		grid[cell / 9][cell % 9] = puzzle[cell] == '.' ? 0 : puzzle[cell] - '0';
	}
	if (limit != 1) {
		int count = solver.countSolutions(grid, (int) limit);
		*guesses = solver.guesses;
		return count;
	}
	int out[9][9];
	bool solved = solver.solve(grid, out);
	*guesses = solver.guesses;
	if (!solved) {
		return 0;
	}
	for (int cell = 0; cell < 81; cell++) {
		solution[cell] = char('0' + out[cell / 9][cell % 9]);
	}
	return 1;
}

struct Solver {
	const char *name;
	SolverFn solve;
};

const std::vector<Solver> SOLVERS = {
	{"sudokusolver", SudokuSolverAdapter},
	{"fastbandsolver", FastBandSolverAdapter},
	{"tdoku", TdokuSolverDpllTriadSimd},
	{"jsolve", OtherSolverJSolve},
	{"kudoku", OtherSolverKudoku},
};



std::vector<std::string> readPuzzles(const char *path) {
	std::vector<std::string> puzzles;
	std::ifstream file(path);
	std::string line;
	while (std::getline(file, line)) {
		if (line.size() >= 81 && line[0] != '#') puzzles.push_back(line.substr(0, 81));
	}
	return puzzles;
}


bool validSolution(std::string const &puzzle, const char *solution) {
	for (int cell = 0; cell < 81; cell++) {
		if (solution[cell] < '1' || solution[cell] > '9') return false;
		if (puzzle[cell] != '.' && puzzle[cell] != solution[cell]) return false;
	}
	for (int unit = 0; unit < 9; unit++) {
		int row = 0, col = 0, box = 0;
		for (int k = 0; k < 9; k++) {
			row |= 1 << (solution[unit * 9 + k] - '0');
			col |= 1 << (solution[k * 9 + unit] - '0');
			box |= 1 << (solution[(unit / 3 * 3 + k / 3) * 9 + unit % 3 * 3 + k % 3] - '0');
		}
		if (row != 0x3fe || col != 0x3fe || box != 0x3fe) return false;
	}
	return true;
}


// puzzles the solver gets wrong: no valid solution, or a different solution count than sudokusolver
int countProblems(Solver const &solver, std::vector<std::string> const &puzzles) {
	int problems = 0;
	char solution[82], unused[82];
	size_t guesses;
	for (auto const &p : puzzles) {
		bool solved = solver.solve(p.c_str(), 1, 0, solution, &guesses) == 1 && validSolution(p, solution);
		bool countAgrees = solver.solve(p.c_str(), 2, 0, unused, &guesses) == SudokuSolverAdapter(p.c_str(), 2, 0, unused, &guesses);
		problems += !solved || !countAgrees;
	}
	return problems;
}


size_t timingLimit = 2;


double secondsPerPuzzle(Solver const &solver, std::vector<std::string> const &puzzles) {
	char solution[82];
	size_t guesses;
	auto start = std::chrono::steady_clock::now();
	for (auto const &p : puzzles) {
		solver.solve(p.c_str(), timingLimit, 0, solution, &guesses);
	}
	return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() / puzzles.size();
}


// solvers take turns so any drift in machine speed affects them all alike; returns the median per solver
std::vector<double> medianTimes(std::vector<std::string> const &puzzles, int reps) {
	std::vector<std::vector<double>> times(SOLVERS.size());
	for (int r = 0; r < reps; r++) {
		for (size_t s = 0; s < SOLVERS.size(); s++) {
			times[s].push_back(secondsPerPuzzle(SOLVERS[s], puzzles));
		}
	}
	std::vector<double> medians;
	for (auto &t : times) {
		std::sort(t.begin(), t.end());
		medians.push_back(t[t.size() / 2]);
	}
	return medians;
}


// significant figures of printed times (DIGITS in the environment); 2 gives e.g. 0.0000084
int digits = 2;

std::string decimalSeconds(double seconds) {
	int decimals = std::max(0, digits - 1 - (int) std::floor(std::log10(seconds)));
	char text[32];
	std::snprintf(text, sizeof text, "%.*f", decimals, seconds);
	return text;
}


std::string setName(std::string const &path) {
	return path.substr(path.find_last_of('/') + 1);
}



int main(int argc, char **argv) {
	if (argc < 3) {
		std::fprintf(stderr, "usage: %s <reps> <data file>...\n", argv[0]);
		return 1;
	}
	int reps = std::atoi(argv[1]);
	if (std::getenv("LIMIT")) timingLimit = std::atoi(std::getenv("LIMIT"));
	if (std::getenv("DIGITS")) digits = std::max(1, std::atoi(std::getenv("DIGITS")));
	size_t fast = 0, tdoku = 0;
	for (size_t s = 0; s < SOLVERS.size(); s++) {
		if (std::string(SOLVERS[s].name) == "fastbandsolver") fast = s;
		if (std::string(SOLVERS[s].name) == "tdoku") tdoku = s;
	}
	std::printf("seconds per puzzle, limit %zu, median of %d runs\n\n%-34s %7s", timingLimit, reps, "data set", "puzzles");
	for (auto const &s : SOLVERS) std::printf(" %15s", s.name);
	std::printf(" %15s\n", "tdoku/fastband");

	int problems = 0;
	for (int a = 2; a < argc; a++) {
		std::vector<std::string> puzzles = readPuzzles(argv[a]);
		for (auto const &s : SOLVERS) {
			int bad = countProblems(s, puzzles);
			if (bad) std::printf("%s: %d puzzles unsolved, invalid or miscounted in %s\n", s.name, bad, argv[a]);
			problems += bad;
		}
		std::vector<double> times = medianTimes(puzzles, reps);
		std::printf("%-34s %7zu", setName(argv[a]).c_str(), puzzles.size());
		for (double t : times) std::printf(" %15s", decimalSeconds(t).c_str());
		// from the unrounded medians
		std::printf(" %15.3f\n", times[tdoku] / times[fast]);
		std::fflush(stdout);
	}
	std::printf("\n%s\n", problems ? "some answers were wrong, see above" : "every solver solved every puzzle correctly");
	return problems ? 1 : 0;
}
