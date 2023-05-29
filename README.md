### repo for generating and solving sudoku tables

- uses naked groups
- space and time efficient implementation using TinyBitSets
- arrayBoard.h has array implmentation, bitBoard.h has bitset implementation
- falls back on backtracking to guess when needed


Time tables using generated sudoku tables:


|---|---|---|---|---|
                        |    wall time 1 |  wall time 10 |  wall time 100 | wall time 1000 |  wall time 100000 |
| easy (40 clues)       |                |               |                |                |                   |
| medium (30 clues)     |                |               |                |                |                   |
| hard (20 clues)       |                |               |                |                |                   |
| very hard (10 clues)  |                |               |                |                |                   |
| devilish (5 clues)    |                |               |                |                |                   |
---

