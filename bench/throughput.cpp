/*
One process of the throughput benchmark (bench/throughput.py runs several at once): solves its share of a data set
(every processes-th puzzle)
with one solver, starting at a given wall-clock time, and prints when it finished. Separate processes, because tdoku
and jsolve keep their state in global variables.

usage: throughput <fastband|tdoku|jsolve|kudoku> <data file> <index> <processes> <reps> <start, ns since epoch> [limit]
*/
#include "../fastbandsolver.hpp"
#include "jsolve/JSolve.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#ifdef __APPLE__
#include <pthread.h>
#include <sys/qos.h>
#endif

using SolverFn = size_t (*)(const char *, size_t, uint32_t, char *, size_t *);
extern "C" size_t TdokuSolverDpllTriadSimd(const char *, size_t, uint32_t, char *, size_t *);
extern "C" size_t OtherSolverKudoku(const char *, size_t, uint32_t, char *, size_t *);

size_t JSolve_guesses;  // tdoku's copy of JSolve counts guesses into this; unused here

extern "C" size_t JSolveAdapter(const char *puzzle, size_t limit, uint32_t, char *solution, size_t *) {
	return JSolve(puzzle, solution, (int) limit);
}

extern "C" size_t FastBandAdapter(const char *puzzle, size_t limit, uint32_t, char *, size_t *) {
	static FastBandSolver solver;
	int grid[9][9];
	for (int cell = 0; cell < 81; cell++) grid[cell / 9][cell % 9] = puzzle[cell] == '.' ? 0 : puzzle[cell] - '0';
	return solver.countSolutions(grid, (int) limit);
}


long long nowNs() {
	return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
}


int main(int argc, char **argv) {
	if (argc != 7 && argc != 8) {
		std::fprintf(stderr, "usage: %s <fastband|tdoku|jsolve|kudoku> <data file> <index> <processes> <reps> <start> [limit]\n", argv[0]);
		return 1;
	}
#ifdef __APPLE__
	pthread_set_qos_class_self_np(QOS_CLASS_USER_INTERACTIVE, 0);
#endif
	std::string name = argv[1];
	SolverFn solve = name == "tdoku" ? TdokuSolverDpllTriadSimd : name == "jsolve" ? JSolveAdapter
	               : name == "kudoku" ? OtherSolverKudoku : FastBandAdapter;
	int index = std::atoi(argv[3]), processes = std::atoi(argv[4]), reps = std::atoi(argv[5]);
	long long start = std::atoll(argv[6]);
	size_t limit = argc == 8 ? std::atoi(argv[7]) : 2;
	std::vector<std::string> puzzles;
	std::ifstream file(argv[2]);
	std::string line;
	while (std::getline(file, line)) {
		if (line.size() >= 81 && line[0] != '#') puzzles.push_back(line.substr(0, 81));
	}
	// every processes-th puzzle, not a block: hard puzzles cluster in the files, and blocks left some processes with
	// much more work than others
	std::vector<std::string> share;
	for (size_t i = index; i < puzzles.size(); i += processes) share.push_back(puzzles[i]);
	while (nowNs() < start) {}
	char solution[82];
	size_t guesses, sink = 0;
	for (int r = 0; r < reps; r++) {
		for (auto const &p : share) sink += solve(p.c_str(), limit, 0, solution, &guesses);
	}
	std::printf("%lld %zu %zu\n", nowNs(), share.size() * reps, sink);
	return 0;
}
