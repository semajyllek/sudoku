
#include <iostream>  
#include <stdlib.h>  
#include <cstdlib>
#include <array>
#include <unordered_map>
#include <string>
#include <vector>
#include "utils.hpp"


const int BOARD_SIZE = 9;   // MUST be multiple of 3


class Board {
	public:
		Board();

		// board contruction methods
		void initializeBoard(int fillNum);
		void initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]);

		// util methods
		void printBoard();

		// board solve methods
		bool backTrackSolve();
	
	private:
    	int board[BOARD_SIZE][BOARD_SIZE];
		std::unordered_map<std::string, std::vector<int> > tryMap;
		bool checkValid(int row, int col, int candidate);
		bool checkRow(int row, int candidate);
		bool checkColumn(int col, int candidate);
		bool checkBox(int row, int col, int candidate);
		int genBoardValue(int i, int j);
		void fillRemaining(int placed, int fillNum,  int tempBoard[BOARD_SIZE][BOARD_SIZE]);
		void fillTryMap(); 

		// solve helpers
		bool backTrackFillValue(int rowIdx, int colIdx);
		std::array<int,2> getNonBackTrackIndices(int rowIdx, int colIdx);
		std::array<int,2> getBackTrackIndices(int rowIdx, int colIdx);
		std::array<int,2> getBackIndicesHelper(int rowIdx, int colIdx);

		bool debugUtil(int rowIdx, int colIdx, int val);

};


Board::Board() {
	// initialize the board with all zeros
	memset(board, 0, sizeof(board));
}



// this overloaded version lets you (re)initialize the board with another board
void Board::initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]) {
	// fill board with newBoard values
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			board[i][j] = newBoard[i][j];
			std::string key = std::to_string(i) + ',' + std::to_string(j);
			tryMap[key] = initializeTryVector(board[i][j]);
		}
	}

}


void Board::initializeBoard(int fillNum) {
	int checkRate = 8; // check if the board is solvable after 8 placements
	int placed = 0;
	std::vector<std::vector<int> > allPosVec = generateAllPositionVector();

	// instead of sequentially filling the board, fill randomly
	while ((allPosVec.size() > 0) && (placed < fillNum)) {
		// randomly select a position from allPosVec
		int rand_num = rand() % allPosVec.size();
		std::vector<int> randPosVec = allPosVec[rand_num];

		// remove from allPosVec
		allPosVec.erase(allPosVec.begin() + rand_num);
		
		// fill the board at the random position
		int i = randPosVec[0];
		int j = randPosVec[1];
		int candidate = genBoardValue(i, j);
		board[i][j] = candidate;
		placed++;

		// fill non-zero-entry positions of the tryMap with {0}
		std::string key = std::to_string(i) + ',' + std::to_string(j);
		tryMap[key] = initializeTryVector(false);  

		if ((placed > 1) && (placed % checkRate == 0)) {
			// check if the board is solvable
			Board tempBoard;
			tempBoard.initializeBoard(board);
			if (!tempBoard.backTrackSolve()) {
				// if not solvable, reset all current placements
				memset(board, 0, sizeof(board));
				placed = 0;
				allPosVec = generateAllPositionVector();;
			} else {
				// if solvable, fill in remaining positions with random values from solved board
				fillRemaining(placed, fillNum, tempBoard.board);
				break;
			}
		}

	}

	// fill the remaining zero-entry positions tryMap with possible values
	fillTryMap();
}



void Board::fillRemaining(int placed, int fillNum, int tempBoard[BOARD_SIZE][BOARD_SIZE]) {
	int totalSize = BOARD_SIZE * BOARD_SIZE;
	int remaining = fillNum - placed;
	float placePct = (float) remaining / (float) totalSize;
	// if solvable, fill in remaining positions with random values from solved board
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			if (board[i][j] == 0) {
				float randPct = generateRandomPct();
				if (generateRandomPct() < placePct) {
					std::string key = std::to_string(i) + ',' + std::to_string(j);
					tryMap[key] = initializeTryVector(false);  
					board[i][j] = tempBoard[i][j];
					placed++;
					if (placed == fillNum) {
						return;
					}
				}
			}
		}
	}

}

	

void Board::fillTryMap() {
	// fill tryMap for non-empty cells
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			if (board[i][j] == 0) {
				std::string key = std::to_string(i) + ',' + std::to_string(j);
				tryMap[key] = initializeTryVector(true);    // {1, 2, 3, 4, 5, 6, 7, 8, 9}
			}
		}
	}
}



int Board::genBoardValue(int i, int j) {
	int candidate;
	do {
		candidate = generateRandomBoardNumber();
	}
	while (!checkValid(i, j, candidate));
	return candidate;
}


bool Board::checkValid(int row, int col, int candidate) {
	// check row
	if (!checkRow(row, candidate)) {
		return false;
	}

    // check column
	if (!checkColumn(col, candidate)) {
		return false;
	}
	
	// check 3x3 box
	if (!checkBox(row, col, candidate)) {
		return false;
	}
	return true;
	
}


bool Board::checkRow(int row, int candidate) {
	for (int i = 0; i < 9; i++) {
		if (board[row][i] == candidate) {
			return false;
		}
	}
	return true;
}


bool Board::checkColumn(int col, int candidate) {
	for (int i = 0; i < 9; i++) {
		if (board[i][col] == candidate) {
			return false;
		}
	}
	return true;
}


bool Board::checkBox(int row, int col, int candidate) {
	int row_start = row - row % 3;
	int col_start = col - col % 3;
	for (int i = row_start; i < row_start + 3; i++) {
		for (int j = col_start; j < col_start + 3; j++) {
			if (board[i][j] == candidate) {
				return false;
			}
		}
	}
	return true;
}




void Board::printBoard() {
	std::cout << "\nBoard: " << std::endl;
	for (int i = 0; i < BOARD_SIZE; i++) {
		if (i % (BOARD_SIZE / 3) == 0) {
			std::cout << "-------------------------" << std::endl;
		}
		std::cout << "| ";
		for (int j = 0; j < BOARD_SIZE; j++) {
			std::cout << board[i][j] << " ";
			if (j % (BOARD_SIZE / 3) == 2) {
				std::cout << "| ";
			}
			
		}
		std::cout << "\n";
	}
	std::cout << "-------------------------" << std::endl;
}



bool Board::debugUtil(int rowIdx, int colIdx, int val) {
	if (board[rowIdx][colIdx] == val) {
		return true;
	}
	return false;
}



/*
  solvers: 
  - backtrack: slowest but guaranteed to find solution eventually
*/


bool Board::backTrackSolve() {
	printBoard();
	int rowIdx = 0, colIdx = 0;
	while ((rowIdx < BOARD_SIZE) && (colIdx < BOARD_SIZE)) {
		bool success = backTrackFillValue(rowIdx, colIdx);
		std::array<int,2> newIndices;
		if (success) {
			// move to next cell
			newIndices = getNonBackTrackIndices(rowIdx, colIdx);
		} else {
			// move to previous cell, reset it to 0
			newIndices = getBackTrackIndices(rowIdx, colIdx);
		}
		rowIdx = newIndices[0];
		colIdx = newIndices[1];
		if ((rowIdx < 0) || (colIdx < 0)) {
			return false;
		}
	}
	return true;
}


bool Board::backTrackFillValue(int rowIdx, int colIdx) {
	/*
	  takes row and column board position, attempts to fill with valid value,
	  if successful, or position is already filled, returns true, else returns false
	*/
    if (board[rowIdx][colIdx] != 0) {
		return true;
	}

	bool success = false;
	int candidate;
	std::string tryKey = std::to_string(rowIdx) + ',' + std::to_string(colIdx);
	for (int i: tryMap[tryKey]) {
		candidate = i;
		success = checkValid(rowIdx, colIdx, candidate);
		if (success) {
			// remove candidate from tryMap
			tryMap[tryKey].erase(std::remove(tryMap[tryKey].begin(), tryMap[tryKey].end(), candidate), tryMap[tryKey].end());
			break;
		}
	}

	
	if (success) {
		// update board
		board[rowIdx][colIdx] = candidate;
	} else {
		// reset tryMap
		tryMap[tryKey] = initializeTryVector(0);
	}

	return success;	
}


std::array<int, 2> Board::getBackIndicesHelper(int rowIdx, int colIdx) {
	// backtrack
	if (colIdx > 0) {
		// go back one column
		colIdx--;
	} else {
		// go back one row, to the last column
		rowIdx--;
		colIdx = BOARD_SIZE - 1;
	}
	std::array<int,2> newIndices = {rowIdx, colIdx};
	return newIndices;
}

std::array<int,2> Board::getBackTrackIndices(int rowIdx, int colIdx) {
	std::array<int,2> newIndices;
	int new_rowIdx, new_colIdx;
	std::string key;
	newIndices = getBackIndicesHelper(rowIdx, colIdx);
    new_rowIdx = newIndices[0];
	new_colIdx = newIndices[1];
	key = std::to_string(new_rowIdx) + ',' + std::to_string(new_colIdx);
	while (tryMap[key].front() == 0) {
		newIndices = getBackIndicesHelper(new_rowIdx, new_colIdx);
    	new_rowIdx = newIndices[0];
		new_colIdx = newIndices[1];
		key = std::to_string(new_rowIdx) + ',' + std::to_string(new_colIdx);
		if ((new_rowIdx < 0) || (new_colIdx < 0)) {
			// no solution
			return newIndices;
		}
	}

	board[new_rowIdx][new_colIdx] = 0;  // reset value to 0, for search
	return newIndices;
}


std::array<int,2> Board::getNonBackTrackIndices(int rowIdx, int colIdx) {
	if (colIdx < BOARD_SIZE - 1) {
		// go forward one column
		colIdx++;
	} else {
		// go forward one row, to the first column
		rowIdx++;
		colIdx = 0;
	}
	std::array<int,2> newIndices = {rowIdx, colIdx};
	return newIndices;
}




