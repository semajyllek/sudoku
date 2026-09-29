### generating and solving sudoku tables

- `sudokusolver.hpp`: solver built on [TinyBitSet](https://github.com/semajyllek/TinyBitSet). it branches on the cell
  with the fewest candidates and places hidden singles first. it can also count solutions:
  `hasUniqueSolution(puzzle)` checks that a puzzle has exactly one
- `arrayboard.hpp` and `bitboard.hpp`: the original solvers. both fill cells in row order and backtrack, giving up
  after 20 million tries
- `gendata.cpp`: generates the puzzles in `data/`
- needs C++20 and `tinybitset` checked out next to this repo, at `../tinybitset`

```
make test     # solver tests
make bench    # sudokusolver timings and the uniqueness report
make data     # regenerate data/ (same seed, same files)
make watch    # replay the solver on a puzzle in the terminal, see below
make all      # also builds the original solvers' benchmarks (bitboard.hpp needs brew install libomp)
```

each benchmark binary takes `data [reps]`, `hard [name|all]` or `par [reps] [threads...]`.


### watching the solver

`build/watch` records every step the solver takes on one puzzle, then replays it in the terminal.

```
./build/watch                     # first puzzle in data/board22__1000.txt
./build/watch 29 5                # puzzle 5 from data/board29__1000.txt
./build/watch inkala2012          # a named puzzle from puzzles.hpp
./build/watch 8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..
                                  # any 81-character puzzle, 0 or . for empty cells
./build/watch inkala2012 -s 20    # replay over 20 seconds instead of 8
```

clues are bold, forced placements green, guesses yellow, and a removed digit flashes red when the solver backtracks.
the last line gives whether the solution is unique and how long `solve()` takes without the replay. run it from the
repo root so it can find `data/`.


### results

times in seconds. Apple M4 Max, clang `-std=c++20 -O2`, puzzles from `data/`. every answer is checked against the
rules and the clues, and timing includes each solver's setup. all three solvers solve every puzzle.

average time per board:

  clues | array | bitset | sudokusolver
  --- | --- | --- | ---
  22 | 0.054 | 0.0069 | 0.0000084
  29 | 0.0011 | 0.000076 | 0.0000045
  39 | 0.000035 | 0.000018 | 0.0000016
  49 | 0.0000076 | 0.000011 | 0.00000073
  59 | 0.0000041 | 0.0000076 | 0.00000039
  69 | 0.0000024 | 0.0000052 | 0.00000024
  79 | 0.0000012 | 0.0000033 | 0.00000015

slowest board:

  clues | array | bitset | sudokusolver
  --- | --- | --- | ---
  22 | 3.2 | 0.49 | 0.000068
  29 | 0.067 | 0.0018 | 0.000019
  39 | 0.00071 | 0.000041 | 0.0000042
  49 | 0.000034 | 0.000024 | 0.0000020
  59 | 0.000015 | 0.000015 | 0.00000079
  69 | 0.000016 | 0.000021 | 0.00000042
  79 | 0.0000015 | 0.000016 | 0.00000029

sudokusolver on all 1000 boards of a file, split across threads, one solver per thread. the speedup is smaller on
easy files, where starting threads costs about as much as the solving:

  clues | 1 thread | 14 threads | speedup
  --- | --- | --- | ---
  22 | 0.0088 | 0.0010 | 8.7x
  29 | 0.0049 | 0.00062 | 7.9x
  39 | 0.0020 | 0.00034 | 5.8x
  49 | 0.0010 | 0.00024 | 4.2x
  59 | 0.00060 | 0.00022 | 2.7x
  69 | 0.00043 | 0.00021 | 2.0x
  79 | 0.00023 | 0.00017 | 1.4x


### data

`data/` has 1000 puzzles for each clue count: 22, 29, 39, 49, 59, 69 and 79. each has exactly that many clues and
exactly one solution, stored with it. `gendata.cpp` fills a random complete grid, then blanks cells in random order,
keeping a blank only if the solution stays unique. the first puzzle in `board29__1000.txt`:

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

a unique solution needs at least 17 clues, and random blanking rarely gets below 23, so 22 is the lowest file.
clue count is only a rough guide to difficulty.


### extension ideas

- quantify difficulty: extract hand-crafted features, time solutions, and look at how features and time covary,
  for insight into making hard puzzles
- implications for sudoku encryption algorithms
