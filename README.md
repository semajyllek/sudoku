### generating and solving sudoku tables

- `sudokusolver.hpp`: solver built on [TinyBitSet](https://github.com/semajyllek/TinyBitSet). it branches on the cell
  with the fewest candidates and places hidden singles first. it can also count solutions:
  `hasUniqueSolution(puzzle)` checks that a puzzle has exactly one
- `fastbandsolver.hpp`: faster solver, same interface. stores each digit's candidates by band (zhouyundong's layout,
  as in JCZSolve), prunes with matching rules on bands and stacks, and branches on the two-candidate cell with the most
  unsolved peers. faster than tdoku on all five data sets below
- `parallelbandsolver.hpp`: fastbandsolver's search spread over several threads for one puzzle, same interface.
  about twice as fast on the hardest puzzles with 4 threads; no help on easy ones
- `arrayboard.hpp` and `bitboard.hpp`: the original solvers. both fill cells in row order and backtrack, giving up
  after 20 million tries
- `gendata.cpp`: generates the puzzles in `data/`
- needs C++20 and `tinybitset` checked out next to this repo, at `../tinybitset`

```
make test     # solver tests
make bench    # sudokusolver timings and the uniqueness report
make data     # regenerate data/ (same seed, same files)
make watch    # replay the solver on a puzzle in the terminal, see below
make sota     # compare with tdoku, jsolve and kudoku, see results (REPS=5 runs per set)
make verify   # fastbandsolver against tdoku on all 7 of its data sets: counts at limits 1-3 and every solution
make parallel # one puzzle on several threads: parallelbandsolver against fastbandsolver and tdoku (about 4 minutes)
make throughput  # many puzzles on many cores, one process per core (about 30 minutes)
make paper    # build/paper/paper.pdf, the write-up (needs latexmk)
make all      # also builds the original solvers' benchmarks (bitboard.hpp needs brew install libomp)
```

`make sota`, `make parallel` and `make throughput` check uniqueness (a limit of 2 solutions) by default; add `LIMIT=1`
to time finding one solution instead.

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

compared with other solvers: seconds per puzzle, on tdoku's standard data sets, checking that each solution is
unique (a limit of 2 solutions, as in tdoku's benchmarks). Apple M4 Max, clang `-O3 -march=native`. every solver
solves every puzzle correctly. from `make sota`:

  data set | puzzles | fastbandsolver | sudokusolver | tdoku | jsolve | kudoku
  --- | --- | --- | --- | --- | --- | ---
  17 clue | 49158 | 1.64 × 10⁻⁶ | 1.53 × 10⁻⁵ | 2.63 × 10⁻⁶ | 2.71 × 10⁻⁶ | 1.33 × 10⁻⁵
  magictour top 1465 | 1465 | 6.29 × 10⁻⁶ | 6.23 × 10⁻⁵ | 7.48 × 10⁻⁶ | 1.15 × 10⁻⁵ | 5.84 × 10⁻⁵
  forum hardest 1106 | 375 | 5.70 × 10⁻⁵ | 4.50 × 10⁻⁴ | 6.69 × 10⁻⁵ | 1.35 × 10⁻⁴ | 5.09 × 10⁻⁴
  forum hardest 1905 11+ | 48766 | 3.77 × 10⁻⁵ | 2.59 × 10⁻⁴ | 4.39 × 10⁻⁵ | 8.47 × 10⁻⁵ | 2.55 × 10⁻⁴
  kaggle | 100000 | 8.24 × 10⁻⁷ | 1.51 × 10⁻⁶ | 8.90 × 10⁻⁷ | 1.49 × 10⁻⁶ | 7.18 × 10⁻⁶

- [tdoku](https://github.com/t-dillon/tdoku) is the fastest solver on hard puzzles in its own benchmark of the
  fastest known solvers. it only supports x86, so this uses its [ARM port](https://github.com/t-dillon/tdoku/pull/13)
- jsolve and kudoku are the fastest cell-based and exact-cover (dancing links style) solvers in tdoku's benchmarks
- fastbandsolver is 1.1 to 1.6 times faster than tdoku. `paper/` describes how, with an ablation and the approaches
  that didn't work
- on x86 the result depends on the processor. measured on rented machines (`bench/results`, workflow in
  `.github/workflows/x86.yml`), fastbandsolver / tdoku on the hard sets: amd zen 3 1.00 to 1.06, amd zen 4 0.92 to 0.96,
  intel ice lake and sapphire rapids 0.67 to 0.73. it is level or faster on 17 clue everywhere but ice lake (0.98)
- sudokusolver is about as fast as kudoku, and 3 to 5.5 times slower than jsolve on the hard sets. jsolve keeps each
  cell's candidates between steps and uses locked candidates. sudokusolver recomputes candidates at every step

`make sota` needs tdoku checked out at `../tdoku`. on ARM, until the port is merged:

```
git clone -b arm-neon https://github.com/semajyllek/tdoku ../tdoku
```

sudokusolver on all 1000 boards of a file in `data/`, split across threads, one solver per thread
(`build/bench_sudokusolver par`, clang `-O2`). the speedup is smaller on easy files, where starting threads costs
about as much as the solving:

  clues | 1 thread | 14 threads | speedup
  --- | --- | --- | ---
  22 | 8.9 × 10⁻³ | 9.7 × 10⁻⁴ | 9.2x
  29 | 4.9 × 10⁻³ | 6.0 × 10⁻⁴ | 8.1x
  39 | 1.9 × 10⁻³ | 3.4 × 10⁻⁴ | 5.6x
  49 | 9.4 × 10⁻⁴ | 2.6 × 10⁻⁴ | 3.6x
  59 | 6.5 × 10⁻⁴ | 2.8 × 10⁻⁴ | 2.4x
  69 | 3.9 × 10⁻⁴ | 2.2 × 10⁻⁴ | 1.8x
  79 | 2.4 × 10⁻⁴ | 2.2 × 10⁻⁴ | 1.1x


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
