// benchmark for the original BitSetBoard (bitboard.hpp)
#include <chrono>
#include <ctime>
#include <iostream>
#include "../bitboard.hpp"
#include "originalsolver.hpp"
#include "benchlib.hpp"

int main(int argc, char **argv) {
	std::cout.setstate(std::ios::failbit);  // BitSetBoard prints when it gives up on a board
	return benchMain<OriginalSolver<BitSetBoard>>(argc, argv);
}
