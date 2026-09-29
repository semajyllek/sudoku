// how many puzzles in each data file have no solution, exactly one, or several,
// and what checking that costs with SudokuSolver::countSolutions
#include "../sudokusolver.hpp"
#include "benchlib.hpp"

int main() {
	SudokuSolver solver;
	std::printf("%-10s %5s %5s %7s %9s %14s %13s\n", "set", "n", "none", "unique", "multiple", "check_mean_us", "check_max_us");
	for (int clues : CLUE_COUNTS) {
		auto puzzles = loadFile(dataPath(clues));
		if (puzzles.empty()) continue;
		int tally[3] = {};
		std::vector<double> micros;
		for (auto const &p : puzzles) {
			auto start = Clock::now();
			tally[solver.countSolutions(p.grid, 2)]++;
			std::chrono::duration<double, std::micro> elapsed = Clock::now() - start;
			micros.push_back(elapsed.count());
		}
		double total = 0;
		for (double m : micros) total += m;
		std::printf("%-10s %5zu %5d %7d %9d %14.2f %13.2f\n", (std::to_string(clues) + " clues").c_str(), puzzles.size(),
		            tally[0], tally[1], tally[2], total / puzzles.size(), percentile(micros, 1.0));
	}
}
