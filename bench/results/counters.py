# summarizes bench/counters.cpp logs: per machine, build, solver and data set, the mean over rounds of each measure
import glob, os, re, sys
from collections import defaultdict


def parse(path):
    # {(build, solver, set): {measure: [values over rounds]}}
    out = defaultdict(lambda: defaultdict(list))
    model, build, key, vals = '', '', None, {}

    def flush():
        if key and vals:
            for k, v in vals.items(): out[key][k].append(v)

    for line in open(path, errors='replace'):
        line = line.rstrip()
        if line.startswith('Model name:'): model = line.split(':', 1)[1].strip()
        m = re.match(r'=== COUNTERS (\S+) round', line)
        if m:
            flush(); build, key, vals = m.group(1), None, {}
            continue
        m = re.match(r'(fastband|tdoku|jsolve|kudoku) \S*/(puzzles\S+) limit', line)
        if m:
            key = (build, m.group(1), m.group(2)); vals = {}
            continue
        f = line.split()
        if key and len(f) >= 2 and not line.startswith('check'):
            name = ' '.join(f[:-2]) if f[0] == 'clock' else f[0]
            if f[0] == 'clock': vals['clock'] = (float(f[-2]) + float(f[-1])) / 2
            elif f[0] in ('cycles', 'seconds', 'GHz'): vals.setdefault(f[0], float(f[1]))  # first group
            elif re.match(r'^[\d.e+-]+$', f[1]): vals[f[0]] = float(f[1])
        if line.startswith('=== SOTA') or line.startswith('=== BENCH DONE'): flush(); key = None
    flush()
    return model, {k: {m: sum(v) / len(v) for m, v in d.items()} for k, d in out.items()}


def cycles(d):
    return d['cycles'] if 'cycles' in d else d['seconds'] * d['clock'] * 1e9


# the paper's tables: (label, vector extensions of the native build, log files); all on forum hardest 1106, limit 2
HARD = 'puzzles6_forum_hardest_1106'
MACHINES = [
    ('AMD EPYC 7B13 (Zen~3)', 'AVX2', ['gcp-c2d-zen3.txt', 'gcp-c2d-zen3-2.txt']),
    ('AMD EPYC 7763 (Zen~3)', 'AVX2', ['github-*-epyc-7763.txt']),
    ('AMD EPYC 9B14 (Zen~4)', 'AVX-512', ['gcp-c3d-zen4.txt']),
    ('AMD EPYC 9V74 (Zen~4)', 'AVX-512', ['github-*-epyc-9v74.txt']),
    ('AMD EPYC 9V45 (Zen~5)', 'AVX-512', ['github-*-epyc-9v45.txt']),
    ('Intel Xeon (Ice Lake)', 'AVX-512', ['gcp-n2-icl.txt']),
    ('Intel Xeon 8481C (Sapphire Rapids)', 'AVX-512', ['gcp-c3-spr.txt']),
    ('Intel Xeon 8573C (Emerald Rapids)', 'AVX-512', ['github-*-xeon-8573c.txt']),
    ('Intel Xeon 8581C (Emerald Rapids)', 'AVX-512', ['gcp-c4-emr-perf.txt', 'gcp-c4-emr-perf-2.txt']),
]
COUNTED = 'gcp-c4-emr-perf*.txt'  # instructions for the x86 builds come from here: same binary, same instructions


def machine(files, here):
    # mean cycles per (build, solver) over every file and round
    acc = defaultdict(list)
    for pattern in files:
        for f in glob.glob(os.path.join(here, 'counters', pattern)):
            for (build, solver, s), d in parse(f)[1].items():
                if s == HARD: acc[(build, solver)].append(cycles(d))
    return {k: sum(v) / len(v) for k, v in acc.items()}, sum(len(glob.glob(os.path.join(here, 'counters', p))) for p in files)


def paper(here):
    instr = defaultdict(list)
    miss = defaultdict(list)
    for f in glob.glob(os.path.join(here, 'counters', COUNTED)):
        for (build, solver, s), d in parse(f)[1].items():
            if s == HARD:
                instr[(build, solver)].append(d['instructions'])
                miss[(build, solver)].append(d['branch-misses'])
    instr = {k: sum(v) / len(v) for k, v in instr.items()}
    miss = {k: sum(v) / len(v) for k, v in miss.items()}
    k = lambda x: '%.0fk' % (x / 1000)
    print('% tab:cycles rows: cycles per puzzle (AVX2 build), IPC, FastBand/tdoku; then native build')
    for name, ext, files in MACHINES:
        c, n = machine(files, here)
        if not c: continue
        fv, tv = c[('build_v3', 'fastband')], c[('build_v3', 'tdoku')]
        fn, tn = c[('build', 'fastband')], c[('build', 'tdoku')]
        fi, ti = instr[('build_v3', 'fastband')], instr[('build_v3', 'tdoku')]
        print(f'{name} & {k(fv)} & {k(tv)} & {fi / fv:.2f} & {ti / tv:.2f} & {tv / fv:.2f} & {k(fn)} & {k(tn)} & {tn / fn:.2f} \\\\  % {n} logs')
    print('% instructions and branch mispredictions per puzzle on x86 (from the counted machine)')
    for b in ('build_v3', 'build'):
        print(b, ' '.join('%s %.0f (%.0f misses, MPKI %.2f)' % (s, instr[(b, s)], miss[(b, s)], 1000 * miss[(b, s)] / instr[(b, s)])
                          for s in ('fastband', 'tdoku', 'jsolve')))


if __name__ == '__main__':
    if sys.argv[1:] == ['paper']:
        paper(os.path.dirname(os.path.abspath(__file__)))
        sys.exit()
    for path in sys.argv[1:]:
        model, data = parse(path)
        print('##', os.path.basename(path), model)
        for (build, solver, s), d in sorted(data.items()):
            ghz = d.get('GHz', d.get('clock'))
            cyc = d.get('cycles', d['seconds'] * ghz * 1e9)
            extra = ''
            if 'instructions' in d:
                extra = ' instr %8.0f IPC %.2f br-miss %6.0f MPKI %5.2f' % (d['instructions'], d['instructions'] / cyc,
                        d['branch-misses'], 1000 * d['branch-misses'] / d['instructions'])
            print('%-9s %-9s %-28s s %.3e GHz %.2f cycles %8.0f%s' % (build, solver, s, d['seconds'], ghz, cyc, extra))
