/* Simulated annealing for Quagmire III/IV with KEYWORD alphabets and a repeating key, scored by
 * English quadgrams plus clue agreement.
 *
 * sa.c lets the alphabets be any of 26!, which is too much freedom for 97 letters when both are
 * unknown. Here each alphabet is a keyword followed by the remaining letters in A-Z order, the way
 * KRYPTOSABCDEFGHIJLMNQUVWXZ is built. The keyword is any string of up to MAXKW different letters,
 * not a dictionary word, so misspellings, names and phrases are covered.
 *
 *   C_i = Y[ (X(P_i) + k[i mod p]) mod 26 ]        (Beaufort form, env BEAU=1: Y[ (k - X(P_i)) mod 26 ])
 * mode 4: X and Y each a free keyword alphabet.  mode 3: X = Y, one free keyword alphabet.
 * mode 1: X free, Y = KRYPTOS.  mode 5: X free, Y = A-Z.  mode 2: X = A-Z, Y free.  mode 6: X = KRYPTOS, Y free.
 * The key is not searched where the clues give it: for each key letter the first clue letter on
 * it fixes the shift, given the two alphabets. Only key letters no clue reaches are free.
 * Moves: replace, swap, insert or delete a keyword letter; change one free key shift.
 * Score = sum of quadgram log-probs + CRIBW * (number of clue letters reproduced).
 *
 * usage: sakw MODE PERIOD RESTARTS ITERS [ciphertext] [seed]     env: CRIBW (10), MAXKW (10), BEAU, QUAD
 * prints the best decryption per restart, and the overall best.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 97
static const char *CT = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
static float *QG;
static int ct[N], cribp[N];
static double CRIBW = 10.0;
static int MAXKW = 10, BEAU = 0;
static unsigned long long rs = 88172645463325252ULL;
static inline unsigned long long xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static inline double ur(void) { return (xr() >> 11) * (1.0 / 9007199254740992.0); }

static int MODE, P, firstcrib[64], nfree, freeres[64];
static int fixed[2];          /* alphabet a is not searched: its keyword stays as set at the start */
typedef struct { int kw[2][26], n[2], K[64]; } State;

/* alpha[letter] = index: keyword letters first, then the rest in A-Z order */
static void build(const int *kw, int n, int *idx, int *inv) {
    int used[26] = {0}, j = 0;
    for (int i = 0; i < n; i++) { idx[kw[i]] = j; inv[j++] = kw[i]; used[kw[i]] = 1; }
    for (int l = 0; l < 26; l++) if (!used[l]) { idx[l] = j; inv[j++] = l; }
}

static double score(const State *s, char *out, int *ncrib, int *keyout) {
    int X[26], Xi[26], Y[26], Yi[26], pt[N], crib = 0;
    build(s->kw[0], s->n[0], X, Xi);
    if (MODE == 3) memcpy(Y, X, sizeof X); else build(s->kw[1], s->n[1], Y, Yi);
    int K[64];
    for (int j = 0; j < P; j++) {
        int i = firstcrib[j];
        K[j] = i < 0 ? s->K[j] : ((Y[ct[i]] + (BEAU ? X[cribp[i]] : -X[cribp[i]])) % 26 + 26) % 26;
    }
    if (keyout) memcpy(keyout, K, sizeof(int) * P);
    for (int i = 0; i < N; i++) {
        pt[i] = Xi[(((BEAU ? K[i % P] - Y[ct[i]] : Y[ct[i]] - K[i % P])) % 26 + 26) % 26];
        if (cribp[i] >= 0 && pt[i] == cribp[i]) crib++;
    }
    double q = 0;
    for (int i = 0; i + 3 < N; i++) q += QG[((pt[i] * 26 + pt[i + 1]) * 26 + pt[i + 2]) * 26 + pt[i + 3]];
    if (out) { for (int i = 0; i < N; i++) out[i] = 'A' + pt[i]; out[N] = 0; }
    if (ncrib) *ncrib = crib;
    return q + CRIBW * crib;
}

static void mutate(State *s) {
    double r = ur();
    if (nfree && r < 0.25) { s->K[freeres[xr() % nfree]] = xr() % 26; return; }
    int a = MODE == 3 ? 0 : fixed[0] ? 1 : fixed[1] ? 0 : (int)(xr() & 1);
    int *kw = s->kw[a], *n = &s->n[a];
    int in[26] = {0};
    for (int i = 0; i < *n; i++) in[kw[i]] = 1;
    r = ur();
    if (r < 0.40 && *n > 0) {                                  /* replace a letter */
        int l; do l = xr() % 26; while (in[l]);
        kw[xr() % *n] = l;
    } else if (r < 0.60 && *n > 1) {                           /* swap two places */
        int i = xr() % *n, j = xr() % *n, t = kw[i]; kw[i] = kw[j]; kw[j] = t;
    } else if (r < 0.82 && *n < MAXKW) {                       /* insert a letter */
        int l; do l = xr() % 26; while (in[l]);
        int pos = xr() % (*n + 1);
        memmove(kw + pos + 1, kw + pos, sizeof(int) * (*n - pos));
        kw[pos] = l; (*n)++;
    } else if (*n > 0) {                                       /* delete a letter */
        int pos = xr() % *n;
        memmove(kw + pos, kw + pos + 1, sizeof(int) * (*n - pos - 1));
        (*n)--;
    }
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: sakw MODE PERIOD RESTARTS ITERS [ciphertext] [seed]\n"); return 1; }
    MODE = atoi(argv[1]); P = atoi(argv[2]);
    int restarts = atoi(argv[3]); long iters = atol(argv[4]);
    if (argc > 5 && argv[5][0]) CT = argv[5];
    if (argc > 6) rs ^= strtoull(argv[6], 0, 10) * 2654435761ULL;
    if (getenv("CRIBW")) CRIBW = atof(getenv("CRIBW"));
    if (getenv("MAXKW")) MAXKW = atoi(getenv("MAXKW"));
    if (getenv("BEAU")) BEAU = atoi(getenv("BEAU"));
    QG = malloc(sizeof(float) * 456976);
    const char *paths[] = {getenv("QUAD"), "data/quadgrams.bin", "data/quadgrams_local.bin"};
    FILE *f = NULL;
    for (int i = 0; i < 3 && !f; i++) if (paths[i]) f = fopen(paths[i], "rb");
    if (!f || fread(QG, sizeof(float), 456976, f) != 456976) { fprintf(stderr, "need a quadgram model in data/\n"); return 1; }
    fclose(f);
    for (int i = 0; i < N; i++) { ct[i] = CT[i] - 'A'; cribp[i] = -1; }
    const char *c1 = "EASTNORTHEAST", *c2 = "BERLINCLOCK";
    for (int i = 0; c1[i]; i++) cribp[21 + i] = c1[i] - 'A';
    for (int i = 0; c2[i]; i++) cribp[63 + i] = c2[i] - 'A';
    for (int j = 0; j < P; j++) firstcrib[j] = -1;
    for (int i = N - 1; i >= 0; i--) if (cribp[i] >= 0) firstcrib[i % P] = i;
    for (int j = 0; j < P; j++) if (firstcrib[j] < 0) freeres[nfree++] = j;
    for (int w = 0; w < 20; w++) xr();

    double overall = -1e18; char obest[N + 1]; State os; int ocrib = 0;
    for (int r = 0; r < restarts; r++) {
        State cur; memset(&cur, 0, sizeof cur);
        for (int a = 0; a < 2; a++) {                          /* random starting keywords */
            int perm[26]; for (int l = 0; l < 26; l++) perm[l] = l;
            for (int i = 25; i > 0; i--) { int j = xr() % (i + 1), t = perm[i]; perm[i] = perm[j]; perm[j] = t; }
            cur.n[a] = 4 + xr() % 4; if (cur.n[a] > MAXKW) cur.n[a] = MAXKW;
            memcpy(cur.kw[a], perm, sizeof(int) * cur.n[a]);
            const char *fx = (a == 1 && MODE == 1) || (a == 0 && MODE == 6) ? "KRYPTOS"
                           : (a == 1 && MODE == 5) || (a == 0 && MODE == 2) ? "" : NULL;
            if (fx) { fixed[a] = 1; cur.n[a] = (int)strlen(fx); for (int i = 0; fx[i]; i++) cur.kw[a][i] = fx[i] - 'A'; }
        }
        for (int j = 0; j < P; j++) cur.K[j] = xr() % 26;
        double sc = score(&cur, 0, 0, 0), best = sc; State bs = cur;
        for (long it = 0; it < iters; it++) {
            double T = 12.0 * (1.0 - (double)it / iters) + 0.25;
            State nx = cur; mutate(&nx);
            double ns = score(&nx, 0, 0, 0);
            if (ns >= sc || ur() < exp((ns - sc) / T)) { cur = nx; sc = ns; if (sc > best) { best = sc; bs = cur; } }
        }
        char out[N + 1]; int nc; score(&bs, out, &nc, 0);
        printf("restart %d score %.1f quad/letter %.2f cribs %d/24 %s\n", r, best, (best - CRIBW * nc) / (N - 3), nc, out);
        fflush(stdout);
        if (best > overall) { overall = best; strcpy(obest, out); os = bs; ocrib = nc; }
    }
    printf("BEST %.1f quad/letter %.2f cribs %d/24 %s  X=", overall, (overall - CRIBW * ocrib) / (N - 3), ocrib, obest);
    for (int i = 0; i < os.n[0]; i++) putchar('A' + os.kw[0][i]);
    printf(" Y=");
    for (int i = 0; i < os.n[MODE == 3 ? 0 : 1]; i++) putchar('A' + os.kw[MODE == 3 ? 0 : 1][i]);
    printf(" key=");
    int key[64]; score(&os, 0, 0, key);
    for (int j = 0; j < P; j++) putchar('A' + key[j]);
    putchar('\n');
    return 0;
}
