// benchmark for the original BitSetBoard (bitboard.hpp), timed from the raw puzzle including initializeBoard
#include <chrono>
#include <ctime>
#include <iostream>
#include "../bitboard.hpp"
#include "benchlib.hpp"

struct Solver {
	BitSetBoard board;

	bool solve(const int in[9][9], int out[9][9]) {
		int copy[9][9];
		std::copy(&in[0][0], &in[0][0] + 81, &copy[0][0]);
		board.initializeBoard(copy);
		bool ok = board.multiSolve();
		for (int cell = 0; cell < 81; cell++) {
			out[cell / 9][cell % 9] = board.getValue(cell / 9, cell % 9);
		}
		return ok;
	}
};

int main(int argc, char **argv) {
	std::cout.setstate(std::ios::failbit);  // BitSetBoard prints when it gives up on a board
	return benchMain<Solver>(argc, argv);
}
