/*
Benchmark harness shared by every solver. Each solver is wrapped in a Solver type with
	bool solve(const int in[9][9], int out[9][9]);
and compiled into its own binary (utils.hpp can't be included twice in one program).

- every answer is checked against the rules and the clues, not against the stored solution,
  since low-clue puzzles have many valid solutions (and many stored solutions don't match their clues)
- timing includes all of a solver's setup, since that is part of solving
- the parallel mode gives each thread its own Solver, so nothing is shared

run from the repo root, data is read from data/board<clues>__1000.txt
*/
#pragma once
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <sstream>
#include <string>
#include <thread>
#include <vector>


struct Puzzle {
	std::string name;
	int grid[9][9] = {};
	int solution[9][9] = {};
	bool hasSolution = false;
};

using Clock = std::chrono::steady_clock;

inline const int CLUE_COUNTS[] = {22, 29, 39, 49, 59, 69, 79};  // the files gendata writes


inline std::string dataPath(int clues) {
	return "data/board" + std::to_string(clues) + "__1000.txt";
}


inline bool readGrid(std::ifstream &file, int grid[9][9]) {
	std::string line, cell;
	for (int r = 0; r < 9; r++) {
		if (!std::getline(file, line)) return false;
		std::stringstream cells(line);
		for (int c = 0; c < 9; c++) {
			if (!std::getline(cells, cell, ',')) return false;
			grid[r][c] = std::stoi(cell);
		}
	}
	return true;
}


// reads the "New Board:" / "Solved Board:" format that gendata writes
inline std::vector<Puzzle> loadFile(std::string const &path) {
	std::vector<Puzzle> puzzles;
	std::ifstream file(path);
	std::string line;
	while (std::getline(file, line)) {
		if (line.rfind("New Board", 0) == 0) {
			Puzzle p;
			p.name = path + "#" + std::to_string(puzzles.size());
			if (!readGrid(file, p.grid)) break;
			puzzles.push_back(p);
		} else if (line.rfind("Solved Board", 0) == 0 && !puzzles.empty()) {
			puzzles.back().hasSolution = readGrid(file, puzzles.back().solution);
		}
	}
	return puzzles;
}


// complete, every row/col/box a permutation of 1-9, and every clue kept
inline bool validSolution(const int in[9][9], const int out[9][9]) {
	for (int i = 0; i < 9; i++) {
		int rowSeen = 0, colSeen = 0, boxSeen = 0;
		for (int j = 0; j < 9; j++) {
			int rv = out[i][j], cv = out[j][i], bv = out[3 * (i / 3) + j / 3][3 * (i % 3) + j % 3];
			if (rv < 1 || rv > 9 || cv < 1 || cv > 9 || bv < 1 || bv > 9) return false;
			rowSeen |= 1 << rv;
			colSeen |= 1 << cv;
			boxSeen |= 1 << bv;
			if (in[i][j] != 0 && in[i][j] != out[i][j]) return false;
		}
		if (rowSeen != 0x3FE || colSeen != 0x3FE || boxSeen != 0x3FE) return false;
	}
	return true;
}


inline double percentile(std::vector<double> values, double p) {
	std::sort(values.begin(), values.end());
	return values[std::min(values.size() - 1, (size_t)(p * values.size()))];
}


inline Puzzle puzzleFromString(std::string const &name, std::string const &cells) {
	Puzzle p;
	p.name = name;
	for (int i = 0; i < 81; i++) {
		p.grid[i / 9][i % 9] = cells[i] == '.' ? 0 : cells[i] - '0';
	}
	return p;
}


// hand-picked hard and edge-case boards
inline std::vector<Puzzle> hardPuzzles() {
	return {
		// from boards.h
		puzzleFromString("easyBoard",          "1.......2..8..9.377..53..8..8..73.54..64.27..97.85..1..1..87..934.6..8..8.......1"),
		puzzleFromString("hardBoard",          "4..9..3....21....453..................4..9.6...78....2.75..62....9..7..8.....5..3"),
		puzzleFromString("superHard39Board",   "987.26..3..2..5..8..1....2.81......2..5..38.1...1.8....9.54.1...568.....174.3...."),
		puzzleFromString("superHard8Board",    "3......4...................4........2..........1.......6.....9..9................"),
		puzzleFromString("arraySegfaultBoard", ".234...7..9..8.134.8.3.5..94.25......6...1.....9..........5....3........8........"),
		puzzleFromString("hardarrayBoard",     ".....35..................2.................6..7......4..4...........5...7........"),
		// well-known public benchmark puzzles
		puzzleFromString("inkala2012",         "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."),
		puzzleFromString("antiBacktrack",      "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9"),
	};
}



// solves each puzzle once, timing each individually, and counts valid / invalid answers
template <class Solver>
void timeEachPuzzle(Solver &solver, std::vector<Puzzle> const &puzzles, std::vector<double> &micros, int &solved, int &invalid) {
	int out[9][9];
	for (auto const &p : puzzles) {
		auto start = Clock::now();
		bool ok = solver.solve(p.grid, out);
		std::chrono::duration<double, std::micro> elapsed = Clock::now() - start;
		micros.push_back(elapsed.count());
		if (ok) {
			validSolution(p.grid, out) ? solved++ : invalid++;
		}
	}
}


// mean microseconds per puzzle: median over reps of timing the whole batch at once,
// which avoids the clock's resolution limit on sub-microsecond solves
template <class Solver>
double timeBatch(Solver &solver, std::vector<Puzzle> const &puzzles, int reps) {
	int out[9][9];
	std::vector<double> perPuzzle;
	for (int r = 0; r < reps; r++) {
		auto start = Clock::now();
		for (auto const &p : puzzles) solver.solve(p.grid, out);
		std::chrono::duration<double, std::micro> elapsed = Clock::now() - start;
		perPuzzle.push_back(elapsed.count() / puzzles.size());
	}
	return percentile(perPuzzle, 0.5);
}


// solves the whole set with `threads` threads, each with its own Solver, pulling puzzles from a shared counter.
// returns wall time in ms, and counts puzzles solved with a valid grid
template <class Solver>
double solveAllParallel(std::vector<Puzzle> const &puzzles, int threads, int &valid) {
	std::atomic<size_t> next{0};
	std::atomic<int> validCount{0};
	std::vector<std::thread> pool;
	auto start = Clock::now();
	for (int t = 0; t < threads; t++) {
		pool.emplace_back([&] {
			auto solver = std::make_unique<Solver>();
			int out[9][9];
			int mine = 0;
			for (size_t i = next++; i < puzzles.size(); i = next++) {
				mine += solver->solve(puzzles[i].grid, out) && validSolution(puzzles[i].grid, out);
			}
			validCount += mine;
		});
	}
	for (auto &thread : pool) thread.join();
	std::chrono::duration<double, std::milli> elapsed = Clock::now() - start;
	valid = validCount;
	return elapsed.count();
}



template <class Solver>
void runDataMode(Solver &solver, int reps) {
	std::printf("%-10s %5s %6s %7s %9s %8s %9s %11s\n", "set", "n", "solved", "invalid", "mean_us", "p50_us", "p99_us", "max_us");
	for (int clues : CLUE_COUNTS) {
		auto puzzles = loadFile(dataPath(clues));
		if (puzzles.empty()) {
			std::printf("%-10s missing or empty: %s\n", (std::to_string(clues) + " clues").c_str(), dataPath(clues).c_str());
			continue;
		}
		std::vector<double> micros;
		int solved = 0, invalid = 0;
		timeEachPuzzle(solver, puzzles, micros, solved, invalid);
		double mean = timeBatch(solver, puzzles, reps);
		std::printf("%-10s %5zu %6d %7d %9.2f %8.2f %9.2f %11.2f\n", (std::to_string(clues) + " clues").c_str(), puzzles.size(),
		            solved, invalid, mean, percentile(micros, 0.5), percentile(micros, 0.99), percentile(micros, 1.0));
		std::fflush(stdout);
	}
}


template <class Solver>
void runParallelMode(int reps, std::vector<int> const &threadCounts) {
	std::printf("%-10s %5s %8s %10s %9s %6s\n", "set", "n", "threads", "batch_ms", "speedup", "valid");
	for (int clues : CLUE_COUNTS) {
		auto puzzles = loadFile(dataPath(clues));
		if (puzzles.empty()) continue;
		double oneThread = 0;
		for (int threads : threadCounts) {
			std::vector<double> times;
			int valid = 0;
			for (int r = 0; r < reps; r++) times.push_back(solveAllParallel<Solver>(puzzles, threads, valid));
			double ms = percentile(times, 0.5);
			if (threads == 1) oneThread = ms;
			std::printf("%-10s %5zu %8d %10.2f %8.2fx %6d\n", (std::to_string(clues) + " clues").c_str(), puzzles.size(),
			            threads, ms, oneThread > 0 ? oneThread / ms : 0.0, valid);
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
		std::chrono::duration<double, std::micro> elapsed = Clock::now() - start;
		const char *result = !ok ? "unsolved" : validSolution(p.grid, out) ? "valid" : "INVALID";
		std::printf("%-20s %-8s %12.1f us\n", p.name.c_str(), result, elapsed.count());
		std::fflush(stdout);
	}
}


// usage: <bin> data [reps]                      the 8 data files, single thread (default)
//        <bin> hard [name|all]                  hand-picked boards, one line each
//        <bin> par [reps] [threads...]          whole-batch wall time across puzzles vs 1 thread
template <class Solver>
int benchMain(int argc, char **argv) {
	std::string mode = argc > 1 ? argv[1] : "data";
	auto solver = std::make_unique<Solver>();
	if (mode == "data") {
		runDataMode(*solver, argc > 2 ? std::atoi(argv[2]) : 5);
	} else if (mode == "hard") {
		runHardMode(*solver, argc > 2 ? argv[2] : "all");
	} else if (mode == "par") {
		std::vector<int> threadCounts;
		for (int a = 3; a < argc; a++) threadCounts.push_back(std::atoi(argv[a]));
		if (threadCounts.empty()) threadCounts = {(int)std::thread::hardware_concurrency()};
		if (threadCounts.front() != 1) threadCounts.insert(threadCounts.begin(), 1);  // speedup is relative to 1 thread
		runParallelMode<Solver>(argc > 2 ? std::atoi(argv[2]) : 5, threadCounts);
	} else {
		std::fprintf(stderr, "usage: %s data [reps] | hard [name|all] | par [reps] [threads...]\n", argv[0]);
		return 1;
	}
	return 0;
}
