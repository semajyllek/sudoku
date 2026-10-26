// extracts real FastBandSolver states for the search helper diagrams (chooseguesscell.py, peerscore.py,
// nextvaluein.py, fewestcandidatescell.py, record.py), as JSON on stdout. It walks the tree in the same order as
// FastBandSolver::search, calling the real propagate, chooseGuessCell, fewestCandidatesCell, nextValueIn, place and
// record, and dumps:
//   "guess":    the first Open state of the given puzzle with four or more two-candidate cells and a tie for the best
//               score, every pair cell's peerScore, and the guess
//   "propagate": the first propagate call of the given puzzle, in search order, that makes a good example (see
//               replayPropagate; for propagate.py), replayed pass by pass on a copy of the state it started from: the
//               masks each pass counts, and the naked singles it places
//   "solved":   the first Solved state of that puzzle, and the grid record wrote
//   "fallback": the first state, over the given files in order, where chooseGuessCell finds no two-candidate cell and
//               the first unsolved cell has more candidates than the one fewestCandidatesCell picks
// usage: search_states <puzzle file> <puzzle string> <fallback file>...
#define private public
#include "../../fastbandsolver.hpp"
#undef private
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
using FB = FastBandSolver;
using St = FB::State;
static FB fb;

static void dumpMasks(St const &state) {
	printf("\"valueToBand\": [");
	for (int digit = 0; digit < 9; digit++) printf("%s[%u, %u, %u]", digit ? ", " : "", state.valueToBand[digit][0], state.valueToBand[digit][1], state.valueToBand[digit][2]);
	printf("], \"unsolved\": [%u, %u, %u]", state.unsolved[0], state.unsolved[1], state.unsolved[2]);
}

static std::vector<std::string> readPuzzles(const char *path) {
	std::ifstream f(path);
	std::string line;
	std::vector<std::string> puzzles;
	while (std::getline(f, line)) if (line.size() >= 81 && line[0] != '#') puzzles.push_back(line.substr(0, 81));
	return puzzles;
}

static bool loadPuzzle(St &state, std::string const &p) {
	int g[9][9];
	for (int k = 0; k < 81; k++) g[k / 9][k % 9] = p[k] == '.' ? 0 : p[k] - '0';
	return fb.load(state, g);
}

// what the walk is looking for
static bool wantGuess, wantSolved, wantFallback, wantPropagate;
static bool haveGuess, haveSolved, haveFallback, havePropagate;
static int solution[9][9];

// whether a state makes a good chooseGuessCell example: at least four two-candidate cells, and a later one with the same
// score as the winner, so that the strict > (first in board order wins) shows
static bool showsTieBreak(St const &state, FB::Mask const pairs[3], FB::GuessCell const &guess) {
	if (guess.band < 0 || std::popcount(pairs[0]) + std::popcount(pairs[1]) + std::popcount(pairs[2]) < 4) return false;
	int best = FB::peerScore(state, guess.band, std::countr_zero(guess.cellBitMask));
	bool afterWinner = false;
	for (int band = 0; band < 3; band++)
		for (FB::Mask p = pairs[band]; p; p &= p - 1) {
			if (band == guess.band && (p & -p) == guess.cellBitMask) afterWinner = true;
			else if (afterWinner && FB::peerScore(state, band, std::countr_zero(p)) == best) return true;
		}
	return false;
}

// whether a state makes a good fewestCandidatesCell example: the first unsolved cell in board order has more candidates
// than the cell chosen, so that "candidates < best.candidates" replaces a real cell, not only the starting 10
static bool firstCellHasMore(St const &state, FB::GuessCell const &guess) {
	for (int band = 0; band < 3; band++) {
		if (!state.unsolved[band]) continue;
		int bitIndex = std::countr_zero(state.unsolved[band]), candidates = 0;
		for (int digit = 0; digit < 9; digit++) candidates += (state.valueToBand[digit][band] >> bitIndex) & 1;
		return candidates > guess.candidates;
	}
	return false;
}

// replays FastBandSolver::propagate on state, a copy of the state propagate was called with, writing each pass to out:
// the masks after update ("start"), each band's nine masks and unsolved as its counting reads them, and the naked singles placed (band, bitIndex, digit). The loop body
// is propagate's, line for line; the end state and pairs are checked against the real call's. Returns whether the call
// makes a good example: two or more passes, and a band in the first pass with two or more naked singles, two or more
// two-candidate cells and a cell with three or more
static bool replayPropagate(St state, St const &real, FB::Mask const realPairs[3], std::string &out) {
	char buffer[64];
	auto add = [&](auto... args) { snprintf(buffer, sizeof buffer, args...); out += buffer; };
	FB::Mask pairs[3];
	bool good = false;
	int pass = 0;
	out = "\"propagate\": {\"passes\": [";
	for (;; pass++) {
		if (!fb.update(state)) return false;
		out += pass ? ", {\"start\": [" : "{\"start\": [";
		for (int digit = 0; digit < 9; digit++) add("%s[%u, %u, %u]", digit ? ", " : "", state.valueToBand[digit][0], state.valueToBand[digit][1], state.valueToBand[digit][2]);
		out += "], \"bands\": [";
		std::string singlesOut;
		bool placed = false, firstSingle = true;
		for (int band = 0; band < 3; band++) {
			// the band's masks as its counting reads them: singles placed earlier in the pass, in other bands, may
			// already have changed them
			add("%s{\"masks\": [", band ? ", " : "");
			for (int digit = 0; digit < 9; digit++) add("%s%u", digit ? ", " : "", state.valueToBand[digit][band]);
			add("], \"unsolved\": %u}", state.unsolved[band]);
			FB::Mask once = 0, twice = 0, thrice = 0;
			for (int digit = 0; digit < 9; digit++) {
				FB::Mask bandCells = state.valueToBand[digit][band];
				thrice |= twice & bandCells;
				twice |= once & bandCells;
				once |= bandCells;
			}
			if (once != FB::ALL_CELLS) return false;
			pairs[band] = twice & ~thrice;
			FB::Mask singlesNow = once & ~twice & state.unsolved[band];
			if (pass == 0 && std::popcount(singlesNow) >= 2 && std::popcount(pairs[band]) >= 2 && thrice) good = true;
			for (FB::Mask singles = singlesNow; singles; singles &= singles - 1) {
				FB::Mask cellBitMask = singles & -singles;
				int digit = FB::nextValueIn(state, band, cellBitMask, 0);
				if (digit == 9) return false;
				snprintf(buffer, sizeof buffer, "%s[%d, %d, %d]", firstSingle ? "" : ", ", band, std::countr_zero(cellBitMask), digit);
				singlesOut += buffer;
				firstSingle = false;
				FB::clearPeers(state, digit, band, cellBitMask);
				placed = true;
			}
		}
		out += "], \"singles\": [" + singlesOut + "]}";
		if (!placed) break;
	}
	add("], \"realPairs\": [%u, %u, ", realPairs[0], realPairs[1]);
	add("%u]", realPairs[2]);
	if (std::memcmp(state.valueToBand, real.valueToBand, sizeof state.valueToBand) || std::memcmp(pairs, realPairs, sizeof pairs)) {
		fprintf(stderr, "replay differs from propagate\n");
		exit(1);
	}
	return good && pass >= 1;
}

// FastBandSolver::search, with a dump at each point of interest
static void walk(St *state, int depth) {
	FB::Mask pairs[3];
	St before;
	std::memcpy(&before, state, sizeof(St));
	FB::Progress progress = fb.propagate(*state, pairs);
	if (wantPropagate && !havePropagate && progress != FB::Progress::Contradiction) {
		std::string out;
		if (replayPropagate(before, *state, pairs, out)) {
			havePropagate = true;
			printf("%s, \"depth\": %d},\n", out.c_str(), depth);
		}
	}
	if (progress == FB::Progress::Contradiction) return;
	if (progress == FB::Progress::Solved) {
		bool first = fb.found == 0;
		fb.record(*state);
		if (wantSolved && first && !haveSolved) {
			haveSolved = true;
			printf("\"solved\": {\"depth\": %d, ", depth);
			dumpMasks(*state);
			printf(", \"grid\": [");
			for (int k = 0; k < 81; k++) printf("%s%d", k ? ", " : "", solution[k / 9][k % 9]);
			printf("]},\n");
		}
		return;
	}

	FB::GuessCell guess = FB::chooseGuessCell(*state, pairs);
	if (wantGuess && !haveGuess && showsTieBreak(*state, pairs, guess)) {
		haveGuess = true;
		printf("\"guess\": {\"depth\": %d, ", depth);
		dumpMasks(*state);
		printf(", \"pairs\": [%u, %u, %u], \"scores\": [", pairs[0], pairs[1], pairs[2]);
		bool firstScore = true;
		for (int band = 0; band < 3; band++)
			for (FB::Mask p = pairs[band]; p; p &= p - 1) {
				printf("%s[%d, %d, %d]", firstScore ? "" : ", ", band, std::countr_zero(p), FB::peerScore(*state, band, std::countr_zero(p)));
				firstScore = false;
			}
		int first = FB::nextValueIn(*state, guess.band, guess.cellBitMask, 0);
		int second = FB::nextValueIn(*state, guess.band, guess.cellBitMask, first + 1);
		printf("], \"result\": [%d, %u, %d], \"first\": %d, \"second\": %d},\n", guess.band, guess.cellBitMask, guess.candidates, first, second);
	}
	if (guess.band >= 0) {
		int first = FB::nextValueIn(*state, guess.band, guess.cellBitMask, 0);
		int second = FB::nextValueIn(*state, guess.band, guess.cellBitMask, first + 1);
		St *child = state + 1;
		std::memcpy(child, state, sizeof(St));
		FB::place(*child, first, guess.band, guess.cellBitMask);
		walk(child, depth + 1);
		if (fb.found >= fb.limit) return;
		FB::place(*state, second, guess.band, guess.cellBitMask);
		walk(state, depth);
		return;
	}

	guess = FB::fewestCandidatesCell(*state);
	if (wantFallback && !haveFallback && firstCellHasMore(*state, guess)) {
		haveFallback = true;
		printf("\"fallback\": {\"depth\": %d, ", depth);
		dumpMasks(*state);
		printf(", \"result\": [%d, %u, %d], \"digits\": [", guess.band, guess.cellBitMask, guess.candidates);
		bool firstDigit = true;
		for (int digit = FB::nextValueIn(*state, guess.band, guess.cellBitMask, 0); digit < 9;
		     digit = FB::nextValueIn(*state, guess.band, guess.cellBitMask, digit + 1)) {
			printf("%s%d", firstDigit ? "" : ", ", digit);
			firstDigit = false;
		}
		printf("], ");
	}
	for (int digit = FB::nextValueIn(*state, guess.band, guess.cellBitMask, 0); digit < 9 && fb.found < fb.limit;
	     digit = FB::nextValueIn(*state, guess.band, guess.cellBitMask, digit + 1)) {
		St *child = state + 1;
		std::memcpy(child, state, sizeof(St));
		FB::place(*child, digit, guess.band, guess.cellBitMask);
		walk(child, depth + 1);
	}
}

// as countSolutions(in, 2) does: the limit the benchmarks use
static void solveWith(std::string const &p) {
	fb.limit = 2;
	fb.found = 0;
	fb.solutionOut = solution;
	if (loadPuzzle(fb.stack[0], p)) walk(&fb.stack[0], 0);
}

int main(int argc, char **argv) {
	if (argc < 4) return 1;
	std::vector<std::string> puzzles = readPuzzles(argv[1]);
	std::string target = argv[2];
	size_t index = 0;
	while (index < puzzles.size() && puzzles[index] != target) index++;
	if (index == puzzles.size()) { fprintf(stderr, "puzzle not found\n"); return 1; }
	printf("{\"puzzle\": \"%s\", \"file\": \"%s\", \"index\": %zu,\n", target.c_str(), argv[1], index);
	wantGuess = wantSolved = wantPropagate = true;
	solveWith(target);
	wantGuess = wantSolved = wantPropagate = false;
	if (!haveGuess || !haveSolved || !havePropagate) { fprintf(stderr, "no guess or no solution\n"); return 1; }

	wantFallback = true;
	for (int a = 3; a < argc && !haveFallback; a++) {
		std::vector<std::string> others = readPuzzles(argv[a]);
		for (size_t i = 0; i < others.size() && !haveFallback; i++) {
			solveWith(others[i]);
			if (haveFallback) printf("\"puzzle\": \"%s\", \"file\": \"%s\", \"index\": %zu}\n", others[i].c_str(), argv[a], i);
		}
	}
	if (!haveFallback) { fprintf(stderr, "no fallback state found\n"); return 1; }
	printf("}\n");
	return 0;
}
