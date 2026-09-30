# build and run from the repo root. needs C++20 (tinybitset) and, for bitboard.hpp, libomp (brew install libomp)
CXX ?= clang++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra
LIBOMP ?= $(shell brew --prefix libomp 2>/dev/null)
OPENMP = -Xpreprocessor -fopenmp -I$(LIBOMP)/include -L$(LIBOMP)/lib -lomp
SANITIZE = -g -fsanitize=undefined,address -fno-sanitize-recover=undefined
BUILD = build

SOLVER = sudokusolver.hpp ../tinybitset/tinybitset.h
PUZZLES = puzzles.hpp
BENCHLIB = bench/benchlib.hpp $(PUZZLES)
ORIGINAL = bench/originalsolver.hpp utils.hpp $(BENCHLIB)
BENCHES = $(BUILD)/bench_sudokusolver $(BUILD)/bench_bitboard $(BUILD)/bench_arrayboard $(BUILD)/uniqueness

# solution limit for make sota, parallel and throughput: 2 checks uniqueness (tdoku's standard), 1 finds one solution
LIMIT ?= 2
# runs per data set for make sota (the median is reported)
REPS ?= 5

# make sota: comparison of sudokusolver and fastbandsolver with tdoku, jsolve and kudoku, from a tdoku checkout (see the README)
TDOKU ?= ../tdoku
SOTA_FLAGS = -O3 -march=native
SOTA_DATA = $(BUILD)/sota_data/data
SOTA_SETS = puzzles2_17_clue puzzles3_magictour_top1465 puzzles6_forum_hardest_1106 puzzles5_forum_hardest_1905_11+ puzzles0_kaggle
SOTA_OBJECTS = $(BUILD)/sota/tdoku.o $(BUILD)/sota/tdoku_util.o $(BUILD)/sota/jsolve.o $(BUILD)/sota/kudoku.o

.PHONY: all test bench data watch sota verify parallel throughput paper figs clean

all: $(BUILD)/test_sudokusolver $(BENCHES) $(BUILD)/gendata $(BUILD)/watch

test: $(BUILD)/test_sudokusolver
	./$(BUILD)/test_sudokusolver

# the original solvers take several minutes on the low-clue data
bench: $(BENCHES)
	./$(BUILD)/bench_sudokusolver data
	./$(BUILD)/uniqueness

# replays the solver on a puzzle in the terminal. more options: see watch.cpp
watch: $(BUILD)/watch
	./$(BUILD)/watch

# regenerates data/ (same seed, same files)
data: $(BUILD)/gendata
	./$(BUILD)/gendata

# takes a few minutes
sota: $(BUILD)/sota/sota $(BUILD)/sota_data/unpacked
	LIMIT=$(LIMIT) ./$(BUILD)/sota/sota $(REPS) $(addprefix $(SOTA_DATA)/,$(SOTA_SETS))

# fastbandsolver against tdoku on all seven of tdoku's data sets: counts at limits 1-3 and every solution (a few minutes)
VERIFY_SETS = $(SOTA_SETS) puzzles7_serg_benchmark puzzles8_gen_puzzles
verify: $(BUILD)/sota/verify $(BUILD)/sota_data/unpacked
	./$(BUILD)/sota/verify $(addprefix $(SOTA_DATA)/,$(VERIFY_SETS))

# one puzzle at a time on several threads: parallelbandsolver against fastbandsolver and tdoku
parallel: $(BUILD)/sota/parallel $(BUILD)/sota_data/unpacked
	LIMIT=$(LIMIT) ./$(BUILD)/sota/parallel 5 2,3,4,6 $(addprefix $(SOTA_DATA)/,$(SOTA_SETS))

# many puzzles on many cores, one process per core: fastbandsolver, tdoku, jsolve, kudoku. takes about 30 minutes
throughput: $(BUILD)/sota/throughput $(BUILD)/sota_data/unpacked
	LIMIT=$(LIMIT) python3 bench/throughput.py ./$(BUILD)/sota/throughput 1,2,4,8,10,12,14 $(SOTA_DATA)/puzzles6_forum_hardest_1106:40 \
		$(SOTA_DATA)/puzzles5_forum_hardest_1905_11+:1 $(SOTA_DATA)/puzzles3_magictour_top1465:60 \
		$(SOTA_DATA)/puzzles2_17_clue:5 $(SOTA_DATA)/puzzles0_kaggle:6

# regenerates the paper's algorithm figures from a real run of fastbandsolver (needs the data from make sota)
figs: $(BUILD)/sota_data/unpacked fastbandsolver.hpp paper/figs/dump.cpp paper/figs/make_figs.py
	$(CXX) -std=c++20 -O1 paper/figs/dump.cpp -o $(BUILD)/dump
	./$(BUILD)/dump $(SOTA_DATA)/puzzles3_magictour_top1465 95 > $(BUILD)/state.json
	python3 paper/figs/make_figs.py $(BUILD)/state.json paper/figs

# the paper, in build/paper/paper.pdf. needs a TeX installation with latexmk
paper: | $(BUILD)
	cd paper && latexmk -pdf -interaction=nonstopmode -output-directory=../$(BUILD)/paper paper.tex

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/test_sudokusolver: tests/test_sudokusolver.cpp $(SOLVER) $(PUZZLES) | $(BUILD)
	$(CXX) $(CXXFLAGS) $(SANITIZE) $< -o $@

$(BUILD)/bench_sudokusolver: bench/bench_sudokusolver.cpp $(SOLVER) $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/uniqueness: bench/uniqueness.cpp $(SOLVER) $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/watch: watch.cpp $(SOLVER) $(PUZZLES) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/gendata: gendata.cpp $(SOLVER) $(PUZZLES) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/bench_bitboard: bench/bench_bitboard.cpp bitboard.hpp $(ORIGINAL) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< $(OPENMP) -o $@

$(BUILD)/bench_arrayboard: bench/bench_arrayboard.cpp arrayboard.hpp $(ORIGINAL) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(TDOKU)/src/solver_dpll_triad_simd.cc:
	@echo "make sota needs tdoku at $(TDOKU). on ARM, until tdoku merges ARM support:"
	@echo "  git clone -b arm-neon https://github.com/semajyllek/tdoku $(TDOKU)"
	@exit 1

$(BUILD)/sota_data/unpacked: $(TDOKU)/src/solver_dpll_triad_simd.cc
	mkdir -p $(BUILD)/sota_data
	unzip -oq $(TDOKU)/data.zip $(addprefix data/,$(SOTA_SETS) puzzles7_serg_benchmark puzzles8_gen_puzzles) -d $(BUILD)/sota_data
	touch $@

$(BUILD)/sota/tdoku.o: $(TDOKU)/src/solver_dpll_triad_simd.cc
	mkdir -p $(BUILD)/sota
	$(CXX) -std=c++17 $(SOTA_FLAGS) -DNDEBUG -w -I$(TDOKU)/include -c $< -o $@

$(BUILD)/sota/tdoku_util.o: $(TDOKU)/src/solver_dpll_triad_simd.cc
	mkdir -p $(BUILD)/sota
	$(CXX) -std=c++17 $(SOTA_FLAGS) -w -c $(TDOKU)/src/util.cc -o $@

$(BUILD)/sota/jsolve.o: $(TDOKU)/src/solver_dpll_triad_simd.cc
	mkdir -p $(BUILD)/sota
	$(CC) $(SOTA_FLAGS) -w -c $(TDOKU)/other/jsolve/JSolve.c -o $@

$(BUILD)/sota/kudoku.o: $(TDOKU)/src/solver_dpll_triad_simd.cc
	mkdir -p $(BUILD)/sota
	$(CC) $(SOTA_FLAGS) -w -c $(TDOKU)/other/kudoku/kudoku.c -o $@

$(BUILD)/sota/sota: bench/sota.cpp $(SOLVER) fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) -I$(TDOKU)/other $< $(SOTA_OBJECTS) -o $@

$(BUILD)/sota/parallel: bench/parallel.cpp parallelbandsolver.hpp fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) $< $(BUILD)/sota/tdoku.o $(BUILD)/sota/tdoku_util.o -o $@

$(BUILD)/sota/verify: bench/verify.cpp fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) $< $(BUILD)/sota/tdoku.o $(BUILD)/sota/tdoku_util.o -o $@

# hardware counters for one solver (Linux perf_event_open; elsewhere it only times the loop)
$(BUILD)/sota/counters: bench/counters.cpp fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) -I$(TDOKU)/other $< $(SOTA_OBJECTS) -o $@

# the same on Apple Silicon through kperf (run with sudo)
$(BUILD)/sota/m4counters: bench/m4counters.cpp fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) -I$(TDOKU)/other $< $(SOTA_OBJECTS) -o $@

$(BUILD)/sota/throughput: bench/throughput.cpp fastbandsolver.hpp $(SOTA_OBJECTS)
	$(CXX) $(CXXFLAGS) $(SOTA_FLAGS) -I$(TDOKU)/other $< $(SOTA_OBJECTS) -o $@

clean:
	rm -rf $(BUILD)
