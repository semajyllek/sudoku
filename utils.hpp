

#include <vector>
#include <fstream>
#include <sstream>

using namespace std;

extern const int BOARD_SIZE = 9;  // MUST be multiple of 3


struct ArrStruct {
	int newBoard[BOARD_SIZE][BOARD_SIZE] = {0};
};



/*


New Board: 
9,7,8,0,5,4,3,2,1
5,3,6,2,7,1,9,8,4
4,2,1,9,8,3,6,7,5
8,0,7,5,9,2,4,1,3
0,9,0,4,1,8,2,6,0
2,1,4,7,3,6,8,5,9
0,8,9,3,2,5,1,4,6
0,0,2,1,4,9,7,3,8
1,4,3,8,6,7,5,9,2

Solved Board:
9,7,8,6,5,4,3,2,1
5,3,6,2,7,1,9,8,4
4,2,1,9,8,3,6,7,5
8,6,7,5,9,2,4,1,3
3,9,5,4,1,8,2,6,7
2,1,4,7,3,6,8,5,9
7,8,9,3,2,5,1,4,6
6,5,2,1,4,9,7,3,8
1,4,3,8,6,7,5,9,2

New Board:
0,0,0,0,0,0,0,0,0
....

*/
ArrStruct* loadBoards(string filename, int boardsize, int numboards) {
	fstream file (filename, ios::in);
	string line, word;

	int boards = 0;
	ArrStruct* boardArray = new ArrStruct[numboards];
	if(file.is_open()) {

		// read in a file of a bunch of boards and their solutions
		// very brittle and inflexible code for a specific format...
		while(getline(file, line)) {
			
			// skip empty lines
			if (line.length() == 0) {
				continue;
			}

			if (line[0] == 'N') { 
				// New Board:
			  	getline(file, line);
			}

			ArrStruct arrobj; 
			stringstream str(line);
 
			// get all numeric rows 0,3,4,5,6,7,8,9, etc.
			for (int i = 0; i < boardsize; i++) {
				stringstream str(line);
				for (int j = 0; j < boardsize; j++) {
					getline(str, word, ',');
					arrobj.newBoard[i][j] = stoi(word);
				}
				getline(file, line);
			}
			

			// skip the solved board blank line and 9 rows of board
			for (int k = 0; k < boardsize + 2; k++) {
				getline(file, line);
			}
			
			boardArray[boards] = arrobj;
			boards++;
			if (boards == numboards) {
				break;
			}
	
		}
			
	} else {
		cout << "Error: File not found" << endl;
	}

	file.close();
	return boardArray;
}


ArrStruct loadBoard(string filename, int boardsize) {
	fstream file (filename, ios::in);
	string line, word;
	ArrStruct arrobj; 
	int i, j = 0;
	if(file.is_open()) {
		while(getline(file, line)) {
			if (line[0] == 'N') { // New Board:
				continue;
			}
			stringstream str(line);
 
			while (getline(str, word, ',')) {
				arrobj.newBoard[i][j] = stoi(word);
				j++;

			}
			j = 0;
			i++;
			
		}
	} else {
		cout << "Error: File not found" << endl;
	}
	file.close();
	return arrobj;
}



vector<int> initializePosVector(bool presetVal, int boardsize) {
	vector<int> vec;
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


vector<vector<int> > generateAllPositionVector() {
	vector<vector<int> > allPosVec;
	for (int i = 0; i < 9; i++) {
		for (int j = 0; j < 9; j++) {
			vector<int> posVec;
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


float computeAverage(float* counts, int ntrials) {
	float avg = 0;
	for (int i = 0; i < ntrials; i++) {
		avg += counts[i];
	}
	avg /= ntrials;
	return avg;
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


int resetMode(int mode, int defaultVal = -2) {
	if (mode > 0) {
		return defaultVal;
	}
	return mode;
}


array<int,2> getNonBackTrackIndices(int boardsize, int rowIdx, int colIdx) {
	if (colIdx < boardsize - 1) {
		// go forward one column
		colIdx++;
	} else {
		// go forward one row, to the first column
		rowIdx++;
		colIdx = 0;
	}
	array<int,2> newIndices = {rowIdx, colIdx};
	return newIndices;
}

array<int, 2> getBackIndicesHelper(int boardsize, int rowIdx, int colIdx) {
	// backtrack
	if (colIdx > 0) {
		// go back one column
		colIdx--;
	} else {
		// go back one row, to the last column
		rowIdx--;
		colIdx = boardsize - 1;
	}
	array<int,2> newIndices = {rowIdx, colIdx};
	return newIndices;
}


