#include "bitboard.hpp"
#include "boards.h"


int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	BitSetBoard bsBoard;

    //solve easy board
	bsBoard.initializeBoard(superHardBoard);
	bsBoard.printBoard();
    bool solved = bsBoard.backTrackSolve(); 
    bsBoard.printBoard();
	std::cout << "Solved: " << solved << std::endl;

}


