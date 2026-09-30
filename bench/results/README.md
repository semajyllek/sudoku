### x86 results

raw output of `make sota` on rented x86 machines, used for the paper's x86 tables (section "measured on x86").
`python3 tables.py` summarizes every log; `python3 tables.py paper` prints the paper's table rows.

- `github-run1-*`: first run of `.github/workflows/x86.yml` (run 36682900287), 2 significant figures. not used in the paper
- `github-run2-*`: second run (36689862537), 3 significant figures, with the processor in the name
- `gcp-c3-spr.txt`, `gcp-n2-icl.txt`: google cloud spot machines, sapphire rapids (c3-standard-4) and ice lake
  (n2-standard-4), limits 2 and 1
- `gcp-avx512-*.txt`: tdoku built with `-march=native` and with `-march=native -mno-avx512f`, alternating, two rounds,
  limit 2, on sapphire rapids and zen 4 (c3d-standard-4). the ice lake machine was reclaimed before it finished

every machine: ubuntu, clang, `-O3 -march=native`, median of 5 interleaved runs, 4 virtual cpus. the `avx flags` line
misses flags with an underscore (such as `avx512_vpopcntdq`).

### counters

`counters/`: output of `bench/counters.cpp` (per-puzzle cycles, instructions, branch misses; clock estimate) for the
paper's section "why: instructions and cycles". each solver is built twice: `build` (`-march=native`) and `build_v3`
(`-march=x86-64-v3`, the same binary on every x86 machine). two rounds each. `python3 counters.py counters/*.txt`
summarizes them; `python3 counters.py paper` prints the paper's table rows.

- `gcp-c4-emr-perf*.txt`: google cloud c4 (emerald rapids), the only machine type with hardware counters
  (`--performance-monitoring-unit=standard`). its instruction counts stand for every x86 machine
- `gcp-*.txt`, `github-*.txt`: no counters; cycles are time times the clock from a register-add chain
- `gcp-c3d-zen4.txt` used the first clock estimate (an add-immediate chain). it is right on amd (zen 3 gave 3.46 and
  3.47 ghz with the old and new chains) but not on intel since golden cove, which folds those chains (about 20 ghz on
  c4); every intel log here uses the register-add chain
- the m4's counts come from `bench/m4counters.cpp` through kperf (`sudo bash bench/m4counters.sh`)
