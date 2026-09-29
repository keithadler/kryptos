/* Columnar transposition x periodic tableau substitution, exhaustive for widths 2..MAXW.
 *
 * sigma(i) = ciphertext position of plaintext letter i. Built by writing 97 letters row-wise into
 * width w and reading columns in a keyed order, each column top-down or bottom-up; both sigma and
 * its inverse are tried (we don't know which way Sanborn ran it).
 *
 * order A: C = T(S(P))  key index = i         (substitute, then transpose)
 * order B: C = S(T(P))  key index = sigma(i)  (transpose, then substitute)
 * Forced key value at crib i: vig k = y(C[sigma i]) - x(P_i);  beau k = y(C[sigma i]) + x(P_i).
 * A candidate survives a period p if every pair of cribs sharing a key index mod p forces the same
 * value. We print survivors with at least MINCHK such checks (random survival odds 26^-checks).
 *
 * usage: trans MAXW [MINCHK]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 97
static const char *K4 = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
static const char *AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static const char *KA = "KRYPTOSABCDEFGHIJLMNQUVWXZ";
static int NC; static int cpos[32]; static char cpt[32];
static int ai[2][26];            /* ai[alpha][letter] = index */
static int minchk = 8;
static long long tested = 0, survivors = 0;
static long long hist[40];

static void add_crib(int start1, const char *w) {
    for (int k = 0; w[k]; k++) { cpos[NC] = start1 - 1 + k; cpt[NC] = w[k]; NC++; }
}

static void check(const int *sigma, int w, const int *ord, int updown, int inv) {
    for (int fam = 0; fam < 8; fam++) {
        int beau = fam >> 2, xa = (fam >> 1) & 1, ya = fam & 1;
        int v[32];
        for (int j = 0; j < NC; j++) {
            int c = ai[ya][K4[sigma[cpos[j]]] - 'A'], p = ai[xa][cpt[j] - 'A'];
            v[j] = beau ? (c + p) % 26 : (c - p + 26) % 26;
        }
        for (int orderB = 0; orderB < 2; orderB++) {
            int kidx[32];
            for (int j = 0; j < NC; j++) kidx[j] = orderB ? sigma[cpos[j]] : cpos[j];
            for (int per = 1; per <= 26; per++) {
                int seen[26], ok = 1, checks = 0;
                memset(seen, -1, sizeof seen);
                for (int j = 0; j < NC && ok; j++) {
                    int r = kidx[j] % per;
                    if (seen[r] < 0) seen[r] = v[j];
                    else { checks++; if (seen[r] != v[j]) ok = 0; }
                }
                tested++;
                if (ok) {
                    hist[checks]++;
                    if (checks >= minchk) {
                        survivors++;
                        printf("SURVIVOR w=%d ord=", w);
                        for (int k = 0; k < w; k++) printf("%d%s", ord[k], k + 1 < w ? "," : "");
                        printf(" updown=%x inv=%d fam=%s-P%s-C%s order=%c per=%d checks=%d\n", updown, inv,
                               beau ? "beau" : "vig", xa ? "KA" : "AZ", ya ? "KA" : "AZ", orderB ? 'B' : 'A', per, checks);
                    }
                }
            }
        }
    }
}

static void build_and_check(int w, const int *ord, int updown) {
    int sigma[N], sinv[N], t = 0;
    int rows = (N + w - 1) / w;
    for (int k = 0; k < w; k++) {
        int col = ord[k], up = (updown >> k) & 1;
        int nrow = (col < N % w || N % w == 0) ? rows : rows - 1;
        for (int rr = 0; rr < nrow; rr++) {
            int r = up ? nrow - 1 - rr : rr;
            sigma[r * w + col] = t++;
        }
    }
    for (int i = 0; i < N; i++) sinv[sigma[i]] = i;
    check(sigma, w, ord, updown, 0);
    check(sinv, w, ord, updown, 1);
}

static int next_perm(int *a, int n) {
    int i = n - 2;
    while (i >= 0 && a[i] >= a[i + 1]) i--;
    if (i < 0) return 0;
    int j = n - 1;
    while (a[j] <= a[i]) j--;
    int t = a[i]; a[i] = a[j]; a[j] = t;
    for (int l = i + 1, r = n - 1; l < r; l++, r--) { t = a[l]; a[l] = a[r]; a[r] = t; }
    return 1;
}

/* One rotation step: write row-wise in width w, read columns (cw: left->right, each bottom->top;
 * ccw: right->left, each top->bottom). Short last row handled like the columnar case. */
static void rotation(int w, int ccw, int *sig) {
    int rows = (N + w - 1) / w, t = 0;
    for (int k = 0; k < w; k++) {
        int col = ccw ? w - 1 - k : k;
        int nrow = (col < N % w || N % w == 0) ? rows : rows - 1;
        for (int rr = 0; rr < nrow; rr++) {
            int r = ccw ? rr : nrow - 1 - rr;
            sig[r * w + col] = t++;
        }
    }
}

static int rot_mode(void) {
    int s1[N], s2[N], sig[N], sinv[N], ord[2];
    for (int w1 = 2; w1 < N; w1++)
        for (int w2 = 1; w2 < N; w2++)       /* w2 == 1: single rotation */
            for (int r = 0; r < 4; r++) {
                rotation(w1, r & 1, s1);
                if (w2 == 1) { if (r & 2) continue; for (int i = 0; i < N; i++) sig[i] = s1[i]; }
                else { rotation(w2, (r >> 1) & 1, s2); for (int i = 0; i < N; i++) sig[i] = s2[s1[i]]; }
                for (int i = 0; i < N; i++) sinv[sig[i]] = i;
                ord[0] = w1; ord[1] = w2;
                check(sig, 2, ord, r, 0);
                check(sinv, 2, ord, r, 1);
            }
    fprintf(stderr, "rotation mode: tested %lld combos, survivors %lld\n", tested, survivors);
    for (int c = 0; c < 40; c++) if (hist[c]) fprintf(stderr, "  checks=%2d: %lld\n", c, hist[c]);
    return 0;
}

/* Orders from stdin, one per line: "label w o0,o1,...". Used for keyword-derived orders at
 * widths too large to enumerate. */
static int ord_mode(void) {
    char line[4096];
    long long n = 0;
    while (fgets(line, sizeof line, stdin)) {
        char label[256]; int w, pos = 0, ord[64];
        if (sscanf(line, "%255s %d %n", label, &w, &pos) < 2 || w < 2 || w > 64) continue;
        char *p = line + pos;
        for (int k = 0; k < w; k++) { ord[k] = (int)strtol(p, &p, 10); if (*p == ',') p++; }
        long long before = survivors;
        build_and_check(w, ord, 0);
        build_and_check(w, ord, (int)((1ULL << (w < 31 ? w : 31)) - 1));
        build_and_check(w, ord, 0x55555555 & (int)((1ULL << (w < 31 ? w : 31)) - 1));
        if (survivors > before) printf("  ^ keyword %s\n", label);
        n++;
    }
    fprintf(stderr, "ord mode: %lld orders, tested %lld combos, survivors %lld\n", n, tested, survivors);
    for (int c = 0; c < 40; c++) if (hist[c]) fprintf(stderr, "  checks=%2d: %lld\n", c, hist[c]);
    return 0;
}

int main(int argc, char **argv) {
    int maxw = argc > 1 ? atoi(argv[1]) : 8;  /* or "rot" for K3-style double rotation */
    if (argc > 2) minchk = atoi(argv[2]);
    if (argc > 3) K4 = argv[3]; /* planted-ciphertext self-test */
    add_crib(22, "EASTNORTHEAST");
    add_crib(64, "BERLINCLOCK");
    for (int i = 0; i < 26; i++) { ai[0][AZ[i] - 'A'] = i; ai[1][KA[i] - 'A'] = i; }
    if (argc > 1 && !strcmp(argv[1], "rot")) return rot_mode();
    if (argc > 1 && !strcmp(argv[1], "ord")) return ord_mode();
    for (int w = 2; w <= maxw; w++) {
        int ord[16];
        for (int k = 0; k < w; k++) ord[k] = k;
        long long before = survivors;
        do {
            build_and_check(w, ord, 0);          /* all columns top-down */
            build_and_check(w, ord, (1 << w) - 1); /* all bottom-up (K3-style rotation) */
            build_and_check(w, ord, 0x5555 & ((1 << w) - 1)); /* boustrophedon, odd columns up */
        } while (next_perm(ord, w));
        fprintf(stderr, "width %d done, survivors so far %lld (+%lld)\n", w, survivors, survivors - before);
    }
    fprintf(stderr, "tested %lld (perm x dir x family x order x period) combos\n", tested);
    fprintf(stderr, "histogram of constraint counts among consistent combos:\n");
    for (int c = 0; c < 40; c++) if (hist[c]) fprintf(stderr, "  checks=%2d: %lld\n", c, hist[c]);
    return 0;
}
