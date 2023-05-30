#include "arrayboard.hpp"
#include "boards.h"






int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	ArrayBoard asBoard;
    //asBoard.initializeBoard(6); // initialize random board with ~40 prefilled cells
	//asBoard.printBoard();
	//asBoard.initializeBoard(loadBoard("testboard.txt", 9));
    //asBoard.printBoard();

    //solve board
	asBoard.initializeBoard(superHard8Board);
	bool solved = asBoard.backTrackSolve(); 
	asBoard.printBoard();
	std::cout << "Solved: " << solved << std::endl;

}


