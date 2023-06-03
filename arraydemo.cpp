#include "arrayboard.hpp"
#include "boards.h"
#include <iostream>
#include <chrono>



void evaluate(std::string path) {
	// evaluate the performance of the solver
	int TRIALS = 1000;
	float maxt = 0;
	float mint = 100000;
	ArrStruct* boards;
	boards = loadBoards(path, 9, TRIALS);
	ArrayBoard asBoard;
	float counts[TRIALS];
	for (int i = 0; i < TRIALS; i++) {
		asBoard.initializeBoard(boards[i].newBoard);
		auto start = std::chrono::high_resolution_clock::now();
		bool solved = asBoard.multiSolve();
		if (!solved) {
			std::cout << "failed to solve board " << i << std::endl;
			asBoard.printBoard();
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
	
}




int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	//ArrayBoard asBoard;
    //asBoard.initializeBoard(6); // initialize random board with ~40 prefilled cells
	//asBoard.printBoard();
	//asBoard.initializeBoard(loadBoard("testboard.txt", 9));
    //asBoard.printBoard();

    // solve board
	// asBoard.initializeBoard(arraySegfaultBoard);
	// //int mode = 1;
	// asBoard.printBoard();
	// //bool solved = asBoard.backtrackSolve(mode);
	// bool solved = asBoard.multiSolve(); 
	// asBoard.printBoard();
	// std::cout << "Solved: " << solved << std::endl;
	evaluate(path79);

}


