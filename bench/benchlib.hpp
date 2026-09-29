/*
Benchmark harness shared by every solver. Each solver is wrapped in a Solver type with
	bool solve(const int in[9][9], int out[9][9]);
and compiled into its own binary (utils.hpp can't be included twice in one program).

- every answer is checked against the rules and the clues, not against the stored solution
- timing includes all of a solver's setup, since that is part of solving
- the parallel mode gives each thread its own Solver, so nothing is shared

run from the repo root, it reads the files in data/
*/
#pragma once
#include "../puzzles.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <thread>
#include <vector>


using Clock = std::chrono::steady_clock;

struct EachPuzzleRun {
	std::vector<double> micros;  // one per puzzle
	int solved = 0;              // solved with a valid grid
	int invalid = 0;             // claimed solved, but the grid is wrong
};

struct ParallelRun {
	double millis = 0;           // wall time for the whole set
	int valid = 0;
};


inline double percentile(std::vector<double> values, double p) {
	std::sort(values.begin(), values.end());
	return values[std::min(values.size() - 1, (size_t)(p * values.size()))];
}


inline double microsSince(Clock::time_point start) {
	return std::chrono::duration<double, std::micro>(Clock::now() - start).count();
}


inline std::string setLabel(int clues) {
	return std::to_string(clues) + " clues";
}



// solves each puzzle once, timed individually, and checks every answer
template <class Solver>
EachPuzzleRun timeEachPuzzle(Solver &solver, std::vector<Puzzle> const &puzzles) {
	EachPuzzleRun run;
	int out[9][9];
	for (auto const &p : puzzles) {
		auto start = Clock::now();
		bool ok = solver.solve(p.grid, out);
		run.micros.push_back(microsSince(start));
		if (ok) {
			validSolution(p.grid, out) ? run.solved++ : run.invalid++;
		}
	}
	return run;
}


// mean microseconds per puzzle: median over reps of timing the whole set at once,
// which avoids the clock's resolution limit on sub-microsecond solves
template <class Solver>
double timeWholeSet(Solver &solver, std::vector<Puzzle> const &puzzles, int reps) {
	int out[9][9];
	std::vector<double> perPuzzle;
	for (int r = 0; r < reps; r++) {
		auto start = Clock::now();
		for (auto const &p : puzzles) {
			solver.solve(p.grid, out);
		}
		perPuzzle.push_back(microsSince(start) / puzzles.size());
	}
	return percentile(perPuzzle, 0.5);
}


// solves the whole set with `threads` threads, each with its own Solver, taking puzzles from a shared counter
template <class Solver>
ParallelRun solveInParallel(std::vector<Puzzle> const &puzzles, int threads) {
	std::atomic<size_t> next{0};
	std::atomic<int> valid{0};
	std::vector<std::thread> pool;
	auto start = Clock::now();
	for (int t = 0; t < threads; t++) {
		pool.emplace_back([&] {
			auto solver = std::make_unique<Solver>();
			int out[9][9];
			for (size_t i = next++; i < puzzles.size(); i = next++) {
				if (solver->solve(puzzles[i].grid, out) && validSolution(puzzles[i].grid, out)) valid++;
			}
		});
	}
	for (auto &thread : pool) {
		thread.join();
	}
	return {microsSince(start) / 1000, valid};
}



template <class Solver>
void runDataMode(Solver &solver, int reps) {
	std::printf("%-10s %5s %6s %7s %9s %8s %9s %11s\n", "set", "n", "solved", "invalid", "mean_us", "p50_us", "p99_us", "max_us");
	for (int clues : CLUE_COUNTS) {
		auto puzzles = readPuzzleFile(dataPath(clues));
		if (puzzles.empty()) {
			std::printf("%-10s missing or empty: %s\n", setLabel(clues).c_str(), dataPath(clues).c_str());
			continue;
		}
		EachPuzzleRun run = timeEachPuzzle(solver, puzzles);
		double mean = timeWholeSet(solver, puzzles, reps);
		std::printf("%-10s %5zu %6d %7d %9.2f %8.2f %9.2f %11.2f\n", setLabel(clues).c_str(), puzzles.size(), run.solved, run.invalid,
		            mean, percentile(run.micros, 0.5), percentile(run.micros, 0.99), percentile(run.micros, 1.0));
		std::fflush(stdout);
	}
}


// threadCounts must start with 1, which every speedup is relative to
template <class Solver>
void runParallelMode(int reps, std::vector<int> const &threadCounts) {
	std::printf("%-10s %5s %8s %10s %9s %6s\n", "set", "n", "threads", "batch_ms", "speedup", "valid");
	for (int clues : CLUE_COUNTS) {
		auto puzzles = readPuzzleFile(dataPath(clues));
		if (puzzles.empty()) continue;
		double oneThread = 0;
		for (int threads : threadCounts) {
			std::vector<double> millis;
			int valid = 0;
			for (int r = 0; r < reps; r++) {
				ParallelRun run = solveInParallel<Solver>(puzzles, threads);
				millis.push_back(run.millis);
				valid = run.valid;
			}
			double ms = percentile(millis, 0.5);
			if (threads == 1) oneThread = ms;
			std::printf("%-10s %5zu %8d %10.2f %8.2fx %6d\n", setLabel(clues).c_str(), puzzles.size(), threads, ms, oneThread / ms, valid);
			std::fflush(stdout);
		}
	}
}


template <class Solver>
void runHardMode(Solver &solver, std::string const &which) {
	int out[9][9];
	for (auto const &p : hardPuzzles()) {
		if (which != "all" && which != p.name) continue;
		auto start = Clock::now();
		bool ok = solver.solve(p.grid, out);
		double micros = microsSince(start);
		const char *result = !ok ? "unsolved" : validSolution(p.grid, out) ? "valid" : "INVALID";
		std::printf("%-20s %-8s %12.1f us\n", p.name.c_str(), result, micros);
		std::fflush(stdout);
	}
}


inline std::vector<int> parseThreadCounts(int argc, char **argv) {
	std::vector<int> counts;
	for (int a = 3; a < argc; a++) {
		counts.push_back(std::atoi(argv[a]));
	}
	if (counts.empty()) counts = {(int)std::thread::hardware_concurrency()};
	if (counts.front() != 1) counts.insert(counts.begin(), 1);
	return counts;
}


// usage: <bin> data [reps]                      the data files, single thread (default)
//        <bin> hard [name|all]                  hand-picked puzzles, one line each
//        <bin> par [reps] [threads...]          whole-set wall time across puzzles vs 1 thread
template <class Solver>
int benchMain(int argc, char **argv) {
	std::string mode = argc > 1 ? argv[1] : "data";
	auto solver = std::make_unique<Solver>();
	if (mode == "data") {
		runDataMode(*solver, argc > 2 ? std::atoi(argv[2]) : 5);
	} else if (mode == "hard") {
		runHardMode(*solver, argc > 2 ? argv[2] : "all");
	} else if (mode == "par") {
		runParallelMode<Solver>(argc > 2 ? std::atoi(argv[2]) : 5, parseThreadCounts(argc, argv));
	} else {
		std::fprintf(stderr, "usage: %s data [reps] | hard [name|all] | par [reps] [threads...]\n", argv[0]);
		return 1;
	}
	return 0;
}
