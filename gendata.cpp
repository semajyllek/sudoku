#include <iostream>
#include "arrayboard.hpp"


void genBoards(int clues, int numBoards) {

	std::string filename = "data/board" + std::to_string(clues) +  "__" + std::to_string(numBoards) + ".txt";
	for (int i = 0; i < numBoards; i++) {
		ArrayBoard asBoard;
		asBoard.initializeBoard(clues); // initialize random board with ~40 prefilled cells
		asBoard.printBoard();
		asBoard.saveBoard(filename, ios::app);
		asBoard.backTrackSolve();
		asBoard.saveBoard(filename, ios::app, "\nSolved Board:\n");
		asBoard.printBoard();
	}
	
}

int main() {
	srand((unsigned) time(NULL));  // seed random number generator
	genBoards(79, 49);	
	return 0;
}