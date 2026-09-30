/*
Time per puzzle for one puzzle at a time: parallelbandsolver on several threads, against fastbandsolver and tdoku on
one. Limit 2, median of the runs, solvers taking turns. Every solver's solution counts are checked against tdoku's
first.

Built by `make parallel`, which needs a tdoku checkout at ../tdoku (see the README).

usage: parallel <reps> <threads,threads,...> <data file>...
the solution limit is 2, or the LIMIT environment variable
*/
#include "../parallelbandsolver.hpp"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

extern "C" size_t TdokuSolverDpllTriadSimd(const char *, size_t, uint32_t, char *, size_t *);

int limit = 2;

struct Puzzle {
	std::string text;
	int grid[9][9];
};


std::vector<Puzzle> readPuzzles(const char *path) {
	std::vector<Puzzle> puzzles;
	std::ifstream file(path);
	std::string line;
	while (std::getline(file, line)) {
		if (line.size() < 81 || line[0] == '#') continue;
		Puzzle p;
		p.text = line.substr(0, 81);
		for (int cell = 0; cell < 81; cell++) p.grid[cell / 9][cell % 9] = p.text[cell] == '.' ? 0 : p.text[cell] - '0';
		puzzles.push_back(p);
	}
	return puzzles;
}


int tdokuCount(Puzzle const &p) {
	char solution[82];
	size_t guesses;
	return (int) TdokuSolverDpllTriadSimd(p.text.c_str(), limit, 0, solution, &guesses);
}


// at limit 1 every solver writes out the solution it finds, as tdoku does
template <class Solver> int countWith(Solver &s, Puzzle const &p) {
	if (limit != 1) return s.countSolutions(p.grid, limit);
	int out[9][9];
	return s.solve(p.grid, out) ? 1 : 0;
}


template <class Count> double secondsPerPuzzle(std::vector<Puzzle> const &puzzles, Count count) {
	long sink = 0;
	auto start = std::chrono::steady_clock::now();
	for (auto const &p : puzzles) sink += count(p);
	double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
	if (sink == 0) std::printf("(nothing solved)\n");
	return seconds / puzzles.size();
}


int main(int argc, char **argv) {
	if (argc < 4) {
		std::fprintf(stderr, "usage: %s <reps> <threads,threads,...> <data file>...\n", argv[0]);
		return 1;
	}
	int reps = std::atoi(argv[1]);
	if (std::getenv("LIMIT")) limit = std::atoi(std::getenv("LIMIT"));
	std::vector<int> threadCounts;
	for (char *t = std::strtok(argv[2], ","); t; t = std::strtok(nullptr, ",")) threadCounts.push_back(std::atoi(t));

	FastBandSolver fast;

	std::printf("microseconds per puzzle, limit %d, median of %d runs\n\n%-34s %9s %9s", limit, reps, "data set", "tdoku", "fastband");
	for (int t : threadCounts) std::printf("  %2d threads", t);
	std::printf("\n");
	int problems = 0;
	for (int a = 3; a < argc; a++) {
		std::vector<Puzzle> puzzles = readPuzzles(argv[a]);
		for (auto const &p : puzzles) problems += countWith(fast, p) != tdokuCount(p);
		for (int t : threadCounts) {
			ParallelBandSolver parallel(t);
			for (auto const &p : puzzles) problems += countWith(parallel, p) != tdokuCount(p);
		}
		size_t n = 2 + threadCounts.size();
		std::vector<std::vector<double>> times(n);
		for (int r = 0; r < reps; r++) {
			times[0].push_back(secondsPerPuzzle(puzzles, tdokuCount));
			times[1].push_back(secondsPerPuzzle(puzzles, [&](Puzzle const &p) { return countWith(fast, p); }));
			for (size_t i = 0; i < threadCounts.size(); i++) {
				// one pool of threads at a time, so idle workers of other pools can't interfere; creating it isn't timed
				ParallelBandSolver parallel(threadCounts[i]);
				times[2 + i].push_back(secondsPerPuzzle(puzzles, [&](Puzzle const &p) { return countWith(parallel, p); }));
			}
		}
		std::string path = argv[a];
		std::printf("%-34s", path.substr(path.find_last_of('/') + 1).c_str());
		for (auto &t : times) {
			std::sort(t.begin(), t.end());
			std::printf(" %9.3f", t[t.size() / 2] * 1e6);
		}
		std::printf("\n");
		std::fflush(stdout);
	}
	std::printf("\n%s\n", problems ? "some solution counts disagree with tdoku" : "every solver agrees with tdoku on every puzzle");
	return problems ? 1 : 0;
}
