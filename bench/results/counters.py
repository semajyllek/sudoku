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


if __name__ == '__main__':
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
