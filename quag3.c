/* General Quagmire III / IV vs the cribs, exact. C port of quag34.py's solver.
 *   QIII (one unknown alphabet A):  vig A(C) - A(P) = k_r     beau A(C) + A(P) = k_r
 *   QIV  (plaintext alphabet X, ciphertext alphabet Y, both unknown):  vig Y(C) - X(P) = k_r
 * Variables: alphabet positions of crib letters (distinct within an alphabet), key residues.
 * Backtracking with propagation (two known -> third forced). One letter per alphabet pinned to 0.
 * usage: quag3 KIND(vig|beau|vig4) PERIOD [ciphertext]      env KGUESS="61:THE" adds guessed cribs
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *K4 = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
#define MAXC 97
static int NC, cp[MAXC], cl[MAXC], pl[MAXC];   /* crib pos, cipher var, plain var */
static int BEAU, PER, TWO;
/* variables: 0..25 plaintext-side letters, 26..51 ciphertext-side letters (QIV; QIII uses 0..25
 * for both), KB.. residues */
#define KB 52
static int val[KB + 128], isset[KB + 128], usedv[2][26];
static int trail[400], tp;
static long long nodes;

static int setv(int v, int x) {
    if (isset[v]) return val[v] == x;
    if (v < KB) { int a = v >= 26; if (usedv[a][x]) return 0; usedv[a][x] = 1; }
    val[v] = x; isset[v] = 1; trail[tp++] = v;
    return 1;
}
static void undo(int t0) {
    while (tp > t0) { int v = trail[--tp]; if (v < KB) usedv[v >= 26][val[v]] = 0; isset[v] = 0; }
}
/* propagate all constraints to fixpoint */
static int propagate(void) {
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int j = 0; j < NC; j++) {
            int y = cl[j], x = pl[j], k = KB + cp[j] % PER;
            int sy = isset[y], sx = isset[x], sk = isset[k];
            if (sy + sx + sk == 3) {
                int lhs = BEAU ? (val[y] + val[x]) % 26 : (val[y] - val[x] + 26) % 26;
                if (lhs != val[k]) return 0;
            } else if (sy + sx + sk == 2) {
                int ok;
                if (!sk) ok = setv(k, BEAU ? (val[y] + val[x]) % 26 : (val[y] - val[x] + 26) % 26);
                else if (!sy) ok = setv(y, BEAU ? (val[k] - val[x] + 26) % 26 : (val[k] + val[x]) % 26);
                else ok = setv(x, BEAU ? (val[k] - val[y] + 26) % 26 : (val[y] - val[k] + 26) % 26);
                if (!ok) return 0;
                changed = 1;
            } else if (y == x && !BEAU && !sk) {     /* same letter both sides: vig shift is 0 */
                if (!setv(k, 0)) return 0;
                changed = 1;
            } else if (y == x && BEAU && sy && !sk) { /* beau: k = 2 A(letter) */
                if (!setv(k, (2 * val[y]) % 26)) return 0;
                changed = 1;
            }
        }
    }
    return 1;
}
static int pick(void) {
    int best = -1, bs = -1;
    for (int v = 0; v < KB + PER; v++) {
        int present = 0;
        for (int j = 0; j < NC; j++) if (cl[j] == v || pl[j] == v || KB + cp[j] % PER == v) { present = 1; break; }
        if (!present || isset[v]) continue;
        int s = 0;
        for (int j = 0; j < NC; j++) {
            int y = cl[j], x = pl[j], k = KB + cp[j] % PER;
            if (y == v || x == v || k == v) s += isset[y] + isset[x] + isset[k];
        }
        if (s > bs) { bs = s; best = v; }
    }
    return best;
}
static int bt(void) {
    nodes++;
    int v = pick();
    if (v < 0) return 1;
    for (int x = 0; x < 26; x++) {
        int t0 = tp;
        if (setv(v, x) && propagate() && bt()) return 1;
        undo(t0);
    }
    return 0;
}
static void add(int start1, const char *w) {
    for (int i = 0; w[i]; i++) {
        int p = start1 - 1 + i;
        for (int j = 0; j < NC; j++) if (cp[j] == p) { if (pl[j] != w[i] - 'A') { fprintf(stderr, "guess contradicts crib\n"); exit(2); } goto next; }
        cp[NC] = p; pl[NC] = w[i] - 'A'; cl[NC] = K4[p] - 'A' + (TWO ? 26 : 0); NC++;
        next:;
    }
}
int main(int argc, char **argv) {
    BEAU = !strcmp(argv[1], "beau"); TWO = !strcmp(argv[1], "vig4"); PER = atoi(argv[2]);
    if (argc > 3) K4 = argv[3];
    add(22, "EASTNORTHEAST"); add(64, "BERLINCLOCK");
    char *g = getenv("KGUESS");
    if (g) { char buf[512]; strncpy(buf, g, 511); buf[511] = 0;
        for (char *t = strtok(buf, ","); t; t = strtok(0, ",")) { char *c = strchr(t, ':'); *c = 0; add(atoi(t), c + 1); } }
    int r = setv(pl[0], 0) && (!TWO || setv(cl[0], 0)) && propagate() && bt();
    printf("%s %s period %d cribs %d: %s  (%lld nodes)\n", TWO ? "QIV" : "QIII", argv[1], PER, NC, r ? "SAT" : "UNSAT", nodes);
    return 0;
}
