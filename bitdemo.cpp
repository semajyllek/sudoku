#include "bitboard.hpp"
#include "boards.h"





void evaluate(std::string path) {
	// evaluate the performance of the solver
	int TRIALS = 1000;
	float maxt = 0;
	float mint = 100000;
	ArrStruct* boards;
	boards = loadBoards(path, 9, TRIALS);
	BitSetBoard bsBoard;
	float counts[TRIALS];
	int solvedCount = 0;
	for (int i = 0; i < TRIALS; i++) {
		bsBoard.initializeBoard(boards[i].newBoard);
		auto start = std::chrono::high_resolution_clock::now();
		bool solved = bsBoard.multiSolve();
		if (solved) {
			solvedCount++;
		} else {
			std::cout << "failed to solve board " << i << std::endl;
			bsBoard.printBoard();
		}

		auto end = std::chrono::high_resolution_clock::now();
		std::chrono::duration<double> elapsed = end - start;
		if (elapsed.count() > maxt) {
			maxt = elapsed.count();
		}
		if (elapsed.count() < mint) {
			mint = elapsed.count();
		}
		counts[i] = elapsed.count();
	}

	float avg = computeAverage(counts, TRIALS);
	std::cout << path << std::endl;
	std::cout << "Average time: " << avg << "ms" << std::endl;
	std::cout << "Max time: " << maxt << "ms" << std::endl;
	std::cout << "Min time: " << mint << "ms" << std::endl;
	std::cout << "Solved: " << solvedCount << ", out of " <<  TRIALS  << " boards." << std::endl;
}



int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	// BitSetBoard bsBoard;

    // //solve easy board
	// bsBoard.initializeBoard(hardarrayBoard);
	// bsBoard.printBoard();
    // bool solved = bsBoard.multiSolve(); 
	// // bool solved = bsBoard.randomSolve();
    // bsBoard.printBoard();
	// std::cout << "Solved: " << solved << std::endl;
	evaluate(path79);

}


