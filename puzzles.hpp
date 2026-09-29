/*
Puzzle data shared by gendata, the tests and the benchmarks: the Puzzle type, where the data files live,
reading and writing them, checking a solution, and a few hand-picked hard puzzles.
*/
#pragma once
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>


struct Puzzle {
	std::string name;
	int grid[9][9] = {};      // 0 = empty
	int solution[9][9] = {};
	bool hasSolution = false;
};

constexpr int CLUE_COUNTS[] = {22, 29, 39, 49, 59, 69, 79};
constexpr int PUZZLES_PER_FILE = 1000;


inline std::string dataPath(int clues) {
	return "data/board" + std::to_string(clues) + "__" + std::to_string(PUZZLES_PER_FILE) + ".txt";
}



inline bool readGrid(std::ifstream &file, int grid[9][9]) {
	std::string line, cell;
	for (int r = 0; r < 9; r++) {
		if (!std::getline(file, line)) return false;
		std::stringstream cells(line);
		for (int c = 0; c < 9; c++) {
			if (!std::getline(cells, cell, ',')) return false;
			grid[r][c] = std::stoi(cell);
		}
	}
	return true;
}


inline void writeGrid(std::ofstream &file, const int grid[9][9]) {
	for (int r = 0; r < 9; r++) {
		for (int c = 0; c < 9; c++) {
			file << grid[r][c] << (c < 8 ? "," : "\n");
		}
	}
}


// the "New Board:" / "Solved Board:" layout that ArrayBoard::saveBoard writes and utils.hpp reads
inline std::vector<Puzzle> readPuzzleFile(std::string const &path) {
	std::vector<Puzzle> puzzles;
	std::ifstream file(path);
	std::string line;
	while (std::getline(file, line)) {
		if (line.rfind("New Board", 0) == 0) {
			Puzzle p;
			p.name = path + "#" + std::to_string(puzzles.size());
			if (!readGrid(file, p.grid)) break;
			puzzles.push_back(p);
		} else if (line.rfind("Solved Board", 0) == 0 && !puzzles.empty()) {
			puzzles.back().hasSolution = readGrid(file, puzzles.back().solution);
		}
	}
	return puzzles;
}


inline void writePuzzleFile(std::string const &path, std::vector<Puzzle> const &puzzles) {
	std::ofstream file(path);
	for (auto const &p : puzzles) {
		file << "\nNew Board: \n";
		writeGrid(file, p.grid);
		file << "\nSolved Board:\n";
		writeGrid(file, p.solution);
	}
}



// complete, every row/col/box a permutation of 1-9, and every clue kept
inline bool validSolution(const int in[9][9], const int out[9][9]) {
	for (int i = 0; i < 9; i++) {
		int rowSeen = 0, colSeen = 0, boxSeen = 0;
		for (int j = 0; j < 9; j++) {
			int rv = out[i][j], cv = out[j][i], bv = out[3 * (i / 3) + j / 3][3 * (i % 3) + j % 3];
			if (rv < 1 || rv > 9 || cv < 1 || cv > 9 || bv < 1 || bv > 9) return false;
			rowSeen |= 1 << rv;
			colSeen |= 1 << cv;
			boxSeen |= 1 << bv;
			if (in[i][j] != 0 && in[i][j] != out[i][j]) return false;
		}
		if (rowSeen != 0x3FE || colSeen != 0x3FE || boxSeen != 0x3FE) return false;
	}
	return true;
}



inline Puzzle puzzleFromString(std::string const &name, std::string const &cells) {
	Puzzle p;
	p.name = name;
	for (int i = 0; i < 81; i++) {
		p.grid[i / 9][i % 9] = cells[i] == '.' ? 0 : cells[i] - '0';
	}
	return p;
}


// hand-picked hard and edge-case puzzles
inline std::vector<Puzzle> hardPuzzles() {
	return {
		// from boards.h
		puzzleFromString("easyBoard",          "1.......2..8..9.377..53..8..8..73.54..64.27..97.85..1..1..87..934.6..8..8.......1"),
		puzzleFromString("hardBoard",          "4..9..3....21....453..................4..9.6...78....2.75..62....9..7..8.....5..3"),
		puzzleFromString("superHard39Board",   "987.26..3..2..5..8..1....2.81......2..5..38.1...1.8....9.54.1...568.....174.3...."),
		puzzleFromString("superHard8Board",    "3......4...................4........2..........1.......6.....9..9................"),
		puzzleFromString("arraySegfaultBoard", ".234...7..9..8.134.8.3.5..94.25......6...1.....9..........5....3........8........"),
		puzzleFromString("hardarrayBoard",     ".....35..................2.................6..7......4..4...........5...7........"),
		// well-known public benchmark puzzles
		puzzleFromString("inkala2012",         "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."),
		puzzleFromString("antiBacktrack",      "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9"),
	};
}


inline Puzzle hardPuzzle(std::string const &name) {
	for (auto const &p : hardPuzzles()) {
		if (p.name == name) return p;
	}
	throw std::invalid_argument("no hard puzzle named " + name);
}
