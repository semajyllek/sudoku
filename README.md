### generating and solving sudoku tables

- uses naked groups
- comparison of space and time efficient implementation using TinyBitSets vs std::array
- arrayBoard.h has array implmentation, bitBoard.h has bitset implementation
- both fall back on backtracking to guess when needed


Time tables using generated sudoku tables in `data/data.zip`:


  difficulty  | wall time 1 |  wall time 10 |  wall time 100 | wall time 1000 |
--- | --- |  --- | --- | --- | --- |
79 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
69 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
59 clues  | 8473 | 3437 | 732 | 3233 | 356 |   
49 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
39 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
29 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
19 clues  | 8473 | 3437 | 732 | 3233 | 356 | 
9 clues   | 8473 | 3437 | 732 | 3233 | 356 | 



### data:
data.zip has 1000 boards and solutions of each clue size: 9, 19, 29, 39, 49, 59, 69, 79, like this:

```

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

```

Note this doesn't reflect difficulty, as this would be related to time for a particular algorithm to solve, and observationally
is not **dependent** solely on the number of clues. see wikipedia/sudoku.


### extension idea:

- quantify difficulty by extracing a number of hand-crafted features and timing puzzle solutions and 
  investigating feature/time covariance for possible high level information about crafting difficult sudoku puzzles 

- implications for sudoku encryption algorithms... 

---

