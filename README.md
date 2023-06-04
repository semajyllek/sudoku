### generating and solving sudoku tables

- uses naked groups
- comparison of space and time efficient implementation using TinyBitSets vs std::array
- arrayBoard.h has array implmentation, bitBoard.h has bitset implementation
- both fall back on backtracking to guess when needed


Time tables in ms using pseudo-randomly generated sudoku tables in `data/data.zip`, tbs=tinybitset, mp=multiprocessing:


  clues  | array mean | array min | array max | tbs mean | tbs min | tbs max | mp tbs mean | mp tbs min | mp tbs max 
  ---    | ---        |  ---      | ---       | ---      | ---     |  ---    | ---         | ---        | --- 
  9      | 0.02       | 7e-5      | 5.75      | 7e-3     | 1e-4    | 2.13    | 4e-3        | 5e-5       | 1.14 
  19     | 0.002      | 5e-5      | 0.88      | 4e-3     | 7e-5    | 0.05    | 2e-4        | 4e-5       | 0.03
  29     | 0.009      | 3e-5      | 7.96      | 3e-3     | 2e-6    | 2.96    | 2e-3        | 2e-6       | 1.63 
  39     | 0.005      | 2e-5      | 0.22      | 8e-5     | 1e-6    | 0.07    | 4e-5        | 0          | 0.04
  49     | 4e-5       | 2e-5      | 3e-4      | 3e-6     | 1e-6    | 6e-5    | 2e-6        | 0          | 4e-5
  59     | 2e-5       | 1e-5      | 8e-5      | 1e-6     | 1e-6    | 9e-6    | 1e-6        | 0          | 8e-6
  69     | 1e-5       | 7e-6      | 4e-5      | 1e-6     | 1e-6    | 3e-6    | 8e-7        | 0          | 2e-6
  79     | 8e-6       | 2e-6      | 2e-5      | 1e-6     | 1e-6    | 7e-6    | 8e-7        | 0          | 3e-6 



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

