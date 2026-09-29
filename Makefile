# build and run from the repo root. needs C++20 (tinybitset) and, for bitboard.hpp, libomp (brew install libomp)
CXX ?= clang++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra
LIBOMP ?= $(shell brew --prefix libomp 2>/dev/null)
OPENMP = -Xpreprocessor -fopenmp -I$(LIBOMP)/include -L$(LIBOMP)/lib -lomp
SANITIZE = -g -fsanitize=undefined,address -fno-sanitize-recover=undefined
BUILD = build

SOLVER = sudokusolver.hpp ../tinybitset/tinybitset.h
BENCHLIB = bench/benchlib.hpp
BENCHES = $(BUILD)/bench_sudokusolver $(BUILD)/bench_bitboard $(BUILD)/bench_arrayboard $(BUILD)/uniqueness

.PHONY: all test bench data clean

all: $(BUILD)/test_sudokusolver $(BENCHES) $(BUILD)/gendata

test: $(BUILD)/test_sudokusolver
	./$(BUILD)/test_sudokusolver

# the original solvers take several minutes on the low-clue data
bench: $(BENCHES)
	./$(BUILD)/bench_sudokusolver data
	./$(BUILD)/uniqueness

# regenerates data/ (same seed, same files)
data: $(BUILD)/gendata
	./$(BUILD)/gendata

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/test_sudokusolver: tests/test_sudokusolver.cpp $(SOLVER) $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $(SANITIZE) $< -o $@

$(BUILD)/bench_sudokusolver: bench/bench_sudokusolver.cpp $(SOLVER) $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/uniqueness: bench/uniqueness.cpp $(SOLVER) $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/gendata: gendata.cpp $(SOLVER) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD)/bench_bitboard: bench/bench_bitboard.cpp bitboard.hpp utils.hpp $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< $(OPENMP) -o $@

$(BUILD)/bench_arrayboard: bench/bench_arrayboard.cpp arrayboard.hpp utils.hpp $(BENCHLIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< -o $@

clean:
	rm -rf $(BUILD)
