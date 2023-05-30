

// easy board, 33 clues, backtracking takes ~0.1 seconds
int easyBoard[9][9] = {
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
int hardBoard[9][9] = {
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


/*
superHard?

9 clue superhard
------------------------
| 0 0 6 | 0 0 0 | 0 0 0 | 
| 3 2 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 3 0 0 | 0 0 0 | 
| 0 0 0 | 7 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 1 | 5 0 0 | 
| 0 0 0 | 0 0 5 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 3 | 
-------------------------
| 0 0 0 | 0 5 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 5 0 | 6 0 0 | 0 0 0 | 
-------------------------
| 0 0 2 | 0 0 1 | 0 0 0 | 
| 0 0 0 | 0 0 4 | 0 0 0 | 
| 0 0 6 | 0 0 0 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 9 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 9 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 2 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 1 | 0 0 0 | 
| 7 0 0 | 0 0 6 | 0 0 0 | 
| 0 0 0 | 5 0 0 | 9 0 0 | 
-------------------------

8 clues
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 9 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 2 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 1 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 5 | 3 1 0 | 
| 4 7 0 | 0 0 0 | 0 0 0 | 
-------------------------


-------------------------
| 3 5 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 9 0 0 | 0 3 0 | 
| 0 0 0 | 0 7 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 9 | 
| 0 0 0 | 0 0 1 | 0 0 0 | 
| 0 0 0 | 0 0 5 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 9 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 7 0 0 | 
| 0 0 0 | 0 0 7 | 0 0 0 | 
| 0 2 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 9 7 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 6 0 | 0 4 0 | 0 0 0 | 
-------------------------


-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 6 | 0 0 0 | 
| 8 0 0 | 0 0 5 | 0 0 0 | 
-------------------------
| 0 1 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 7 | 0 0 0 | 
| 0 0 0 | 0 0 2 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 2 | 
| 0 0 0 | 1 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 1 0 | 0 0 9 | 
| 0 0 0 | 0 0 0 | 0 0 5 | 
-------------------------
| 0 6 0 | 9 0 0 | 0 0 3 | 
| 0 0 0 | 4 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 1 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 3 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 2 8 | 
| 0 0 0 | 3 9 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 9 0 0 | 0 0 0 | 
| 0 8 0 | 0 0 7 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 6 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 6 0 0 | 
-------------------------
| 5 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 8 0 | 
| 0 0 0 | 8 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 3 0 | 0 0 0 | 
| 0 8 0 | 0 0 0 | 0 5 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 3 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 1 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 2 0 | 
| 0 0 0 | 0 0 0 | 0 8 0 | 
-------------------------
| 2 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 6 0 3 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 2 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 8 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 4 | 0 0 0 | 0 0 0 | 
| 0 0 5 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 3 9 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 9 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 9 0 | 0 1 0 | 0 0 0 | 
-------------------------


(medium hard difficulty)

-------------------------
| 0 0 0 | 0 0 0 | 0 0 5 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 7 9 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 8 | 0 0 0 | 0 0 0 | 
| 0 5 0 | 0 0 2 | 0 0 0 | 
| 1 0 2 | 0 0 0 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 4 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 4 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 1 0 0 | 
| 0 6 0 | 8 5 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 1 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 2 | 0 0 0 | 0 0 0 | 
-------------------------

-------------------------
| 0 0 0 | 0 0 9 | 0 0 0 | 
| 7 0 0 | 0 0 0 | 0 0 3 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 9 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 7 | 
| 0 0 0 | 0 0 0 | 0 0 5 | 
| 0 8 0 | 0 0 0 | 0 0 2 | 
-------------------------



-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 1 0 0 | 
-------------------------
| 0 0 0 | 0 0 7 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 7 0 0 | 
| 0 0 0 | 0 0 0 | 5 0 0 | 
-------------------------
| 0 7 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 7 0 | 
| 0 0 6 | 9 0 0 | 0 0 0 | 
-------------------------

(medium hard difficulty)
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 0 0 0 | 0 2 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 0 0 0 | 
| 8 1 0 | 0 0 0 | 0 0 0 | 
| 0 0 0 | 9 1 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 0 0 0 | 5 0 0 | 
| 0 0 0 | 7 0 6 | 0 0 0 | 
| 0 4 0 | 0 0 0 | 0 0 0 | 
-------------------------


39 clue hard
-------------------------
| 0 0 7 | 1 0 5 | 0 0 2 | 
| 6 5 0 | 0 9 0 | 1 0 0 | 
| 0 2 1 | 0 7 0 | 0 6 0 | 
-------------------------
| 7 0 8 | 0 1 0 | 5 0 0 | 
| 0 6 0 | 9 2 0 | 0 0 1 | 
| 4 0 0 | 0 0 0 | 0 0 0 | 
-------------------------
| 0 0 0 | 5 0 7 | 2 0 9 | 
| 1 3 5 | 2 8 0 | 6 0 0 | 
| 0 7 9 | 6 4 1 | 0 5 0 | 
-------------------------

39 clue superhard?
-------------------------
| 9 8 7 | 0 2 6 | 0 0 3 | 
| 0 0 2 | 0 0 5 | 0 0 8 | 
| 0 0 1 | 0 0 0 | 0 2 0 | 
-------------------------
| 8 1 0 | 0 0 0 | 0 0 2 | 
| 0 0 5 | 0 0 3 | 8 0 1 | 
| 0 0 0 | 1 0 8 | 0 0 0 | 
-------------------------
| 0 9 0 | 5 4 0 | 1 0 0 | 
| 0 5 6 | 8 0 0 | 0 0 0 | 
| 1 7 4 | 0 3 0 | 0 0 0 | 
-------------------------

-------------------------
| 0 7 0 | 0 0 4 | 0 2 1 | 
| 0 0 9 | 8 0 1 | 5 0 0 | 
| 0 4 1 | 2 0 0 | 0 8 0 | 
-------------------------
| 0 0 6 | 7 0 3 | 0 0 2 | 
| 7 5 0 | 6 1 0 | 8 9 0 | 
| 0 0 3 | 0 0 0 | 6 0 7 | 
-------------------------
| 0 0 0 | 5 0 0 | 7 0 0 | 
| 0 0 7 | 1 8 6 | 2 4 0 | 
| 4 9 0 | 0 2 7 | 1 0 5 | 
-------------------------

*/



int superHard39Board[BOARD_SIZE][BOARD_SIZE] = {
	{9, 8, 7, 0, 2, 6, 0, 0, 3},
	{0, 0, 2, 0, 0, 5, 0, 0, 8},
	{0, 0, 1, 0, 0, 0, 0, 2, 0},
	{8, 1, 0, 0, 0, 0, 0, 0, 2},
	{0, 0, 5, 0, 0, 3, 8, 0, 1},
	{0, 0, 0, 1, 0, 8, 0, 0, 0},
	{0, 9, 0, 5, 4, 0, 1, 0, 0},
	{0, 5, 6, 8, 0, 0, 0, 0, 0},
	{1, 7, 4, 0, 3, 0, 0, 0, 0}
}

int superHard8Board[BOARD_SIZE][BOARD_SIZE] = {
	{3, 0, 0, 0, 0, 0, 0, 4, 0},
	{0, 0, 0, 0, 0, 0, 0, 0, 0},
	{0, 0, 0, 0, 0, 0, 0, 0, 0},
	{4, 0, 0, 0, 0, 0, 0, 0, 0},
	{2, 0, 0, 0, 0, 0, 0, 0, 0},
	{0, 0, 1, 0, 0, 0, 0, 0, 0},
	{0, 6, 0, 0, 0, 0, 0, 9, 0},
	{0, 9, 0, 0, 0, 0, 0, 0, 0},
	{0, 0, 0, 0, 0, 0, 0, 0, 0}
};

