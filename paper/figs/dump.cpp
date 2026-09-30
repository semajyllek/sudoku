// extracts real FastBandSolver states for the paper's before/after figures, as JSON; see make_figs.py
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
using Mask = uint32_t;
static FB fb;

static void dumpState(FILE *o, const char *name, St const &s) {
  fprintf(o, "\"%s\": {\"cands\": [", name);
  for (int cell = 0; cell < 81; cell++) { int m = 0; for (int d = 0; d < 9; d++) if (s.cells[d * 3 + cell / 27] >> (cell % 27) & 1) m |= 1 << d; fprintf(o, "%s%d", cell ? "," : "", m); }
  fprintf(o, "], \"unsolved\": [");
  for (int cell = 0; cell < 81; cell++) fprintf(o, "%s%d", cell ? "," : "", (s.unsolved[cell / 27] >> (cell % 27)) & 1);
  fprintf(o, "], \"openRows\": [");
  for (int d = 0; d < 9; d++) fprintf(o, "%s%d", d ? "," : "", s.openRows[d]);
  fprintf(o, "], \"cells\": [");
  for (int i = 0; i < 27; i++) fprintf(o, "%s%u", i ? "," : "", s.cells[i]);
  fprintf(o, "], \"checked\": [");
  for (int i = 0; i < 27; i++) fprintf(o, "%s%u", i ? "," : "", s.checked[i]);
  fprintf(o, "]}");
}
static int pc(Mask m) { return __builtin_popcount(m); }

// runs updateBand<B> through its own steps, capturing intermediate states; asserts the result equals the real call
template <int B> static bool traced(St &s, int d, St &afterBand, St &afterStack, St &afterSingles, Mask &newlyOut, bool &stackRan) {
  St real = s; bool okReal = fb.updateBand<B>(real, d);
  int i = d * 3 + B; Mask cells = s.cells[i], before = s.checked[i];
  int mr = FB::BOXES_OF_ROW[cells & 0777] | FB::BOXES_OF_ROW[(cells >> 9) & 0777] << 3 | FB::BOXES_OF_ROW[cells >> 18] << 6;
  cells &= FB::POSSIBLE_CELLS[mr];
  if (!cells) { if (okReal) { fprintf(stderr, "trace mismatch\n"); exit(1); } return false; }
  s.cells[i] = s.checked[i] = cells; afterBand = s;
  Mask columns = FB::presence(cells);
  unsigned single = FB::SINGLE_ROWS[FB::MATCHABLE[mr] | FB::ONE_COLUMN_BOXES[columns] << 9];
  unsigned open = (s.openRows[d] >> (B * 3)) & 07, newly = single & open;
  if (newly) { Mask placed = cells & FB::ROWS_CELLS[newly]; Mask own = s.cells[i]; for (int o = 0; o < 9; o++) s.cells[o * 3 + B] &= ~placed; s.cells[i] = own; s.unsolved[B] &= ~placed; s.openRows[d] &= ~(newly << (B * 3)); }
  afterSingles = s;
  stackRan = columns != FB::presence(before);
  if (stackRan) fb.stackRule(s, d);
  afterStack = s; newlyOut = newly;
  if (memcmp(&s, &real, sizeof(St)) || !okReal) { fprintf(stderr, "trace mismatch\n"); exit(1); }
  return true;
}

int main(int argc, char **argv) {
  std::ifstream f(argv[1]); std::string l; std::vector<std::string> ps;
  while (std::getline(f, l)) if (l.size() >= 81 && l[0] != '#') ps.push_back(l.substr(0, 81));
  int pick = atoi(argv[2]);
  // candidate search for a good UpdateBand example: small band-rule pruning, one row single, stack rule changing another band
  for (size_t pi = 0; pi < ps.size(); pi++) {
    if (pick >= 0 && (int)pi != pick) continue;
    const std::string &p = ps[pi];
    int g[9][9]; for (int k = 0; k < 81; k++) g[k/9][k%9] = p[k] == '.' ? 0 : p[k] - '0';
    St s; if (!fb.load(s, g)) continue;
    St loaded = s;
    bool found = false; St b0, b1, b2, b3; int fd = -1, fbnd = -1; Mask fnewly = 0; int call = 0;
    // emulate update(), tracing each call
    bool again = true; bool bad = false;
    while (again && !bad) { again = false;
      for (int d = 0; d < 9 && !bad; d++) for (int B = 0; B < 3 && !bad; B++) {
        int i = d * 3 + B; if (s.cells[i] == s.checked[i]) continue;
        St before = s, a1, a2, a3; Mask nw; bool sr; call++;
        bool ok = B == 0 ? traced<0>(s, d, a1, a2, a3, nw, sr) : B == 1 ? traced<1>(s, d, a1, a2, a3, nw, sr) : traced<2>(s, d, a1, a2, a3, nw, sr);
        if (!ok) { bad = true; break; }
        again = true;
        if (!found && call > 30) {
          int pruned = pc(before.cells[i] & ~a1.cells[i]);
          int otherBands = pc(a1.cells[d*3+(B+1)%3] & ~a2.cells[d*3+(B+1)%3]) + pc(a1.cells[d*3+(B+2)%3] & ~a2.cells[d*3+(B+2)%3]);
          int rs = pc(nw);
          int cleared = 0; for (int o = 0; o < 9; o++) if (o != d) cleared += pc(a1.cells[o*3+B] & ~a3.cells[o*3+B]);
          if (pruned >= 1 && pruned <= 4 && rs == 1 && sr && otherBands >= 1 && otherBands <= 4 && cleared >= 1 && cleared <= 4) {
            found = true; b0 = before; b1 = a1; b2 = a2; b3 = a3; fd = d; fbnd = B; fnewly = nw;
          }
        }
      }
    }
    if (bad || !found) continue;
    // propagate at root, and the first branch
    St root = loaded; Mask pairs[3]; int prog = fb.propagate(root, pairs);
    if (prog != 1) continue;
    FILE *o = stdout;
    fprintf(o, "{\"puzzle\": \"%s\", \"index\": %zu, \"digit\": %d, \"band\": %d, \"newly\": %u,\n", p.c_str(), pi, fd, fbnd, fnewly);
    dumpState(o, "ub_before", b0); fprintf(o, ",\n"); dumpState(o, "ub_after_bandrule", b1); fprintf(o, ",\n");
    dumpState(o, "ub_after_rowsingles", b3); fprintf(o, ",\n"); dumpState(o, "ub_after", b2); fprintf(o, ",\n");
    dumpState(o, "loaded", loaded); fprintf(o, ",\n"); dumpState(o, "root", root); fprintf(o, ",\n");
    // branch choice
    fprintf(o, "\"pairs\": [");
    bool first = true; int bestBand = -1, bestScore = -1; Mask bestCell = 0;
    for (int band = 0; band < 3; band++) for (Mask q = pairs[band]; q; q &= q - 1) { int idx = __builtin_ctz(q); int sc = FB::peerScore(root, band, idx);
      fprintf(o, "%s[%d,%d]", first ? "" : ",", band * 27 + idx, sc); first = false; if (sc > bestScore) bestScore = sc, bestBand = band, bestCell = q & -q; }
    int cell = bestBand * 27 + __builtin_ctz(bestCell); int d1 = 0; while (!(root.cells[d1*3+bestBand] & bestCell)) d1++; int d2 = d1 + 1; while (!(root.cells[d2*3+bestBand] & bestCell)) d2++;
    fprintf(o, "], \"branchCell\": %d, \"d1\": %d, \"d2\": %d,\n", cell, d1, d2);
    St c1 = root; FB::place(c1, d1, bestBand, bestCell); St c2 = root; FB::place(c2, d2, bestBand, bestCell);
    dumpState(o, "child1", c1); fprintf(o, ",\n"); dumpState(o, "child2", c2); fprintf(o, "}\n");
    return 0;
  }
  fprintf(stderr, "no example found\n"); return 1;
}
