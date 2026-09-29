/* Simulated-annealing solver for periodic polyalphabetic ciphers with unknown alphabets
 * (Quagmire I-IV), scored by English quadgrams plus crib agreement.
 *
 *   C_i = Y[ (X(P_i) + k[i mod p]) mod 26 ]      i.e.  P_i = Xinv[ (Y(C_i) - k) mod 26 ]
 * mode: 4 = X and Y free (Quagmire IV), 3 = X = Y free (III), 1 = X free, Y = KA (I),
 *       2 = X = AZ, Y free (II), 5 = X free, Y = AZ, 6 = X = KA, Y free.
 * State moves: swap two letters in a free alphabet, or change one key shift.
 * Score = sum of quadgram log-probs + CRIBW * (number of crib letters reproduced).
 *
 * usage: sa MODE PERIOD RESTARTS ITERS [ciphertext] [seed]
 * prints the best decryption per restart, and the overall best.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 97
static const char *CT = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
static const char *KA = "KRYPTOSABCDEFGHIJLMNQUVWXZ";
static float *QG;
static int ct[N], cribp[N];   /* cribp[i] = plaintext letter or -1 */
static double CRIBW = 4.0;   /* env CRIBW overrides */
static unsigned long long rs = 88172645463325252ULL;
static inline unsigned long long xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static inline double ur(void) { return (xr() >> 11) * (1.0 / 9007199254740992.0); }

static int MODE, P;
static int X[26], Y[26], K[64];   /* X[letter] = index, Y[letter] = index */

static double score(char *out) {
    int xinv[26], pt[N];
    for (int l = 0; l < 26; l++) xinv[X[l]] = l;
    int crib = 0;
    for (int i = 0; i < N; i++) {
        pt[i] = xinv[((Y[ct[i]] - K[i % P]) % 26 + 26) % 26];
        if (cribp[i] >= 0 && pt[i] == cribp[i]) crib++;
    }
    double s = 0;
    for (int i = 0; i + 3 < N; i++) s += QG[((pt[i] * 26 + pt[i + 1]) * 26 + pt[i + 2]) * 26 + pt[i + 3]];
    if (out) { for (int i = 0; i < N; i++) out[i] = 'A' + pt[i]; out[N] = 0; }
    return s + CRIBW * crib;
}

static void shuffle(int *a) {
    for (int i = 25; i > 0; i--) { int j = xr() % (i + 1), t = a[i]; a[i] = a[j]; a[j] = t; }
}

int main(int argc, char **argv) {
    MODE = atoi(argv[1]); P = atoi(argv[2]);
    int restarts = atoi(argv[3]); long iters = atol(argv[4]);
    if (argc > 5 && argv[5][0]) CT = argv[5];
    if (argc > 6) rs ^= strtoull(argv[6], 0, 10) * 2654435761ULL;
    if (getenv("CRIBW")) CRIBW = atof(getenv("CRIBW"));
    QG = malloc(sizeof(float) * 456976);
    FILE *f = fopen("data/quadgrams.bin", "rb");
    if (!f || fread(QG, sizeof(float), 456976, f) != 456976) { fprintf(stderr, "need data/quadgrams.bin\n"); return 1; }
    fclose(f);
    for (int i = 0; i < N; i++) { ct[i] = CT[i] - 'A'; cribp[i] = -1; }
    const char *c1 = "EASTNORTHEAST", *c2 = "BERLINCLOCK";
    for (int k = 0; c1[k]; k++) cribp[21 + k] = c1[k] - 'A';
    for (int k = 0; c2[k]; k++) cribp[63 + k] = c2[k] - 'A';

    double best_all = -1e18; char best_txt[N + 1], txt[N + 1];
    for (int r = 0; r < restarts; r++) {
        for (int l = 0; l < 26; l++) X[l] = Y[l] = l;
        if (MODE == 1) { for (int l = 0; l < 26; l++) Y[KA[l] - 'A'] = l; }
        if (MODE == 6) { for (int l = 0; l < 26; l++) X[KA[l] - 'A'] = l; }
        if (MODE == 1 || MODE == 3 || MODE == 4 || MODE == 5) shuffle(X);
        if (MODE == 2 || MODE == 4 || MODE == 6) shuffle(Y);
        if (MODE == 3) memcpy(Y, X, sizeof X);
        for (int j = 0; j < P; j++) K[j] = xr() % 26;
        double cur = score(0), best = cur;
        int bX[26], bY[26], bK[64];
        memcpy(bX, X, sizeof X); memcpy(bY, Y, sizeof Y); memcpy(bK, K, sizeof(int) * P);
        for (long it = 0; it < iters; it++) {
            double T = 12.0 * pow(0.2 / 12.0, (double)it / iters);
            /* allowed moves: 0 = swap in X (modes 1,3,4; mode 3 mirrors into Y), 1 = swap in Y
             * (modes 2,4), 2 = change a key shift (all modes) */
            int allowed[3], na = 0;
            if (MODE != 2 && MODE != 6) allowed[na++] = 0;
            if (MODE == 2 || MODE == 4 || MODE == 6) allowed[na++] = 1;
            allowed[na++] = 2;
            int mv = allowed[xr() % na], a = xr() % 26, b = xr() % 26, j = xr() % P, oldk = K[j];
            if (mv == 2) K[j] = xr() % 26;
            else if (mv == 0) { int t = X[a]; X[a] = X[b]; X[b] = t; if (MODE == 3) { t = Y[a]; Y[a] = Y[b]; Y[b] = t; } }
            else { int t = Y[a]; Y[a] = Y[b]; Y[b] = t; }
            double s = score(0);
            if (s >= cur || ur() < exp((s - cur) / T)) {
                cur = s;
                if (s > best) { best = s; memcpy(bX, X, sizeof X); memcpy(bY, Y, sizeof Y); memcpy(bK, K, sizeof(int) * P); }
            } else {
                if (mv == 2) K[j] = oldk;
                else if (mv == 0) { int t = X[a]; X[a] = X[b]; X[b] = t; if (MODE == 3) { t = Y[a]; Y[a] = Y[b]; Y[b] = t; } }
                else { int t = Y[a]; Y[a] = Y[b]; Y[b] = t; }
            }
        }
        memcpy(X, bX, sizeof X); memcpy(Y, bY, sizeof Y); memcpy(K, bK, sizeof(int) * P);
        best = score(txt);
        int crib = 0;
        for (int i = 0; i < N; i++) if (cribp[i] >= 0 && txt[i] - 'A' == cribp[i]) crib++;
        double qpl = (best - CRIBW * crib) / (N - 3);
        printf("restart %2d  score %8.1f  quadgram/letter %.2f  cribs %2d/24  %s\n", r, best, qpl, crib, txt);
        if (best > best_all) { best_all = best; memcpy(best_txt, txt, N + 1); }
        fflush(stdout);
    }
    printf("BEST %s\n", best_txt);
    return 0;
}
