#include "board.hpp"


int easyBoard[BOARD_SIZE][BOARD_SIZE] = {
	{1, 0, 0, 0, 0, 0, 0, 0, 2},
	{0, 0, 8, 0, 0, 9, 0, 3, 7},
	{7, 0, 0, 5, 3, 0, 0, 8, 0},
	{0, 8, 0, 0, 7, 3, 0, 5, 4},
	{0, 0, 6, 4, 0, 2, 7, 0, 0},
	{9, 7, 0, 8, 5, 0, 0, 1, 0},
	{0, 1, 0, 0, 8, 7, 0, 0, 9},
	{3, 4, 0, 6, 0, 0, 8, 0, 0},
	{8, 0, 0, 0, 0, 0, 0, 0, 1}
};

/* autogenerated board, 40 prefilled
-------------------------
| 8 0 5 | 7 0 0 | 0 9 0 | 
| 1 0 0 | 8 2 0 | 0 0 0 | 
| 9 0 0 | 0 1 0 | 0 0 2 | 
-------------------------
| 0 0 0 | 0 3 0 | 5 0 8 | 
| 2 4 0 | 0 8 0 | 0 1 7 | 
| 5 8 0 | 0 6 7 | 3 0 0 | 
-------------------------
| 0 0 0 | 6 0 0 | 0 7 1 | 
| 0 6 9 | 0 7 0 | 0 8 0 | 
| 7 1 0 | 2 5 0 | 9 0 0 | 
-------------------------

*/

int testBoard2[BOARD_SIZE][BOARD_SIZE] = {
	{8, 0, 5, 7, 0, 0, 0, 9, 0},
	{1, 0, 0, 8, 2, 0, 0, 0, 0},
	{9, 0, 0, 0, 1, 0, 0, 0, 2},
	{0, 0, 0, 0, 3, 0, 5, 0, 8},
	{2, 4, 0, 0, 8, 0, 0, 1, 7},
	{5, 8, 0, 0, 6, 7, 3, 0, 0},
	{0, 0, 0, 6, 0, 0, 0, 7, 1},
	{0, 6, 9, 0, 7, 0, 0, 8, 0},
	{7, 1, 0, 2, 5, 0, 9, 0, 0}
};


int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	Board sudoBoard;
	sudoBoard.initializeBoard(40);
	sudoBoard.printBoard();

    //solve easy board
	// sudoBoard.initializeBoard(easyBoard);
	// bool solved = sudoBoard.backTrackSolve(); 
	// sudoBoard.printBoard();
	// std::cout << "Solved: " << solved << std::endl;

}


