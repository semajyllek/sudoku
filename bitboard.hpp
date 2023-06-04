/*
James Kelly, 2023

This implementation of a sudoku board uses a 9x9 array of TinyBitSets to represent the board.
Using TinyBitSets makes the validation checking all super faster and easy, with much less space.

We see this most when we look for naked groups, as we can compare whole possibility sets in O(1) time
because they are just integers.

The only problem is that the bit representations don't offer iterators. They must be extracted to a vector, 
or array, first. For this there is a pop() method that returns the first element of the tinybitset, and removes it.
*/

#include <iostream>  
#include <string>
#include <array>
#include <unordered_map>
#include "utils.hpp"
#include "../tinybitset/tinybitset.h"
#include <omp.h>



int MAX_TRIALS = 20000000;
int MAX_RANDOM_TRIALS = 10;

struct BitBoardCell {
	int value;
	TinyBitSet<BOARD_SIZE> possibilities;
	TinyBitSet<BOARD_SIZE> og_possibilities; // for backtracking
};


class BitSetBoard {
	public:
		BitSetBoard() {};

		// board contruction methods
		void initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]);
		void initializeSets();
		void updatePossibilities(bool init=false);
		void insertUsedSets(int row, int col);
		void removeUsedSets(int row, int col);
		TinyBitSet<BOARD_SIZE> getUnusedVals(int row, int col);
		
		// board solve methods
		bool multiSolve();
		bool multiSolveMP();
		bool randomSolve(int randomTrials=MAX_RANDOM_TRIALS, int maxTrials=10000);
		bool backTrackSolve(int mode=0, int maxTrials=MAX_TRIALS);
		bool backTrackGuess(int rowIdx, int colIdx, int mode=0);
		bool checkValid(int rowIdx, int colIdx, int candidate);
		std::array<int,2> getBackTrackIndices(int rowIdx, int colIdx); 
		int getCandidate(int rowIdx, int colIdx, int mode);

		// naked groups
		void removeNakedGroups(bool init=false);
		bool removeNakedSingles();
		void treatNakedBoxes();
		void treatNakedRowsAndColumns();
		void searchNakedBox(int boxRow, int boxCol);
		void searchNakedRowOrColumn(int fixed, bool isRow=true);
		void removeNakedBox(std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap, int boxRow, int boxCol);
		void removeNakedRowOrColumn(std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap, int fixed, bool isRow);


		// remove unique from adjacent boxes methods
		void treatAdjacentBoxes();
		void searchAdjacentBox(int boxRow, int boxCol);
		void removeUniqueFromAdjacentBoxes(TinyBitRepType<BOARD_SIZE> unique_row_bits[], TinyBitRepType<BOARD_SIZE> unique_col_bits[], int boxRow, int boxCol);

		// util methods
		void printUsedSets();
		void printBoardPossibles();
		void printBoard();
		bool debugUtil(int rowIdx, int colIdx, int val);

	
	private:
		BitBoardCell board[BOARD_SIZE][BOARD_SIZE];

		// these are all FIXED after initialization
		TinyBitSet<BOARD_SIZE> usedboxset[BOARD_SIZE/3][BOARD_SIZE/3];
		TinyBitSet<BOARD_SIZE> usedrowset[BOARD_SIZE];
		TinyBitSet<BOARD_SIZE> usedcolset[BOARD_SIZE];

};





// this overloaded version lets you (re)initialize the board with another board
void BitSetBoard::initializeBoard(int newBoard[BOARD_SIZE][BOARD_SIZE]) {

	// initialize tinybitsets
	initializeSets();

	// fill board with newBoard values
	for (int row = 0; row < BOARD_SIZE; row++) {
		for (int col = 0; col < BOARD_SIZE; col++) {

			// initialize solving board (can't update possibilities yet)
			TinyBitSet<BOARD_SIZE> newPossibilities;
			BitBoardCell newCell;
			newCell.value = newBoard[row][col];
			newCell.possibilities = newPossibilities;
			board[row][col] = newCell;

			// update used sets
			if (newBoard[row][col] != 0) {
				insertUsedSets(row, col);
			}

		}
	}

	//printBoard();

	// update possibilities and remove naked groups
	updatePossibilities(true);
	//printUsedSets();
	//printBoardPossibles();
	removeNakedGroups(true);
	//printBoardPossibles();

}


void BitSetBoard::initializeSets() {
	for (int row = 0; row < 9; row++) {
		this->usedrowset[row] = TinyBitSet<9>();
		this->usedcolset[row] = TinyBitSet<9>();
		for (int col = 0; col < 9; col+=3) {
			this->usedboxset[row/3][col/3] = TinyBitSet<9>();
		}
	}
}



void BitSetBoard::updatePossibilities(bool init) {
	// fill board with newBoard values
	for (int row = 0; row < BOARD_SIZE; row++) {
		for (int col = 0; col < BOARD_SIZE; col++) {
			if (board[row][col].value == 0) {
				board[row][col].possibilities = getUnusedVals(row, col);
			} 
			
			if (init) {
				if (board[row][col].value != 0) {
					board[row][col].possibilities.removeall();
				}
				board[row][col].og_possibilities = board[row][col].possibilities;
			}
		}
	}
}


void BitSetBoard::insertUsedSets(int row, int col) {
	usedrowset[row].insert(board[row][col].value);
	usedcolset[col].insert(board[row][col].value);
	usedboxset[row/(BOARD_SIZE / 3)][col/(BOARD_SIZE / 3)].insert(board[row][col].value);
}

void BitSetBoard::removeUsedSets(int row, int col) {
	usedrowset[row].remove(board[row][col].value);
	usedcolset[col].remove(board[row][col].value);
	usedboxset[row/(BOARD_SIZE / 3)][col/(BOARD_SIZE / 3)].remove(board[row][col].value);
}



TinyBitSet<BOARD_SIZE>  BitSetBoard::getUnusedVals(int row, int col) {
	// possibility set is a bitstring that is the negation of the intersection (bitstring &) 
	// of the row, column, and box TonyBitSets for that position
	TinyBitSet<BOARD_SIZE> newbitset = usedrowset[row].unionb(usedcolset[col]).unionb(usedboxset[row/(BOARD_SIZE/3)][col/(BOARD_SIZE/3)]);
	newbitset.invertSet();
	return newbitset;
}




/*
	Naked Pairs, Triples, etc. Method
    - the intuition is that if N cells in a row, column, or box have the same N possibilities, 
	  then those possibilities MUST be in those N cells, and can be removed from all other cells
	  in that row, column, or box

    - see: https://www.learn-sudoku.com/naked-pairs.html
*/


void BitSetBoard::removeNakedGroups(bool init) {
	bool changed = true;
	while (changed) {
		treatNakedBoxes();
	    treatNakedRowsAndColumns();
		//printBoardPossibles();
		if (!init) {
			return;
		}
		changed = removeNakedSingles();
		updatePossibilities(init);

	}
}

		
bool BitSetBoard::removeNakedSingles() {
	bool changed = false;
	for (int row = 0; row < BOARD_SIZE; row++) {
		for (int col = 0; col < BOARD_SIZE; col++) {
			if (board[row][col].possibilities.getSetSize() == 1) {
				board[row][col].value = board[row][col].possibilities.popSmallest();
				insertUsedSets(row, col);
				changed = true;
			}
		}
	}
	return changed;
}



void BitSetBoard::treatNakedBoxes() {
	for (int boxRow = 0; boxRow < (BOARD_SIZE / 3); boxRow++) {
		for (int boxCol = 0; boxCol < (BOARD_SIZE / 3); boxCol++) {
			searchNakedBox(boxRow*3, boxCol*3);	
		}
	}
}

void BitSetBoard::searchNakedBox(int boxRow, int boxCol) {
	// make a map of possibility sets to counts O(BOARD_SIZE)
	std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap;

	for (int r = boxRow; r < boxRow + 3; r++) {
		for (int c = boxCol; c < boxCol + 3; c++) {
			TinyBitRepType<BOARD_SIZE> bitint = board[r][c].possibilities.getBitInt();
			if (bitint == 0) {
				continue;
			}
			possMap[bitint]++;
		}
	}

	// iterate through map, if count == size, then remove those possibilities from the rest of the box
	removeNakedBox(possMap, boxRow, boxCol);
}


void BitSetBoard::removeNakedBox(std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap, int boxRow, int boxCol) {
	for (auto const& pair: possMap) {
		int posSize = __builtin_popcount(pair.first); // <= BOARD_SIZE
		if (pair.second == posSize) {
			
			// remove the possibilities from the rest of the box
			for (int r = boxRow; r < boxRow + 3; r++) {
				for (int c = boxCol; c < boxCol + 3; c++) {
					TinyBitRepType<BOARD_SIZE> bitint = board[r][c].possibilities.getBitInt();
					if (bitint == 0) {
						continue;
					}
					if (bitint != pair.first) {
						board[r][c].possibilities = board[r][c].possibilities.leftDifference(pair.first);
					}
				}
			}
		}
	}
}


void BitSetBoard::treatNakedRowsAndColumns() {
	for (int i = 0; i < BOARD_SIZE; i++) {
		searchNakedRowOrColumn(i);
		searchNakedRowOrColumn(i, false);
	}
}

void BitSetBoard::searchNakedRowOrColumn(int fixed, bool isRow) {
	// make a map of possibility sets to counts O(BOARD_SIZE)
	std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap;

	for (int i = 0; i < BOARD_SIZE; i++) {
		if (isRow) {
			possMap[board[fixed][i].possibilities.getBitInt()]++;
		} else {
			possMap[board[i][fixed].possibilities.getBitInt()]++;
		}
	}

	// iterate through map, if count == size, then remove those possibilities from the rest of the row
	removeNakedRowOrColumn(possMap, fixed, isRow);
}



void BitSetBoard::removeNakedRowOrColumn(std::unordered_map<TinyBitRepType<BOARD_SIZE>, int> possMap, int fixed, bool isRow) {
	for (auto const& pair: possMap) {
		int posSize = __builtin_popcount(pair.first); // <= BOARD_SIZE
		if (pair.second == posSize) {
			
			// remove the possibilities from the rest of the column
			for (int i = 0; i < BOARD_SIZE; i++) {
				if (isRow) {
					// we don't want to remove possibilities from the shared sets!
					if (board[fixed][i].possibilities.getBitInt() != pair.first) {
						board[fixed][i].possibilities = board[fixed][i].possibilities.leftDifference(pair.first);
					}

				} else {
					if (board[i][fixed].possibilities.getBitInt() != pair.first) {
						board[i][fixed].possibilities = board[i][fixed].possibilities.leftDifference(pair.first);
					}
				}
				
			}
		}
	}
}

void BitSetBoard::treatAdjacentBoxes() {
	for (int boxRow = 0; boxRow < (BOARD_SIZE / 3); boxRow++) {
		for (int boxCol = 0; boxCol < (BOARD_SIZE / 3); boxCol++) {
			searchAdjacentBox(boxRow*3, boxCol*3);	
		}
	}
}


void BitSetBoard::searchAdjacentBox(int boxRow, int boxCol) {

	// some size (8, 16, 32, 64) of unsigned fast int based on BOARD_SIZE
	TinyBitRepType<BOARD_SIZE> unique_row_bitreps[BOARD_SIZE / 3] = {0};
	TinyBitRepType<BOARD_SIZE> unique_col_bitreps[BOARD_SIZE / 3] = {0};

	// e.g. 0-3, 3-6, 6-9 for BOARD_SIZE = 9
	for (int r = boxRow; r < boxRow + (BOARD_SIZE / 3); r++) {	
		for (int c = boxCol; c < boxCol + (BOARD_SIZE / 3); c++) {
			unique_row_bitreps[r] &= (unique_row_bitreps[r] ^ board[r][c].possibilities.getBitInt());
			unique_col_bitreps[c] &= (unique_col_bitreps[c] ^ board[r][c].possibilities.getBitInt());
		}
	}


	// now go to the other boxes and remove the unique possibilities from the other boxes for the other rows and columns
	removeUniqueFromAdjacentBoxes(unique_row_bitreps, unique_col_bitreps, boxRow, boxCol);
}


void BitSetBoard::removeUniqueFromAdjacentBoxes(TinyBitRepType<BOARD_SIZE> unique_row_bitreps[], TinyBitRepType<BOARD_SIZE> unique_col_bitreps[], int boxRow, int boxCol) {
	for (int r = 0; r < BOARD_SIZE; r++) {
		if (r >= boxRow && r < boxRow + (BOARD_SIZE / 3)) {
			continue;
		}
		for (int c = 0; c < BOARD_SIZE; c++) {
			if (c >= boxCol && c < boxCol + (BOARD_SIZE / 3)) {
				continue;
			}
			board[r][c].possibilities = board[r][c].possibilities.leftDifference(unique_row_bitreps[r]);
			board[r][c].possibilities = board[r][c].possibilities.leftDifference(unique_col_bitreps[c]);
		}
	}
}






/*
    backtracking methods
  
*/


bool BitSetBoard::multiSolve() {
	return backTrackSolve(0) || backTrackSolve(-1);
}

bool BitSetBoard::multiSolveMP() {
	omp_set_num_threads(BOARD_SIZE);
	bool found = false;

	#pragma omp parallel for
	for (int i = 0; i < BOARD_SIZE; i++) {
		if (!found) {
			found = backTrackSolve(i+1);
		}
	}
	return found;
}

bool BitSetBoard::randomSolve(int randomTrials, int maxTrials) {
	for (int i = 0; i < randomTrials; i++) {
		// mode=4 sets it into random search
		if (backTrackSolve(-2, maxTrials)) {
			return true;
		}
	}
	return false;
}


bool BitSetBoard::backTrackSolve(int mode, int maxTrials) {
	int rowIdx = 0, colIdx = 0;
	int trials = 0;
	while ((rowIdx < BOARD_SIZE) && (colIdx < BOARD_SIZE)) {
		//printBoard();
		trials++;
		if (trials > maxTrials) {
			std::cout << "searched past max trials: " << MAX_TRIALS << std::endl;
			return false;
		}
	
		bool success = backTrackGuess(rowIdx, colIdx, mode);
		mode = resetMode(mode);

		std::array<int,2> newIndices;
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
			std::cout << "boundaries met, unvolvable board." << std::endl;
			return false;
		}
	}
	return true;
}




int BitSetBoard::getCandidate(int rowIdx, int colIdx, int mode) {
	if (mode == 0) {
		return board[rowIdx][colIdx].possibilities.popSmallest();
	} else if (mode == -1) {
		return board[rowIdx][colIdx].possibilities.popLargest();
	} else if (mode == -2) {
		std::vector<int> possN = board[rowIdx][colIdx].possibilities.getIntegerElements();
		if (possN.size() == 0) {
			return 0;
		}
		int randN = possN[rand() % possN.size()];
		board[rowIdx][colIdx].possibilities.remove(randN);
		return randN;
	} else if (mode > 0) {
		board[rowIdx][colIdx].possibilities.remove(mode);
		return mode;
	} else {
		std::cout << "invalid mode" << std::endl;
		return 0;
	}

}


bool BitSetBoard::backTrackGuess(int rowIdx, int colIdx, int mode) {
	/*
	  takes row and column board position, attempts to fill with valid value,
	  if successful, or position is already filled, returns true, else returns false
	*/
    if (board[rowIdx][colIdx].value != 0) {
		return true;
	}


	// find valid
	int candidate;
	do {
       candidate = getCandidate(rowIdx, colIdx, mode);
	}
	while ((candidate != 0) && !checkValid(rowIdx, colIdx, candidate));

	if (candidate == 0) {
		// no possibilities, need to backtrack, reset this cell's possibilities for next search
		board[rowIdx][colIdx].possibilities = board[rowIdx][colIdx].og_possibilities;
		return false;
	}

	board[rowIdx][colIdx].value = candidate;
	insertUsedSets(rowIdx, colIdx);
	updatePossibilities();
	//removeNakedGroups(false);

	return true;

}


std::array<int,2> BitSetBoard::getBackTrackIndices(int rowIdx, int colIdx) {
	
	std::array<int,2> newIndices = getBackIndicesHelper(BOARD_SIZE, rowIdx, colIdx);
	int new_rowIdx = newIndices[0];
	int new_colIdx = newIndices[1];
	while (board[new_rowIdx][new_colIdx].og_possibilities.getBitInt() == 0) {
		newIndices = getBackIndicesHelper(BOARD_SIZE, new_rowIdx, new_colIdx);
    	new_rowIdx = newIndices[0];
		new_colIdx = newIndices[1];
		if ((new_rowIdx < 0) || (new_colIdx < 0)) {
			// no solution
			return newIndices;
		}
	} ;

	// remove value from used sets
	removeUsedSets(new_rowIdx, new_colIdx);
	board[new_rowIdx][new_colIdx].value = 0;
	
	return newIndices;
}



bool BitSetBoard::checkValid(int rowIdx, int colIdx, int candidate) {
	if (usedrowset[rowIdx].contains(candidate)) {
		return false;
	}

	if (usedcolset[colIdx].contains(candidate)) {
		return false;
	}

	int boxRow = rowIdx / 3;
	int boxCol = colIdx / 3;
	if (usedboxset[boxRow][boxCol].contains(candidate)) {
		return false;
	}
	return true;
}




		

/*
       printing methods
*/



void BitSetBoard::printUsedSets() {
	std::cout << "\n******* USED SETS: *******" << std::endl;
	std::cout << "Row Sets:" << std::endl;
	for (int row = 0; row < BOARD_SIZE; row++) {
		std::cout << row << ": " << usedrowset[row].getBitString() << std::endl;
	}
	std::cout << "\nColumn Sets:" << std::endl;
	for (int col = 0; col < BOARD_SIZE; col++) {
		std::cout << col << ": " << usedcolset[col].getBitString() << std::endl;
	}

	std::cout << "\nBox Sets:" << std::endl;
	for (int i = 0; i < (BOARD_SIZE / 3); i++) {
		for (int j = 0; j < (BOARD_SIZE / 3); j++) {
			std::cout << "i,j: " << i << "," << j << " : " << usedboxset[i][j].getBitString() << std::endl;
		}
	}
}


void BitSetBoard::printBoardPossibles() {
	std::cout << "\nPOSSIBLES: "	<< std::endl;
	std::cout << "-------------------------------------------------------------------------------------------------" << std::endl;
	for (int row = 0; row < BOARD_SIZE; row++) {
		std::cout << "| ";
		for (int col = 0; col < BOARD_SIZE; col++) {
			std::cout << board[row][col].possibilities.getBitString() << " ";
			if ((col+1) % 3 == 0) {
				std::cout << "| ";
			}
		}
		std::cout << std::endl;
		if ((row+1) % 3 == 0) {
			std::cout << "-------------------------------------------------------------------------------------------------" << std::endl;
		}
	}
}



void BitSetBoard::printBoard() {
	std::cout << "\nBoard: " << std::endl;
	for (int i = 0; i < BOARD_SIZE; i++) {
		if (i % (BOARD_SIZE / 3) == 0) {
			std::cout << "-------------------------" << std::endl;
		}
		std::cout << "| ";
		for (int j = 0; j < BOARD_SIZE; j++) {
			std::cout << board[i][j].value << " ";
			if (j % (BOARD_SIZE / 3) == 2) {
				std::cout << "| ";
			}
			
		}
		std::cout << "\n";
	}
	std::cout << "-------------------------" << std::endl;
}



bool BitSetBoard::debugUtil(int rowIdx, int colIdx, int val) {
	if (board[rowIdx][colIdx].value == val) {
		return true;
	}
	return false;
}


