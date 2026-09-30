# prints the paper's x86 tables (LaTeX rows) from the logs in this directory
import glob, os, re, sys

SETS = ['puzzles2_17_clue', 'puzzles3_magictour_top1465', 'puzzles6_forum_hardest_1106',
        'puzzles5_forum_hardest_1905_11+', 'puzzles0_kaggle']


def blocks(text):
    # {(label, limit): {set: {solver: seconds}}}; label is the === header before each table
    out, label, cols, limit = {}, '', None, None
    for line in text.splitlines():
        if line.startswith('=== '): label = line[4:].strip()
        m = re.match(r'seconds per puzzle, limit (\d+)', line)
        if m: limit = int(m.group(1))
        if line.startswith('data set'): cols = line.split()[3:]
        f = line.split()
        if cols and f and f[0] in SETS:
            out.setdefault((label, limit), {})[f[0]] = dict(zip(cols, map(float, f[2:2 + len(cols)])))
    return out


def load(path):
    if os.path.isdir(path):
        return blocks('\n'.join(open(p).read() for p in sorted(glob.glob(path + '/sota_limit*.txt'))))
    return blocks(open(path).read())


def ratio(t): return t['tdoku'] / t['fastbandsolver']


def summary():
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(here + '/*')):
        if path.endswith('.py') or path.endswith('.md'): continue
        for (label, limit), sets in load(path).items():
            print(os.path.basename(path), label, 'limit', limit, ' '.join('%.2f' % ratio(sets[s]) for s in SETS if s in sets),
                  '| 1106 s:', ' '.join('%s %.2e' % (k[:5], v) for k, v in sets.get(SETS[2], {}).items() if '/' not in k))


# the paper's tables: (label, vector extensions, source file, block label), limit 2 unless noted
MACHINES = [
    ('AMD EPYC 7763 (Zen 3), clang 14', 'AVX2', 'github-run2-ubuntu-22.04-1-epyc-7763', ''),
    ('AMD EPYC 7763 (Zen 3), clang 18', 'AVX2', 'github-run2-ubuntu-24.04-2-epyc-7763', ''),
    ('AMD EPYC 9V74 (Zen 4)', 'AVX-512', 'github-run2-ubuntu-24.04-1-epyc-9v74', ''),
    ('AMD EPYC 9B14 (Zen 4)', 'AVX-512', 'gcp-avx512-c3d-zen4.txt', 'NATIVE round 1'),
    ('Intel Xeon 8370C (Ice Lake)', 'AVX-512', 'github-run2-ubuntu-22.04-2-xeon-8370c', ''),
    ('Intel Xeon (Ice Lake)', 'AVX-512', 'gcp-n2-icl.txt', 'LIMIT2'),
    ('Intel Xeon 8481C (Sapphire Rapids)', 'AVX-512', 'gcp-c3-spr.txt', 'LIMIT2'),
]
LIMIT1 = {'gcp-n2-icl.txt': 'LIMIT1', 'gcp-c3-spr.txt': 'LIMIT1'}


def num(x): return '\\num{%.2e}' % x


def paper_tables():
    here = os.path.dirname(os.path.abspath(__file__))
    print('% tab:x86 rows')
    for name, ext, f, lab in MACHINES:
        b = load(os.path.join(here, f))
        two = b[(lab, 2)]
        one = b.get((LIMIT1.get(f, lab), 1))
        cells = ['%.2f' % ratio(two[s]) for s in SETS]
        cells.append('%.2f' % ratio(one[SETS[2]]) if one else '--')
        print(f'{name} & {ext} & ' + ' & '.join(cells) + ' \\\\')
    print('% tab:x86times rows (forum hardest 1106, limit 2)')
    for name, ext, f, lab in MACHINES:
        t = load(os.path.join(here, f))[(lab, 2)][SETS[2]]
        print(f'{name} & ' + ' & '.join(num(t[k]) for k in ('fastbandsolver', 'tdoku', 'jsolve', 'kudoku')) + ' \\\\')

    print('% tab:avx512 rows (two rounds averaged)')
    for name, f in (('Intel Xeon 8481C (Sapphire Rapids)', 'gcp-avx512-c3-spr.txt'), ('AMD EPYC 9B14 (Zen 4)', 'gcp-avx512-c3d-zen4.txt')):
        b = load(os.path.join(here, f))
        def mean(kind, s, solver):
            v = [b[k][s][solver] for k in b if k[0].startswith(kind)]
            return sum(v) / len(v)
        slow = [mean('NOAVX512', s, 'tdoku') / mean('NATIVE', s, 'tdoku') for s in SETS]
        hard = SETS[1:4]
        withr = [mean('NATIVE', s, 'tdoku') / mean('NATIVE', s, 'fastbandsolver') for s in hard]
        without = [mean('NOAVX512', s, 'tdoku') / mean('NOAVX512', s, 'fastbandsolver') for s in hard]
        print(f'{name} & {min(slow):.2f}--{max(slow):.2f} & {min(withr):.2f}--{max(withr):.2f} & {min(without):.2f}--{max(without):.2f} \\\\')


if __name__ == '__main__':
    paper_tables() if sys.argv[1:] == ['paper'] else summary()
