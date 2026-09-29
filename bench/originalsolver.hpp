/*
Adapts the original board classes (ArrayBoard, BitSetBoard) to the benchmark's Solver interface.
Timed from the raw puzzle, including initializeBoard, since that is where BitSetBoard does its propagation.
*/
#pragma once
#include <algorithm>

template <class Board>
struct OriginalSolver {
	Board board;

	bool solve(const int in[9][9], int out[9][9]) {
		int copy[9][9];  // initializeBoard takes a non-const grid
		std::copy(&in[0][0], &in[0][0] + 81, &copy[0][0]);
		board.initializeBoard(copy);
		bool ok = board.multiSolve();
		for (int cell = 0; cell < 81; cell++) {
			out[cell / 9][cell % 9] = board.getValue(cell / 9, cell % 9);
		}
		return ok;
	}
};
