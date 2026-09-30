#!/bin/bash
# counters for the paper on Apple Silicon: sudo bash bench/m4counters.sh > bench/results/m4-counters.txt
cd "$(dirname "$0")/.."
D=build/sota_data/data
echo "=== MACHINE"
echo "Model name: $(sysctl -n machdep.cpu.brand_string)"
for round in 1 2; do
  for solver in fastband tdoku jsolve; do
    echo "=== COUNTERS build round $round"
    ./build/sota/m4counters $solver $D/puzzles6_forum_hardest_1106 20
    echo "=== COUNTERS build round $round"
    ./build/sota/m4counters $solver $D/puzzles2_17_clue 5
  done
done
echo "=== BENCH DONE"
