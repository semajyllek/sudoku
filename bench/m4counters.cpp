/*
Hardware counters for one solver on Apple Silicon, through Apple's private kperf and kperfdata frameworks (the same
ones Instruments uses): cycles, instructions, branches, branch mispredictions and L1 data cache load misses per puzzle,
counted on this thread around the solve loop only. Needs root: sudo build/sota/m4counters ...
The event names come from the processor's database in /usr/share/kpep, so they are resolved for this machine.

usage: sudo m4counters <fastband|tdoku|jsolve|kudoku> <data file> <reps> [limit]
*/
#include "../fastbandsolver.hpp"
#include "jsolve/JSolve.h"
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <fstream>
#include <string>
#include <vector>

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


// the private API, as used by Instruments; signatures follow the framework's exported symbols
constexpr int KPC_MAX_COUNTERS = 32;
struct kpep_db;
struct kpep_config;
struct kpep_event;
static int (*kpc_force_all_ctrs_set)(int);
static int (*kpc_set_config)(uint32_t, uint64_t *);
static int (*kpc_set_counting)(uint32_t);
static int (*kpc_set_thread_counting)(uint32_t);
static int (*kpc_get_thread_counters)(uint32_t, uint32_t, uint64_t *);
static int (*kpep_db_create)(const char *, kpep_db **);
static int (*kpep_db_event)(kpep_db *, const char *, kpep_event **);
static int (*kpep_config_create)(kpep_db *, kpep_config **);
static int (*kpep_config_force_counters)(kpep_config *);
static int (*kpep_config_add_event)(kpep_config *, kpep_event **, uint32_t, uint32_t *);
static int (*kpep_config_kpc_classes)(kpep_config *, uint32_t *);
static int (*kpep_config_kpc_count)(kpep_config *, size_t *);
static int (*kpep_config_kpc_map)(kpep_config *, size_t *, size_t);
static int (*kpep_config_kpc)(kpep_config *, uint64_t *, size_t);

template <class F>
bool load(void *lib, F &fn, const char *name) {
	fn = (F) dlsym(lib, name);
	if (!fn) std::fprintf(stderr, "missing %s\n", name);
	return fn != nullptr;
}

bool loadFrameworks() {
	void *kperf = dlopen("/System/Library/PrivateFrameworks/kperf.framework/kperf", RTLD_LAZY);
	void *kpep = dlopen("/System/Library/PrivateFrameworks/kperfdata.framework/kperfdata", RTLD_LAZY);
	if (!kperf || !kpep) return false;
	return load(kperf, kpc_force_all_ctrs_set, "kpc_force_all_ctrs_set") && load(kperf, kpc_set_config, "kpc_set_config")
	    && load(kperf, kpc_set_counting, "kpc_set_counting")
	    && load(kperf, kpc_set_thread_counting, "kpc_set_thread_counting")
	    && load(kperf, kpc_get_thread_counters, "kpc_get_thread_counters")
	    && load(kpep, kpep_db_create, "kpep_db_create") && load(kpep, kpep_db_event, "kpep_db_event")
	    && load(kpep, kpep_config_create, "kpep_config_create")
	    && load(kpep, kpep_config_force_counters, "kpep_config_force_counters")
	    && load(kpep, kpep_config_add_event, "kpep_config_add_event")
	    && load(kpep, kpep_config_kpc_classes, "kpep_config_kpc_classes")
	    && load(kpep, kpep_config_kpc_count, "kpep_config_kpc_count")
	    && load(kpep, kpep_config_kpc_map, "kpep_config_kpc_map") && load(kpep, kpep_config_kpc, "kpep_config_kpc");
}


int main(int argc, char **argv) {
	if (argc != 4 && argc != 5) {
		std::fprintf(stderr, "usage: sudo %s <fastband|tdoku|jsolve|kudoku> <data file> <reps> [limit]\n", argv[0]);
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

	const char *names[] = {"FIXED_CYCLES", "FIXED_INSTRUCTIONS", "INST_BRANCH", "BRANCH_MISPRED_NONSPEC",
	                       "L1D_CACHE_MISS_LD_NONSPEC"};
	const char *labels[] = {"cycles", "instructions", "branches", "branch-misses", "l1d-read-misses"};
	constexpr int EVENTS = 5;
	kpep_db *db = nullptr;
	kpep_config *config = nullptr;
	if (!loadFrameworks() || kpep_db_create(nullptr, &db) || kpep_config_create(db, &config)
	    || kpep_config_force_counters(config)) {
		std::fprintf(stderr, "cannot load kperf or this processor's event database\n");
		return 1;
	}
	for (auto event : names) {
		kpep_event *e = nullptr;
		if (kpep_db_event(db, event, &e) || kpep_config_add_event(config, &e, 1, nullptr)) {
			std::fprintf(stderr, "cannot add event %s\n", event);
			return 1;
		}
	}
	uint32_t classes = 0;
	size_t count = 0, map[KPC_MAX_COUNTERS] = {};
	uint64_t regs[KPC_MAX_COUNTERS] = {};
	if (kpep_config_kpc_classes(config, &classes) || kpep_config_kpc_count(config, &count)
	    || kpep_config_kpc_map(config, map, sizeof map) || kpep_config_kpc(config, regs, sizeof regs)) {
		std::fprintf(stderr, "cannot build the counter configuration\n");
		return 1;
	}
	if (kpc_force_all_ctrs_set(1) || kpc_set_config(classes, regs) || kpc_set_counting(classes)
	    || kpc_set_thread_counting(classes)) {
		std::fprintf(stderr, "cannot take the counters: run with sudo\n");
		return 1;
	}

	char solution[82];
	size_t guesses, sink = 0;
	auto run = [&](int times) {
		for (int r = 0; r < times; r++) {
			for (auto const &p : puzzles) sink += solve(p.c_str(), limit, 0, solution, &guesses);
		}
	};
	run(1);  // warm the caches and branch predictors
	uint64_t before[KPC_MAX_COUNTERS] = {}, after[KPC_MAX_COUNTERS] = {};
	auto start = std::chrono::steady_clock::now();
	kpc_get_thread_counters(0, KPC_MAX_COUNTERS, before);
	run(reps);
	kpc_get_thread_counters(0, KPC_MAX_COUNTERS, after);
	double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
	kpc_set_counting(0);
	kpc_set_thread_counting(0);
	kpc_force_all_ctrs_set(0);

	double solves = (double) puzzles.size() * reps;
	std::printf("%s %s limit %zu, per puzzle over %d reps of %zu puzzles\n", name.c_str(), argv[2], limit, reps,
	            puzzles.size());
	for (int i = 0; i < EVENTS; i++) std::printf("%-16s %14.1f\n", labels[i], (after[map[i]] - before[map[i]]) / solves);
	std::printf("%-16s %14.3e\n", "seconds", seconds / solves);
	std::printf("%-16s %14.3f\n", "GHz", (after[map[0]] - before[map[0]]) / seconds / 1e9);
	std::printf("check %zu\n", sink);
	return 0;
}
