### repo for generating and solving sudoku tables

- uses naked groups
- space and time efficient implementation using TinyBitSets
- arrayBoard.h has array implmentation, bitBoard.h has bitset implementation
- falls back on backtracking to guess when needed


Time tables using generated sudoku tables:


    | wall time 1 |  wall time 10 |  wall time 100 | wall time 1000 |  wall time 100000 |
--- | --- |  --- | --- | --- | --- |
easy (40 clues)  | 8473 | 3437 | 732 | 3233 | 356 | 
medium (30 clues)  | 8473 | 3437 | 732 | 3233 | 356 | 
hard (20 clues)      | 8473 | 3437 | 732 | 3233 | 356 |   
very hard (10 clues)  | 8473 | 3437 | 732 | 3233 | 356 | 
| devilish (5 clues)    | 8473 | 3437 | 732 | 3233 | 356 | 
---

