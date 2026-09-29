### generating and solving sudoku tables

- `sudokusolver.hpp`: solver built on [TinyBitSet](https://github.com/semajyllek/TinyBitSet). it fills the cell with the
  fewest possible digits first, and places hidden singles (a digit that fits in only one cell of a row, column or box)
  before guessing. it can also count solutions, so `hasUniqueSolution(puzzle)` checks a puzzle has exactly one answer
- `arrayboard.hpp` (std::vector per cell) and `bitboard.hpp` (TinyBitSets, naked groups) are the original solvers.
  both fill cells in row order and fall back on backtracking, giving up after 20 million tries
- `tinybitset` is expected next to this repo, at `../tinybitset`, and needs C++20

```
make test     # solver tests
make bench    # sudokusolver timings and the uniqueness report
make data     # regenerate data/ (same files every time)
make all      # also builds build/bench_bitboard and build/bench_arrayboard (bitboard.hpp needs brew install libomp)
```

each benchmark binary takes `data [reps]`, `hard [name|all]` or `par [reps] [threads...]`.


### results

all times in seconds, Apple M4 Max, clang `-std=c++20 -O2`, on the puzzles in `data/` (1000 per clue count, each with
exactly one solution, see below). every answer is checked against the rules and the clues, and timing includes each
solver's setup.

average time per board:

  clues | array | bitset | sudokusolver
  --- | --- | --- | ---
  22 | 0.054 | 0.0069 | 0.000010
  29 | 0.0011 | 0.000076 | 0.0000046
  39 | 0.000035 | 0.000018 | 0.0000017
  49 | 0.0000076 | 0.000011 | 0.00000076
  59 | 0.0000041 | 0.0000076 | 0.00000046
  69 | 0.0000024 | 0.0000052 | 0.00000029
  79 | 0.0000012 | 0.0000033 | 0.00000014

slowest board:

  clues | array | bitset | sudokusolver
  --- | --- | --- | ---
  22 | 3.2 | 0.49 | 0.00011
  29 | 0.067 | 0.0018 | 0.000014
  39 | 0.00071 | 0.000041 | 0.000018
  49 | 0.000034 | 0.000024 | 0.0000079
  59 | 0.000015 | 0.000015 | 0.00000088
  69 | 0.000016 | 0.000021 | 0.00000042
  79 | 0.0000015 | 0.000016 | 0.00000021

all three solve every puzzle. (on the original 2023 data the two original solvers left up to 19 of 1000 boards
unsolved at the lowest clue counts, when they hit their try limit.)

multiprocessing, sudokusolver solving all 1000 boards of a file, split across threads (each thread has its own
solver and takes the next board no other thread has claimed). a single board can't usefully be split this way, the
speedup comes from solving different boards at the same time. it drops for the easier files, where starting threads
costs about as much as the work:

  clues | 1 thread | 14 threads | speedup
  --- | --- | --- | ---
  22 | 0.0088 | 0.0010 | 8.7x
  29 | 0.0049 | 0.00062 | 7.9x
  39 | 0.0020 | 0.00034 | 5.8x
  49 | 0.0010 | 0.00024 | 4.2x
  59 | 0.00060 | 0.00022 | 2.7x
  69 | 0.00043 | 0.00021 | 2.0x
  79 | 0.00023 | 0.00017 | 1.4x



### data:
`data/` has 1000 puzzles for each clue count: 22, 29, 39, 49, 59, 69 and 79. every puzzle has exactly that many clues
and exactly one solution, which is stored with it. they're made by `gendata.cpp` (`make data`), which fills a random
complete grid and then blanks cells in random order, keeping each blank only if the puzzle still has one solution.
it uses a fixed seed, so rerunning it produces the same files. the first puzzle in `board29__1000.txt`:

```

New Board: 
0,0,3,0,0,0,5,0,7
4,5,0,0,9,2,0,0,0
0,9,0,7,0,0,0,0,0
7,0,0,0,5,0,0,0,0
0,0,0,4,0,9,1,0,5
0,4,0,0,1,0,9,2,0
0,6,5,0,0,4,7,1,0
2,7,0,0,0,8,0,5,0
0,0,0,0,0,0,4,0,0

Solved Board:
8,2,3,6,4,1,5,9,7
4,5,7,8,9,2,6,3,1
1,9,6,7,3,5,2,8,4
7,1,9,2,5,6,8,4,3
6,3,2,4,8,9,1,7,5
5,4,8,3,1,7,9,2,6
3,6,5,9,2,4,7,1,8
2,7,4,1,6,8,3,5,9
9,8,1,5,7,3,4,6,2

```

there's no 9 or 19 clue file any more: a sudoku needs at least 17 clues to have only one solution, and random
blanking usually gets stuck at 23 to 26 clues (only about 1 grid in 26 got down to 22). `data.zip` has the original 2023 data, which wasn't checked for this. none of its
9, 19 or 29 clue boards had a unique solution, its stored solutions often didn't keep the puzzle's own clues, and
its file names were the most clues a board could have rather than an exact count.

Note this doesn't reflect difficulty, as this would be related to time for a particular algorithm to solve, and observationally
is not **dependent** solely on the number of clues. see wikipedia/sudoku.


### extension idea:

- quantify difficulty by extracing a number of hand-crafted features and timing puzzle solutions and 
  investigating feature/time covariance for possible high level information about crafting difficult sudoku puzzles 

- implications for sudoku encryption algorithms... 

---

