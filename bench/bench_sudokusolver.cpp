// benchmark for SudokuSolver (sudokusolver.hpp)
#include "../sudokusolver.hpp"
#include "benchlib.hpp"

int main(int argc, char **argv) {
	return benchMain<SudokuSolver>(argc, argv);
}
