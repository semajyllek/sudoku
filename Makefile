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

# make sota: comparison of sudokusolver and fastbandsolver with tdoku, jsolve and kudoku, from a tdoku checkout (see the README)
TDOKU ?= ../tdoku
SOTA_FLAGS = -O3 -march=native
SOTA_DATA = $(BUILD)/sota_data/data
SOTA_SETS = puzzles2_17_clue puzzles3_magictour_top1465 puzzles6_forum_hardest_1106 puzzles5_forum_hardest_1905_11+ puzzles0_kaggle
SOTA_OBJECTS = $(BUILD)/sota/tdoku.o $(BUILD)/sota/tdoku_util.o $(BUILD)/sota/jsolve.o $(BUILD)/sota/kudoku.o

.PHONY: all test bench data watch sota clean

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
	./$(BUILD)/sota/sota 5 $(addprefix $(SOTA_DATA)/,$(SOTA_SETS))

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
	unzip -oq $(TDOKU)/data.zip $(addprefix data/,$(SOTA_SETS)) -d $(BUILD)/sota_data
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

clean:
	rm -rf $(BUILD)
