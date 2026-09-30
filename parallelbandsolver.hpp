/*
ParallelBandSolver: FastBandSolver's search spread over several threads, for one puzzle at a time.

Same interface as FastBandSolver, plus the number of threads. The deductions, the choice of guess cell and the counting
are FastBandSolver's; see fastbandsolver.hpp. What this adds is who explores which branch.

How the work is shared. With a limit of 2 on a puzzle with one solution, the whole search tree has to be explored, and
its branches are independent. The calling thread searches depth first as FastBandSolver does. At a two-candidate
branch it may hand the second branch, as a copy of the state, to a shared queue instead of exploring it later itself;
idle worker threads take branches from the queue and search them the same way, handing out branches in turn.

What keeps it from being slower than one thread:
- a puzzle is searched by the calling thread alone until it has taken shareAfterNodes nodes of search. Easy puzzles
  never reach that, so they never touch the other threads
- only branches fewer than maxShareDepth guesses deep are handed out, and only when some worker is idle: deep
  branches are too small to be worth moving to another core
- idle workers spin only while a puzzle is being shared, then sleep (after a short grace period, in case the next
  puzzle is hard too), so they don't slow the calling thread down between hard puzzles. Two flags: sharing says
  whether the current puzzle may hand out branches; active says whether workers should be spinning for them
- the queue uses a try-lock: a thread that finds it busy keeps spinning instead of sleeping in the kernel, which costs
  more than a whole node of search

A solution counter shared by all threads stops the search once the limit is reached. Results are exactly
FastBandSolver's: the same tree is explored, split between threads.
*/
#pragma once
#include "fastbandsolver.hpp"
#include <atomic>
#include <deque>
#include <memory>
#include <thread>
#include <vector>
#ifdef __APPLE__
#include <pthread.h>
#include <sys/qos.h>
#endif

class ParallelBandSolver {
	public:
		// threads: the calling thread plus threads - 1 workers
		explicit ParallelBandSolver(int threads = 4);
		~ParallelBandSolver();
		ParallelBandSolver(ParallelBandSolver const &) = delete;
		ParallelBandSolver &operator=(ParallelBandSolver const &) = delete;

		bool solve(const int in[9][9], int out[9][9]);
		int countSolutions(const int in[9][9], int limit = 2);
		bool hasUniqueSolution(const int in[9][9]) { return countSolutions(in, 2) == 1; }

		// binary decisions made by the last call, over all threads (as FastBandSolver counts them)
		long long guesses = 0;
		// branches handed to other threads in the last call
		long long shared = 0;

		// tuning, see the comment at the top
		int shareAfterNodes = 16;
		int maxShareDepth = 8;
		int graceSpins = 20000;

	private:
		using FB = FastBandSolver;
		using State = FB::State;
		using Mask = FB::Mask;

		struct Task {
			State state;
			int depth;
		};

		// per thread: a stack of states, one per depth, and counters
		struct Worker {
			State stack[82];
			long long nodes = 0;
			long long guesses = 0;
		};

		int limit = 0;
		int *solutionOut = nullptr;
		std::atomic<int> found{0};
		std::atomic<bool> stop{false};
		std::atomic<bool> sharing{false};   // this puzzle may hand branches to workers
		std::atomic<int> active{0};         // 1 while workers should look for branches, 0 while they may sleep
		std::atomic<bool> quit{false};
		std::atomic<int> pending{0};        // branches handed out and not finished
		std::atomic<int> queued{0};
		std::atomic<int> hungry{0};         // workers looking for a branch
		std::atomic<long long> guessTotal{0};
		std::atomic<long long> sharedTotal{0};
		std::atomic_flag lock = ATOMIC_FLAG_INIT;
		std::deque<Task> queue;
		std::vector<std::thread> threads;
		std::unique_ptr<Worker> caller = std::make_unique<Worker>();
		// FastBandSolver's load and propagate only touch the state passed to them, so one instance serves every thread.
		// (A FastBandSolver holds 82 states itself, too big to create at every node.)
		std::unique_ptr<FB> engine = std::make_unique<FB>();

		int run(const int in[9][9], int maxSolutions, int *solution);
		void search(Worker &w, State *s, int depth);
		void record(State const &s);
		bool pop(Task &out);
		void push(State const &s, int depth);
		void workerLoop();

		static void pause() {
#if defined(__aarch64__)
			__builtin_arm_isb(15);
#elif defined(__x86_64__)
			__builtin_ia32_pause();
#endif
		}
		static void preferFastCores() {
#ifdef __APPLE__
			pthread_set_qos_class_self_np(QOS_CLASS_USER_INTERACTIVE, 0);
#endif
		}
};


inline ParallelBandSolver::ParallelBandSolver(int threadCount) {
	for (int t = 1; t < threadCount; t++) threads.emplace_back([this] { workerLoop(); });
}


inline ParallelBandSolver::~ParallelBandSolver() {
	quit.store(true);
	active.store(1);
	active.notify_all();
	for (auto &t : threads) t.join();
}


inline bool ParallelBandSolver::solve(const int in[9][9], int out[9][9]) {
	int solution[81];
	if (run(in, 1, solution) == 0) return false;
	for (int cell = 0; cell < 81; cell++) out[cell / 9][cell % 9] = solution[cell];
	return true;
}


inline int ParallelBandSolver::countSolutions(const int in[9][9], int maxSolutions) {
	return run(in, maxSolutions, nullptr);
}


inline int ParallelBandSolver::run(const int in[9][9], int maxSolutions, int *solution) {
	limit = maxSolutions;
	solutionOut = solution;
	found.store(0);
	stop.store(false);
	sharing.store(false);
	guessTotal.store(0);
	sharedTotal.store(0);
	Worker &w = *caller;
	w.nodes = w.guesses = 0;
	if (engine->load(w.stack[0], in)) {
		search(w, &w.stack[0], 0);
		// help with the branches handed out until all are done
		Task task;
		while (pending.load(std::memory_order_acquire) > 0) {
			if (pop(task)) {
				w.stack[0] = task.state;
				search(w, &w.stack[0], task.depth);
				pending.fetch_sub(1, std::memory_order_acq_rel);
			} else {
				pause();
			}
		}
	}
	// every branch handed out is finished (pending is 0), so no worker is still searching. A worker may still be
	// leaving its wait for a branch, with hungry briefly counting it into the next call; then a branch handed out at
	// the start of that call waits for the caller to take it itself, which is harmless
	active.store(0);
	guesses = guessTotal.load() + w.guesses;
	shared = sharedTotal.load();
	int n = found.load();
	return n < limit ? n : limit;
}


inline bool ParallelBandSolver::pop(Task &out) {
	if (queued.load(std::memory_order_acquire) == 0) return false;
	if (lock.test_and_set(std::memory_order_acquire)) return false;  // someone else is at the queue: try again later
	bool got = !queue.empty();
	if (got) {
		out = queue.front();
		queue.pop_front();
		queued.fetch_sub(1, std::memory_order_release);
	}
	lock.clear(std::memory_order_release);
	return got;
}


inline void ParallelBandSolver::push(State const &s, int depth) {
	pending.fetch_add(1, std::memory_order_relaxed);
	while (lock.test_and_set(std::memory_order_acquire)) pause();
	queue.push_back(Task{s, depth});
	queued.fetch_add(1, std::memory_order_release);
	lock.clear(std::memory_order_release);
	sharedTotal.fetch_add(1, std::memory_order_relaxed);
}


inline void ParallelBandSolver::record(State const &s) {
	int index = found.fetch_add(1);
	if (index + 1 >= limit) stop.store(true);
	if (index == 0 && solutionOut) FB::writeSolution(s, solutionOut);
}


// FastBandSolver::search, with the option of handing the second branch to another thread
inline void ParallelBandSolver::search(Worker &w, State *s, int depth) {
	if (stop.load(std::memory_order_relaxed)) return;
	w.nodes++;
	if (&w == caller.get() && !sharing.load(std::memory_order_relaxed) && w.nodes >= shareAfterNodes && !threads.empty()) {
		// a hard puzzle: wake the workers
		sharing.store(true);
		active.store(1);
		active.notify_all();
	}
	Mask pairs[3];
	int progress = engine->propagate(*s, pairs);
	if (progress == 0) return;
	if (progress == 2) {
		record(*s);
		return;
	}
	int bestBand = -1, bestScore = -1;
	Mask bestCell = 0;
	for (int band = 0; band < 3; band++) {
		for (Mask p = pairs[band]; p; p &= p - 1) {
			int score = FB::peerScore(*s, band, std::countr_zero(p));
			if (score > bestScore) bestScore = score, bestBand = band, bestCell = p & -p;
		}
	}
	if (bestBand >= 0) {
		int first = 0;
		while (!(s->cells[first * 3 + bestBand] & bestCell)) first++;
		int second = first + 1;
		while (!(s->cells[second * 3 + bestBand] & bestCell)) second++;
		w.guesses++;
		State *child = s + 1;
		std::memcpy(child, s, sizeof(State));
		FB::place(*child, first, bestBand, bestCell);
		FB::place(*s, second, bestBand, bestCell);
		if (depth < maxShareDepth && sharing.load(std::memory_order_relaxed) &&
		    hungry.load(std::memory_order_relaxed) > queued.load(std::memory_order_relaxed)) {
			push(*s, depth + 1);
			search(w, child, depth + 1);
			return;
		}
		search(w, child, depth + 1);
		search(w, s, depth + 1);
		return;
	}
	// no cell with two candidates: every candidate of a cell with the fewest, searched here
	int fewest = 10;
	for (int band = 0; band < 3; band++) {
		for (Mask u = s->unsolved[band]; u; u &= u - 1) {
			int index = std::countr_zero(u), n = 0;
			for (int digit = 0; digit < 9; digit++) n += (s->cells[digit * 3 + band] >> index) & 1;
			if (n > fewest) continue;
			int score = FB::peerScore(*s, band, index);
			if (n < fewest || score > bestScore) fewest = n, bestScore = score, bestBand = band, bestCell = u & -u;
		}
	}
	w.guesses += fewest - 1;
	for (int digit = 0; digit < 9; digit++) {
		if (stop.load(std::memory_order_relaxed)) return;
		if (!(s->cells[digit * 3 + bestBand] & bestCell)) continue;
		State *child = s + 1;
		std::memcpy(child, s, sizeof(State));
		FB::place(*child, digit, bestBand, bestCell);
		search(w, child, depth + 1);
	}
}


inline void ParallelBandSolver::workerLoop() {
	preferFastCores();
	auto w = std::make_unique<Worker>();
	Task task;
	while (!quit.load(std::memory_order_relaxed)) {
		if (!active.load(std::memory_order_acquire)) {
			// spin a little in case the next puzzle is hard too, then sleep until woken
			int spins = 0;
			while (!active.load(std::memory_order_acquire) && spins++ < graceSpins) pause();
			if (!active.load(std::memory_order_acquire)) active.wait(0);
			continue;
		}
		hungry.fetch_add(1, std::memory_order_relaxed);
		bool got = false;
		while (active.load(std::memory_order_acquire) && !quit.load(std::memory_order_relaxed) && !(got = pop(task))) pause();
		hungry.fetch_sub(1, std::memory_order_relaxed);
		if (!got) continue;
		w->nodes = w->guesses = 0;
		w->stack[0] = task.state;
		search(*w, &w->stack[0], task.depth);
		guessTotal.fetch_add(w->guesses, std::memory_order_relaxed);
		pending.fetch_sub(1, std::memory_order_acq_rel);
	}
}
