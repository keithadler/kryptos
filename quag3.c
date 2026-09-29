/* General Quagmire III (one unknown alphabet A on both sides, periodic key) vs the cribs, exact.
 * C port of quag34.py's solver for the periods Python timed out on.
 *   vig:  A(C) - A(P) = k_r      beau: A(C) + A(P) = k_r
 * Variables: A(letter) for letters in the cribs (distinct values), k_r for residues.
 * Backtracking with propagation (two known -> third forced). A(first letter) = 0 by shift symmetry.
 * usage: quag3 KIND(vig|beau) PERIOD [ciphertext]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *K4 = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
#define NC 24
static int cp[NC], cl[NC], pl[NC];   /* crib pos, cipher letter, plain letter */
static int BEAU, PER;
/* variables 0..25 letters, 26.. residues */
static int val[26 + 64], isset[26 + 64], usedv[26];
static int trail[200], tp;
static long long nodes;

static int setv(int v, int x) {
    if (isset[v]) return val[v] == x;
    if (v < 26) { if (usedv[x]) return 0; usedv[x] = 1; }
    val[v] = x; isset[v] = 1; trail[tp++] = v;
    return 1;
}
static void undo(int t0) {
    while (tp > t0) { int v = trail[--tp]; if (v < 26) usedv[val[v]] = 0; isset[v] = 0; }
}
/* propagate all constraints to fixpoint */
static int propagate(void) {
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int j = 0; j < NC; j++) {
            int y = cl[j], x = pl[j], k = 26 + cp[j] % PER;
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
    for (int v = 0; v < 26 + PER; v++) {
        int present = 0;
        for (int j = 0; j < NC; j++) if (cl[j] == v || pl[j] == v || 26 + cp[j] % PER == v) { present = 1; break; }
        if (!present || isset[v]) continue;
        int s = 0;
        for (int j = 0; j < NC; j++) {
            int y = cl[j], x = pl[j], k = 26 + cp[j] % PER;
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
int main(int argc, char **argv) {
    BEAU = !strcmp(argv[1], "beau"); PER = atoi(argv[2]);
    if (argc > 3) K4 = argv[3];
    const char *w1 = "EASTNORTHEAST", *w2 = "BERLINCLOCK";
    int n = 0;
    for (int i = 0; w1[i]; i++, n++) { cp[n] = 21 + i; pl[n] = w1[i] - 'A'; cl[n] = K4[21 + i] - 'A'; }
    for (int i = 0; w2[i]; i++, n++) { cp[n] = 63 + i; pl[n] = w2[i] - 'A'; cl[n] = K4[63 + i] - 'A'; }
    int r = setv(pl[0], 0) && propagate() && bt();
    printf("QIII %s period %d: %s  (%lld nodes)\n", argv[1], PER, r ? "SAT" : "UNSAT", nodes);
    return 0;
}
