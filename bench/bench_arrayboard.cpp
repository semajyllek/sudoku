// benchmark for the original ArrayBoard (arrayboard.hpp).
// note: its third solve attempt uses rand(), which is shared between threads in the parallel mode
#include <chrono>
#include <ctime>
#include <iostream>
#include "../arrayboard.hpp"
#include "originalsolver.hpp"
#include "benchlib.hpp"

int main(int argc, char **argv) {
	std::cout.setstate(std::ios::failbit);  // ArrayBoard prints when it gives up on a board
	return benchMain<OriginalSolver<ArrayBoard>>(argc, argv);
}
