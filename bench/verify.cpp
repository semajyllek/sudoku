/*
Checks FastBandSolver against tdoku on whole data sets: solution counts at limits 1, 2 and 3 must agree, and at
limit 1 FastBandSolver's solution must be a valid grid that keeps the clues, and equal tdoku's when the puzzle has
exactly one solution. make verify runs it on all seven of tdoku's data sets (709,764 puzzles, including
puzzles with several solutions and with none).

usage: verify <data file>...
*/
#include "../fastbandsolver.hpp"
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

extern "C" size_t TdokuSolverDpllTriadSimd(const char *, size_t, uint32_t, char *, size_t *);


bool validSolution(std::string const &puzzle, int const grid[9][9]) {
	for (int cell = 0; cell < 81; cell++) {
		int d = grid[cell / 9][cell % 9];
		if (d < 1 || d > 9) return false;
		if (puzzle[cell] != '.' && puzzle[cell] != '0' && puzzle[cell] - '0' != d) return false;
	}
	for (int i = 0; i < 9; i++) {
		int row = 0, col = 0, box = 0;
		for (int j = 0; j < 9; j++) {
			row |= 1 << grid[i][j];
			col |= 1 << grid[j][i];
			box |= 1 << grid[i / 3 * 3 + j / 3][i % 3 * 3 + j % 3];
		}
		if (row != 01776 || col != 01776 || box != 01776) return false;
	}
	return true;
}


int main(int argc, char **argv) {
	FastBandSolver solver;
	long total = 0, problems = 0;
	for (int a = 1; a < argc; a++) {
		std::ifstream file(argv[a]);
		std::string line;
		long n = 0, bad = 0;
		while (std::getline(file, line)) {
			if (line.size() < 81 || line[0] == '#') continue;
			std::string p = line.substr(0, 81);
			int grid[9][9], out[9][9];
			for (int cell = 0; cell < 81; cell++) grid[cell / 9][cell % 9] = p[cell] == '.' ? 0 : p[cell] - '0';
			char tdokuSolution[82] = {};
			size_t guesses;
			bool ok = true;
			for (int limit = 1; limit <= 3; limit++) {
				size_t expected = TdokuSolverDpllTriadSimd(p.c_str(), limit, 0, tdokuSolution, &guesses);
				ok &= (size_t) solver.countSolutions(grid, limit) == expected;
			}
			size_t count = TdokuSolverDpllTriadSimd(p.c_str(), 2, 0, tdokuSolution, &guesses);
			bool solved = solver.solve(grid, out);
			ok &= solved == (count > 0);
			if (solved) {
				ok &= validSolution(p, out);
				if (count == 1) {
					for (int cell = 0; cell < 81; cell++) ok &= out[cell / 9][cell % 9] == tdokuSolution[cell] - '0';
				}
			}
			if (!ok && bad < 3) std::printf("mismatch: %s\n", p.c_str());
			bad += !ok;
			n++;
		}
		std::printf("%-36s %7ld puzzles, %ld problems\n", argv[a], n, bad);
		total += n;
		problems += bad;
	}
	std::printf("%ld puzzles, %s\n", total, problems ? "SOME PROBLEMS" : "all agree with tdoku");
	return problems ? 1 : 0;
}
