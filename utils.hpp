

#include <vector>


std::vector<int> initializePosVector(bool presetVal, int boardsize) {
	std::vector<int> vec;
	if (presetVal) {
		// preset value, 0 is marker for preset
		vec.push_back(0);
		return vec;
	}
	for (int i = 1; i < (boardsize + 1); i++) {
		vec.push_back(i);
	}
	return vec;
}


std::vector<std::vector<int> > generateAllPositionVector() {
	std::vector<std::vector<int> > allPosVec;
	for (int i = 0; i < 9; i++) {
		for (int j = 0; j < 9; j++) {
			std::vector<int> posVec;
			posVec.push_back(i);
			posVec.push_back(j);
			allPosVec.push_back(posVec);
		}
	}
	return allPosVec;
}


int generateRandomBoardNumber() {
	int rand_num = 1 + rand() % 9;  // random number between 1 and 9
	return rand_num;
}


float generateRandomPct() {
	float rand_pct = (float) rand() / RAND_MAX;  // random number between 0 and 1
	return rand_pct;
}


// pass 1-dim array, checks if any zeros
bool anyZeros(int* arr, int arrLen) {
	for (int i = 0; i < arrLen; i++) {
		if (arr[i] == 0) {
			return true;
		}
	}
	return false;
}

std::array<int,2> getNonBackTrackIndices(int boardsize, int rowIdx, int colIdx) {
	if (colIdx < boardsize - 1) {
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

std::array<int, 2> getBackIndicesHelper(int boardsize, int rowIdx, int colIdx) {
	// backtrack
	if (colIdx > 0) {
		// go back one column
		colIdx--;
	} else {
		// go back one row, to the last column
		rowIdx--;
		colIdx = boardsize - 1;
	}
	std::array<int,2> newIndices = {rowIdx, colIdx};
	return newIndices;
}


