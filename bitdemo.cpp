#include "bitboard.hpp"

// easy board, 33 clues, backtracking takes ~0.1 seconds
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


// hard board, 23 clues, backtracking takes ~2.8 seconds
int hardBoard[BOARD_SIZE][BOARD_SIZE] = {
	{4, 0, 0, 9, 0, 0, 3, 0, 0},
	{0, 0, 2, 1, 0, 0, 0, 0, 4},
	{5, 3, 0, 0, 0, 0, 0, 0, 0},
	{0, 0, 0, 0, 0, 0, 0, 0, 0},
	{0, 0, 4, 0, 0, 9, 0, 6, 0},
	{0, 0, 7, 8, 0, 0, 0, 0, 2},
	{0, 7, 5, 0, 0, 6, 2, 0, 0},
	{0, 0, 9, 0, 0, 7, 0, 0, 8},
	{0, 0, 0, 0, 0, 5, 0, 0, 3}
};


int main() {
	
	srand((unsigned) time(NULL));  // seed random number generator

	BitSetBoard bsBoard;

    //solve easy board
	bsBoard.initializeBoard(hardBoard);
	bsBoard.printBoard();
    bool solved = bsBoard.backTrackSolve(); 
    bsBoard.printBoard();
	std::cout << "Solved: " << solved << std::endl;

}

