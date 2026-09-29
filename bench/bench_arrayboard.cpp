// benchmark for the original ArrayBoard (arrayboard.hpp), timed from the raw puzzle including initializeBoard.
// note: its third solve attempt uses rand(), which is shared between threads in the parallel mode
#include <chrono>
#include <ctime>
#include <iostream>
#include "../arrayboard.hpp"
#include "benchlib.hpp"

struct Solver {
	ArrayBoard board;

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
	std::cout.setstate(std::ios::failbit);  // ArrayBoard prints when it gives up on a board
	return benchMain<Solver>(argc, argv);
}
