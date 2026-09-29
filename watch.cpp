/*
Watch SudokuSolver solve a puzzle in the terminal: records every step of the search, then replays it.

usage: watch                      first puzzle in data/board22__1000.txt
       watch <clues> [index]      a puzzle from data/, e.g. watch 29 5
       watch <name>               a hard puzzle from puzzles.hpp, e.g. watch inkala2012
       watch <81 characters>      any puzzle, 0 or . for empty cells
       add -s <seconds> to change how long the replay takes (default 8)
*/
#include "sudokusolver.hpp"
#include "puzzles.hpp"
#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>
#include <vector>


enum class Kind { empty, clue, forced, guess };

struct Step {
	int cell;
	int digit;
	bool removed;
	bool guessed;
};

// what the replay shows: the digit and kind of each cell, plus what just happened
struct Board {
	int digits[81] = {};
	Kind kinds[81] = {};
	int current = -1;       // the cell the last step changed
	bool undoing = false;   // the last step removed a digit
	int guesses = 0;
	int backtracks = 0;
};

namespace ansi {
	const char *reset = "\x1b[0m", *bold = "\x1b[1m", *dim = "\x1b[2m", *reverse = "\x1b[7m";
	const char *red = "\x1b[31m", *green = "\x1b[32m", *yellow = "\x1b[33m";
	const char *home = "\x1b[H", *clearScreen = "\x1b[2J", *clearLine = "\x1b[K";
	const char *hideCursor = "\x1b[?25l", *showCursor = "\x1b[?25h";
}



class Recorder : public SearchObserver {
	public:
		std::vector<Step> steps;
		void placed(int cell, int digit, bool guessed) override { steps.push_back({cell, digit, false, guessed}); }
		void removed(int cell, int digit) override { steps.push_back({cell, digit, true, false}); }
};


bool isNumber(std::string const &s) {
	return !s.empty() && std::all_of(s.begin(), s.end(), [](unsigned char c) { return std::isdigit(c); });
}


Puzzle puzzleFromDataFile(int clues, int index) {
	std::vector<Puzzle> puzzles = readPuzzleFile(dataPath(clues));
	if (puzzles.empty()) {
		throw std::invalid_argument("no puzzles in " + dataPath(clues) + ", run from the repo root");
	}
	if (index < 0 || index >= (int)puzzles.size()) {
		throw std::invalid_argument("index must be 0 to " + std::to_string(puzzles.size() - 1));
	}
	return puzzles[index];
}


Puzzle puzzleFromArgs(std::vector<std::string> const &args) {
	if (args.empty()) {
		return puzzleFromDataFile(22, 0);
	}
	if (args[0].size() == 81) {
		std::string cells = args[0];
		std::replace(cells.begin(), cells.end(), '0', '.');
		return puzzleFromString("from the command line", cells);
	}
	if (isNumber(args[0])) {
		int index = args.size() > 1 ? std::stoi(args[1]) : 0;
		return puzzleFromDataFile(std::stoi(args[0]), index);
	}
	return hardPuzzle(args[0]);
}


Board startingBoard(Puzzle const &p) {
	Board board;
	for (int cell = 0; cell < 81; cell++) {
		board.digits[cell] = p.grid[cell / 9][cell % 9];
		board.kinds[cell] = board.digits[cell] ? Kind::clue : Kind::empty;
	}
	return board;
}


void apply(Board &board, Step const &step) {
	board.current = step.cell;
	board.undoing = step.removed;
	if (step.removed) {
		board.digits[step.cell] = 0;
		board.kinds[step.cell] = Kind::empty;
		board.backtracks++;
	} else {
		board.digits[step.cell] = step.digit;
		board.kinds[step.cell] = step.guessed ? Kind::guess : Kind::forced;
		board.guesses += step.guessed;
	}
}



std::string renderCell(Board const &board, int cell) {
	std::string out = cell == board.current ? ansi::reverse : "";
	switch (board.kinds[cell]) {
		case Kind::clue:   out += ansi::bold; break;
		case Kind::forced: out += ansi::green; break;
		case Kind::guess:  out += ansi::yellow; break;
		case Kind::empty:  out += cell == board.current && board.undoing ? ansi::red : ansi::dim; break;
	}
	out += board.digits[cell] ? std::to_string(board.digits[cell]) : "·";
	return out + ansi::reset;
}


std::string renderGrid(Board const &board) {
	std::string out = "  ┌───────┬───────┬───────┐\n";
	for (int row = 0; row < 9; row++) {
		if (row == 3 || row == 6) out += "  ├───────┼───────┼───────┤\n";
		out += "  │";
		for (int col = 0; col < 9; col++) {
			out += " " + renderCell(board, row * 9 + col);
			if (col % 3 == 2) out += " │";
		}
		out += "\n";
	}
	return out + "  └───────┴───────┴───────┘\n";
}


void draw(Board const &board, std::string const &title, size_t step, size_t totalSteps) {
	int filled = std::count_if(board.digits, board.digits + 81, [](int d) { return d != 0; });
	std::string frame = ansi::home;
	frame += "  " + title + ansi::clearLine + "\n\n";
	frame += renderGrid(board);
	frame += "\n  step " + std::to_string(step) + "/" + std::to_string(totalSteps) + "   guesses " + std::to_string(board.guesses) +
	         "   backtracks " + std::to_string(board.backtracks) + "   filled " + std::to_string(filled) + "/81" + ansi::clearLine + "\n";
	frame += std::string("  ") + ansi::bold + "clue" + ansi::reset + "  " + ansi::green + "forced" + ansi::reset + "  " +
	         ansi::yellow + "guess" + ansi::reset + "  " + ansi::red + "·" + ansi::reset + " backtrack" + ansi::clearLine + "\n";
	std::fputs(frame.c_str(), stdout);
	std::fflush(stdout);
}


void replay(Puzzle const &p, std::vector<Step> const &steps, double seconds) {
	Board board = startingBoard(p);
	auto delay = std::chrono::duration<double>(std::clamp(seconds / std::max<size_t>(steps.size(), 1), 0.001, 0.15));
	std::fputs((std::string(ansi::clearScreen) + ansi::hideCursor).c_str(), stdout);
	draw(board, p.name, 0, steps.size());
	for (size_t i = 0; i < steps.size(); i++) {
		std::this_thread::sleep_for(delay);
		apply(board, steps[i]);
		draw(board, p.name, i + 1, steps.size());
	}
	board.current = -1;
	draw(board, p.name, steps.size(), steps.size());
	std::fputs(ansi::showCursor, stdout);
}



// average time for solve() on its own, without recording, in seconds
double timeSolve(Puzzle const &p) {
	SudokuSolver solver;
	int out[9][9];
	const int reps = 1000;
	auto start = std::chrono::steady_clock::now();
	for (int i = 0; i < reps; i++) {
		solver.solve(p.grid, out);
	}
	return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() / reps;
}


// 2 significant figures as a plain decimal, e.g. 0.0000084
std::string decimalSeconds(double seconds) {
	int decimals = std::max(0, 1 - (int)std::floor(std::log10(seconds)));
	char text[32];
	std::snprintf(text, sizeof text, "%.*f", decimals, seconds);
	return text;
}


void printSummary(Puzzle const &p, bool solved) {
	SudokuSolver solver;
	if (!solved) {
		std::printf("\n  no solution\n\n");
		return;
	}
	std::printf("\n  solved. %s. solve() without watching takes %s s\n\n",
	            solver.hasUniqueSolution(p.grid) ? "the solution is unique" : "the puzzle has more than one solution",
	            decimalSeconds(timeSolve(p)).c_str());
}


void restoreCursor(int signal) {
	std::fputs(ansi::showCursor, stdout);
	std::fputs(ansi::reset, stdout);
	std::fflush(stdout);
	std::_Exit(128 + signal);
}


int main(int argc, char **argv) {
	std::vector<std::string> args;
	double seconds = 8;
	for (int a = 1; a < argc; a++) {
		std::string arg = argv[a];
		if (arg == "-s" && a + 1 < argc) {
			seconds = std::atof(argv[++a]);
		} else {
			args.push_back(arg);
		}
	}

	Puzzle p;
	try {
		p = puzzleFromArgs(args);
	} catch (std::exception const &e) {
		std::fprintf(stderr, "can't load that puzzle (%s). see the usage at the top of watch.cpp\n", e.what());
		return 1;
	}

	Recorder recorder;
	SudokuSolver solver;
	solver.watch(&recorder);
	int out[9][9];
	bool solved = solver.solve(p.grid, out);

	std::signal(SIGINT, restoreCursor);
	replay(p, recorder.steps, seconds);
	printSummary(p, solved);
	return 0;
}
