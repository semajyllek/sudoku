#!/usr/bin/env python3
"""
Throughput: puzzles per second when each of N processes solves its own share of a data set, for each solver.
All processes start at the same moment; the time is until the last one finishes. Median of 3 runs.

usage: throughput.py <throughput binary> <processes,processes,...> <data file>:<reps> ...
the solution limit is 2, or the LIMIT environment variable
"""
import statistics
import subprocess
import sys
import os
import time

LIMIT = os.environ.get('LIMIT', '2')

SOLVERS = ['fastband', 'tdoku', 'jsolve', 'kudoku']


def run(binary, solver, path, processes, reps):
    start = time.time_ns() + 700_000_000
    procs = [subprocess.Popen([binary, solver, path, str(i), str(processes), str(reps), str(start), LIMIT],
                              stdout=subprocess.PIPE, text=True) for i in range(processes)]
    ends, solved = [], 0
    for p in procs:
        end, count, _ = p.communicate()[0].split()
        ends.append(int(end))
        solved += int(count)
    return solved / ((max(ends) - start) / 1e9)


def main():
    binary = sys.argv[1]
    counts = [int(x) for x in sys.argv[2].split(',')]
    print(f'puzzles per second, limit {LIMIT}, each process solving its own share, median of 3 runs\n')
    print(f'{"data set":34} {"processes":>9} ' + ' '.join(f'{s:>11}' for s in SOLVERS))
    for arg in sys.argv[3:]:
        path, reps = arg.rsplit(':', 1)
        for n in counts:
            rates = [statistics.median(run(binary, s, path, n, int(reps)) for _ in range(3)) for s in SOLVERS]
            print(f'{path.split("/")[-1]:34} {n:9d} ' + ' '.join(f'{r:11.0f}' for r in rates), flush=True)


main()
