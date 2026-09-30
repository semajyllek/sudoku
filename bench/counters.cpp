/*
Hardware counters for one solver on one data set: cycles, instructions, branches, branch mispredictions and L1 data
cache read misses per puzzle, counted around the solve loop only (Linux, perf_event_open). Two passes over the data,
one per group of counters, so no counter is multiplexed. Elsewhere it only times the loop; on macOS, /usr/bin/time -l
around a run with reps and a run with 0 reps gives instructions and cycles.

usage: counters <fastband|tdoku|jsolve|kudoku> <data file> <reps> [limit]
*/
#include "../fastbandsolver.hpp"
#include "jsolve/JSolve.h"
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#ifdef __linux__
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>
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


struct Counter {
	const char *name;
	uint32_t type;
	uint64_t config;
};


#ifdef __linux__
constexpr uint64_t L1D_READ_MISS = PERF_COUNT_HW_CACHE_L1D | (PERF_COUNT_HW_CACHE_OP_READ << 8)
                                 | (PERF_COUNT_HW_CACHE_RESULT_MISS << 16);

// the first counter of each group is its leader; cycles lead both so each pass has its own cycle count
const std::vector<std::vector<Counter>> GROUPS = {
	{{"cycles", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES},
	 {"instructions", PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS},
	 {"branches", PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS},
	 {"branch-misses", PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES}},
	{{"cycles", PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES},
	 {"l1d-read-misses", PERF_TYPE_HW_CACHE, L1D_READ_MISS}},
};

int openCounter(Counter const &c, int leader) {
	perf_event_attr attr;
	std::memset(&attr, 0, sizeof attr);
	attr.size = sizeof attr;
	attr.type = c.type;
	attr.config = c.config;
	attr.disabled = leader == -1;
	attr.exclude_kernel = 1;
	attr.exclude_hv = 1;
	attr.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
	return (int) syscall(SYS_perf_event_open, &attr, 0, -1, leader, 0);
}
#endif


double secondsSince(std::chrono::steady_clock::time_point start) {
	return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}


int main(int argc, char **argv) {
	if (argc != 4 && argc != 5) {
		std::fprintf(stderr, "usage: %s <fastband|tdoku|jsolve|kudoku> <data file> <reps> [limit]\n", argv[0]);
		return 1;
	}
	std::string name = argv[1];
	SolverFn solve = name == "tdoku" ? TdokuSolverDpllTriadSimd : name == "jsolve" ? JSolveAdapter
	               : name == "kudoku" ? OtherSolverKudoku : FastBandAdapter;
	int reps = std::atoi(argv[3]);
	size_t limit = argc == 5 ? std::atoi(argv[4]) : 2;
	std::vector<std::string> puzzles;
	std::ifstream file(argv[2]);
	std::string line;
	while (std::getline(file, line)) {
		if (line.size() >= 81 && line[0] != '#') puzzles.push_back(line.substr(0, 81));
	}
	char solution[82];
	size_t guesses, sink = 0;
	auto run = [&](int times) {
		for (int r = 0; r < times; r++) {
			for (auto const &p : puzzles) sink += solve(p.c_str(), limit, 0, solution, &guesses);
		}
	};
	run(reps > 0 ? 1 : 0);  // warm the caches and branch predictors
	double solves = (double) puzzles.size() * reps;
	std::printf("%s %s limit %zu, per puzzle over %d reps of %zu puzzles\n", name.c_str(), argv[2], limit, reps,
	            puzzles.size());

#ifdef __linux__
	for (auto const &group : GROUPS) {
		std::vector<int> fds;
		for (auto const &c : group) {
			int fd = openCounter(c, fds.empty() ? -1 : fds[0]);
			if (fd < 0) {
				std::printf("cannot open %s: %s\n", c.name, std::strerror(errno));
				return 1;
			}
			fds.push_back(fd);
		}
		ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
		auto start = std::chrono::steady_clock::now();
		ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
		run(reps);
		ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
		double seconds = secondsSince(start);
		// layout for PERF_FORMAT_GROUP: count, time enabled, time running, then one value per counter
		std::vector<uint64_t> values(3 + group.size());
		if (read(fds[0], values.data(), values.size() * sizeof(uint64_t)) < 0) {
			std::printf("cannot read counters: %s\n", std::strerror(errno));
			return 1;
		}
		if (values[2] < values[1]) std::printf("warning: counters multiplexed (running %.3f of enabled)\n",
		                                       (double) values[2] / values[1]);
		for (size_t i = 0; i < group.size(); i++) std::printf("%-16s %14.1f\n", group[i].name, values[3 + i] / solves);
		std::printf("%-16s %14.3e\n", "seconds", seconds / solves);
		std::printf("%-16s %14.3f\n", "GHz", values[3] / seconds / 1e9);
		for (int fd : fds) close(fd);
	}
#else
	auto start = std::chrono::steady_clock::now();
	run(reps);
	std::printf("%-16s %14.3e\n", "seconds", secondsSince(start) / std::max(solves, 1.0));
#endif
	std::printf("check %zu\n", sink);
	return 0;
}
