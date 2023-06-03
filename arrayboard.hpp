
#include <iostream>  
#include <fstream>
#include <sstream>
#include <stdlib.h>  
#include <cstdlib>
#include <array>
#include <string>
#include <vector>
#include "utils.hpp"
#include "../tinybitset/tinybitset.h"

using namespace std;




struct ArrayBoardCell {
	int value;
	vector<int> possibilities;
};

const int MAX_TRIES = 20000000;

class ArrayBoard{
	public:
		ArrayBoard();
		~ArrayBoard() {};

		//solve public method 
		bool multiSolve(int maxTries=0);
		bool backTrackSolve(int mode=0, int maxTries=MAX_TRIES);

		// board contruction helpers
		void initializeBoard();
		void initializeBoard(int fillNum);
		void initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]);
		void initializeBoard(ArrayBoardCell newBoard[BOARD_SIZE][BOARD_SIZE]);
	

		// debug helpers
		void printBoard();
		bool debugUtil(int rowIdx, int colIdx, int val);
		void saveBoard(string filename, unsigned int mode=ios::out, string header="\nNew Board: \n");

	
	private:
    	ArrayBoardCell board[BOARD_SIZE][BOARD_SIZE];

		// initializer helpers
		int genBoardValue(int i, int j);
		void fillRemaining(int placed, int fillNum,  ArrayBoardCell tempBoard[BOARD_SIZE][BOARD_SIZE]);
		void updatePossibilities();

		// solve helpers
		int getCandidate(int rowIdx, int colIdx, int mode);
		bool backTrackGuess(int rowIdx, int colIdx, int mode=0);
		array<int,2> getBackTrackIndices(int rowIdx, int colIdx);
		
		// checkers
		bool checkValid(int row, int col, int candidate);
		bool checkRow(int row, int candidate);
		bool checkColumn(int col, int candidate);
		bool checkBox(int row, int col, int candidate);	


};

/*

	constructor, initializers

*/


ArrayBoard::ArrayBoard() {
	// initialize the board with all zeros
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			board[i][j].value = 0;
			board[i][j].possibilities = initializePosVector(board[i][j].value, BOARD_SIZE);
		}
	}
}

void ArrayBoard::initializeBoard() {
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			board[i][j].value = 0;
			board[i][j].possibilities = initializePosVector(board[i][j].value, BOARD_SIZE);
		}
	}
}


// this overloaded version lets you (re)initialize the board with another board
void ArrayBoard::initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]) {
	// fill board with newBoard values
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			board[i][j].value = newBoard[i][j];
			board[i][j].possibilities = initializePosVector(board[i][j].value, BOARD_SIZE);
		}
	}

}



// this overloaded version lets you (re)initialize the board with another board
void ArrayBoard::initializeBoard(ArrayBoardCell newBoard[BOARD_SIZE][BOARD_SIZE]) {
	// fill board with newBoard values
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			board[i][j].value = newBoard[i][j].value;
			board[i][j].possibilities = initializePosVector(board[i][j].value, BOARD_SIZE);
		}
	}

}


void ArrayBoard::initializeBoard(int fillNum) {
	int checkRate = min(fillNum, 8); // check if the board is solvable after 8 placements
	int placed = 0;
	vector<vector<int> > allPosVec = generateAllPositionVector();
	int tries = 0;

	// instead of sequentially filling the board, fill randomly
	while ((allPosVec.size() > 0) && (placed < fillNum) && (tries < MAX_TRIES)) {
		tries++;

		// randomly select a position from allPosVec
		int rand_num = rand() % allPosVec.size();
		vector<int> randPosVec = allPosVec[rand_num];

		// remove from allPosVec
		allPosVec.erase(allPosVec.begin() + rand_num);
		
		// fill the board at the random position
		int i = randPosVec[0];
		int j = randPosVec[1];
		int candidate = genBoardValue(i, j);
		this->board[i][j].value = candidate;
		placed++;

		board[i][j].possibilities = initializePosVector(true, BOARD_SIZE);  
		if ((placed > 1) && (placed % checkRate == 0)) {
			// check if the board is solvable
			ArrayBoard tempBoard;
			tempBoard.initializeBoard(board);
			if (!tempBoard.backTrackSolve()) {
				// if not solvable, reset all current placements
				initializeBoard();
				placed = 0;
				allPosVec = generateAllPositionVector();
			} else {
				//tempBoard.printBoard();
				// if solvable, fill in remaining positions with random values from solved board
				fillRemaining(placed, fillNum, tempBoard.board);
				break;
			}
		}

	}

	// fill the remaining zero-entry positions tryMap with possible values
	updatePossibilities();
}


int ArrayBoard::genBoardValue(int i, int j) {
	int candidate;
	do {
		candidate = generateRandomBoardNumber();
	}
	while (!checkValid(i, j, candidate));
	return candidate;
}



void ArrayBoard::fillRemaining(int placed, int fillNum, ArrayBoardCell tempBoard[BOARD_SIZE][BOARD_SIZE]) {
	int totalSize = BOARD_SIZE * BOARD_SIZE;
	int remaining = fillNum - placed;
	float placePct = (float) remaining / (float) totalSize;
	// if solvable, fill in remaining positions with random values from solved board
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			if (board[i][j].value == 0) {
				float randPct = generateRandomPct();
				if (generateRandomPct() < placePct) {
					this->board[i][j].possibilities = initializePosVector(true, BOARD_SIZE);  
					this->board[i][j].value = tempBoard[i][j].value;
					placed++;
					if (placed == fillNum) {
						return;
					}
				}
			}
		}
	}

}

	

void ArrayBoard::updatePossibilities() {
	// fill tryMap for non-empty cells
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE; j++) {
			if (board[i][j].value == 0) {
				board[i][j].possibilities = initializePosVector(false, BOARD_SIZE);    // {1, 2, 3, 4, 5, 6, 7, 8, 9}
			}
		}
	}
}



/*

	solvers

*/


bool  ArrayBoard::multiSolve(int maxTries) {
	return backTrackSolve(0, maxTries) || backTrackSolve(-1, maxTries) || backTrackSolve(2, maxTries);
}


bool ArrayBoard::backTrackSolve(int mode, int maxTries) {
	int rowIdx = 0, colIdx = 0;
	int tries = 0;
	while ((rowIdx < BOARD_SIZE) && (colIdx < BOARD_SIZE) && (tries < MAX_TRIES)) {
		tries++;
		bool success = backTrackGuess(rowIdx, colIdx, mode);
		array<int,2> newIndices;
		if (success) {
			// move to next cell
			newIndices = getNonBackTrackIndices(BOARD_SIZE, rowIdx, colIdx);
		} else {
			// move to previous guessable cell, reset possibilities
			newIndices = getBackTrackIndices(rowIdx, colIdx);
		}
		rowIdx = newIndices[0];
		colIdx = newIndices[1];
		if ((rowIdx < 0) || (colIdx < 0)) {
			return false;
		}
	}

	if ((rowIdx == BOARD_SIZE) || (colIdx == BOARD_SIZE)) {
		return true;
	}
	if (tries > maxTries) {
		std:cout << "max tries exceeded, last cell: " << board[BOARD_SIZE-1][BOARD_SIZE - 1].value << std::endl;
		return false;
	}
	return true;
}



bool ArrayBoard::backTrackGuess(int rowIdx, int colIdx, int mode) {
	/*
	  takes row and column board position, attempts to fill with valid value,
	  if successful, or position is already filled, returns true, else returns false
	*/

    if (board[rowIdx][colIdx].value != 0) {
		return true;
	}

	bool success = false;
	int candidate;
	while (board[rowIdx][colIdx].possibilities.size() != 0) {
		candidate = getCandidate(rowIdx, colIdx, mode);
		success = checkValid(rowIdx, colIdx, candidate);
		if (success) {
			// remove candidate from possibilities
			break;
		} 
	}
		
	if (success) {
		// update board	
		board[rowIdx][colIdx].value = candidate;
	} else {
		// reset possibilities
		board[rowIdx][colIdx].possibilities = initializePosVector(false, BOARD_SIZE);
	}

	return success;	
}



int ArrayBoard::getCandidate(int rowIdx, int colIdx, int mode) {
	int candidate = 0;
 	if (mode == 0){
		// get smallest candidate
		candidate =  board[rowIdx][colIdx].possibilities.front();
		board[rowIdx][colIdx].possibilities.erase(board[rowIdx][colIdx].possibilities.begin());
	} else if (mode == -1) {
		// get largest candidate
		candidate =  board[rowIdx][colIdx].possibilities.back();
		board[rowIdx][colIdx].possibilities.pop_back();
	} else {
		// get random candidate
		int rand_num = rand() % board[rowIdx][colIdx].possibilities.size();
		candidate = board[rowIdx][colIdx].possibilities[rand_num];
		board[rowIdx][colIdx].possibilities.erase(board[rowIdx][colIdx].possibilities.begin() + rand_num);
	}
	return candidate;
}



array<int,2> ArrayBoard::getBackTrackIndices(int rowIdx, int colIdx) {
	array<int,2> newIndices;
	int new_rowIdx, new_colIdx;
	newIndices = getBackIndicesHelper(BOARD_SIZE, rowIdx, colIdx);
    new_rowIdx = newIndices[0];
	new_colIdx = newIndices[1];
	while (board[new_rowIdx][new_colIdx].possibilities.front() == 0) {
		newIndices = getBackIndicesHelper(BOARD_SIZE, new_rowIdx, new_colIdx);
    	new_rowIdx = newIndices[0];
		new_colIdx = newIndices[1];
		if ((new_rowIdx < 0) || (new_colIdx < 0)) {
			// no solution
			return newIndices;
		}
	}

	board[new_rowIdx][new_colIdx].value = 0;  // reset value to 0, for search
	return newIndices;
}


/*

	validity checks

*/

bool ArrayBoard::checkValid(int row, int col, int candidate) {
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


bool ArrayBoard::checkRow(int row, int candidate) {
	for (int i = 0; i < 9; i++) {
		if (board[row][i].value == candidate) {
			return false;
		}
	}
	return true;
}


bool ArrayBoard::checkColumn(int col, int candidate) {
	for (int i = 0; i < 9; i++) {
		if (board[i][col].value == candidate) {
			return false;
		}
	}
	return true;
}


bool ArrayBoard::checkBox(int row, int col, int candidate) {
	int row_start = row - row % 3;
	int col_start = col - col % 3;
	for (int i = row_start; i < row_start + 3; i++) {
		for (int j = col_start; j < col_start + 3; j++) {
			if (board[i][j].value == candidate) {
				return false;
			}
		}
	}
	return true;
}



bool ArrayBoard::debugUtil(int rowIdx, int colIdx, int val) {
	if (board[rowIdx][colIdx].value == val) {
		return true;
	}
	return false;
}



/*
	debugging
*/
void ArrayBoard::printBoard() {
	cout << "\nBoard: " << endl;
	for (int i = 0; i < BOARD_SIZE; i++) {
		if (i % (BOARD_SIZE / 3) == 0) {
			cout << "-------------------------" << endl;
		}
		cout << "| ";
		for (int j = 0; j < BOARD_SIZE; j++) {
			cout << board[i][j].value << " ";
			if (j % (BOARD_SIZE / 3) == 2) {
				cout << "| ";
			}
			
		}
		cout << "\n";
	}
	cout << "-------------------------" << endl;
}




void ArrayBoard::saveBoard(string filename, unsigned int mode, string header) {
	ofstream file;
	file.open(filename, mode);
	file << header;
	for (int i = 0; i < BOARD_SIZE; i++) {
		for (int j = 0; j < BOARD_SIZE - 1; j++) {
			file << board[i][j].value << ",";
		}
		file << board[i][BOARD_SIZE - 1].value << "\n";
	}

	file.close();
}




