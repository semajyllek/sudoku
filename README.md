### repo for generating and solving sudoku tables....

in progress....
currently very fast at generating and solving **most** tables using modified backtracking only

### goals:

- implement HGSA solving (https://arxiv.org/pdf/0805.0697.pdf)
- construct dataset of tables of various difficulties as 81 token sequences with 0s as unknowns (MASKED), upload to hf hub
- train vs fine-tune seq2seq, eval performance
- write-up
