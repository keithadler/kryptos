/* Exact columnar-transposition x periodic-substitution search at widths too large to enumerate,
 * by depth-first placement of columns with crib pruning.
 *
 * Columns are assigned read ranks 0..w-1 one at a time. As soon as a column is placed, every crib
 * letter in it gets a known ciphertext position, hence a forced key value; if two cribs sharing a
 * key residue disagree, the whole subtree dies. Leaves that survive with >= MINCHK constraints are
 * printed. Exactly equivalent to brute force over all w! orders, only pruned.
 *
 * dir 0 (forward): plaintext written row-wise, columns read top-down in rank order.
 * dir 1 (inverse): plaintext written into columns in rank order, ciphertext read row-wise.
 * order A: key index = plaintext position (substitute, then transpose)
 * order B: key index = ciphertext position (transpose, then substitute)
 *
 * usage: dfs WMIN WMAX PMAX [MINCHK] [ciphertext]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 97
static const char *K4 = "OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR";
static const char *AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static const char *KA = "KRYPTOSABCDEFGHIJLMNQUVWXZ";
static int NC, cpos[32], cptv[2][32], ai[2][26];
static int W, ROWS, FULL, DIR, BEAU, XA, YA, ORDB, PER, MINCHK = 8;
static int colen[64], used[64], ord[64];
static int val[64], cnt[64];
static int cribcol[32];            /* dir 0: column of crib j */
static long long nodes, survivors;
static int checks_now;

static int forced(int j, int cp) {
    int c = ai[YA][K4[cp] - 'A'], p = cptv[XA][j];
    return BEAU ? (c + p) % 26 : (c - p + 26) % 26;
}

/* place crib j at ciphertext position cp; returns 0 on conflict. Records undo on stack. */
static int stk[64], sp;
static int place(int j, int cp) {
    int v = forced(j, cp), r = (ORDB ? cp : cpos[j]) % PER;
    if (cnt[r]) { if (val[r] != v) return 0; checks_now++; }
    else val[r] = v;
    cnt[r]++; stk[sp++] = r;
    return 1;
}

static void dfs(int k, int start) {
    nodes++;
    if (checks_now + (NC - sp) < MINCHK) return;   /* each unplaced crib adds at most one check */
    if (k == W) {
        if (checks_now >= MINCHK) {
            survivors++;
            printf("SURVIVOR w=%d dir=%d fam=%s-P%s-C%s order=%c per=%d checks=%d ord=", W, DIR,
                   BEAU ? "beau" : "vig", XA ? "KA" : "AZ", YA ? "KA" : "AZ", ORDB ? 'B' : 'A', PER, checks_now);
            for (int i = 0; i < W; i++) printf("%d%s", ord[i], i + 1 < W ? "," : "\n");
        }
        return;
    }
    for (int c = 0; c < W; c++) {
        if (used[c]) continue;
        int sp0 = sp, ch0 = checks_now, ok = 1;
        if (DIR == 0) {
            for (int j = 0; j < NC && ok; j++)
                if (cribcol[j] == c) ok = place(j, start + cpos[j] / W);
        } else {
            for (int j = 0; j < NC && ok; j++)
                if (cpos[j] >= start && cpos[j] < start + colen[c]) ok = place(j, (cpos[j] - start) * W + c);
        }
        if (ok) { used[c] = 1; ord[k] = c; dfs(k + 1, start + colen[c]); used[c] = 0; }
        while (sp > sp0) cnt[stk[--sp]]--;
        checks_now = ch0;
    }
}

static void add_crib(int s1, const char *w) {
    for (int k = 0; w[k]; k++) {
        cpos[NC] = s1 - 1 + k;
        cptv[0][NC] = ai[0][w[k] - 'A']; cptv[1][NC] = ai[1][w[k] - 'A'];
        NC++;
    }
}

int main(int argc, char **argv) {
    int wmin = atoi(argv[1]), wmax = atoi(argv[2]), pmax = atoi(argv[3]);
    if (argc > 4) MINCHK = atoi(argv[4]);
    if (argc > 5) K4 = argv[5];
    for (int i = 0; i < 26; i++) { ai[0][AZ[i] - 'A'] = i; ai[1][KA[i] - 'A'] = i; }
    add_crib(22, "EASTNORTHEAST");
    add_crib(64, "BERLINCLOCK");
    for (W = wmin; W <= wmax; W++) {
        ROWS = (N + W - 1) / W; FULL = N % W;
        for (int c = 0; c < W; c++) colen[c] = (FULL == 0 || c < FULL) ? ROWS : ROWS - 1;
        for (int j = 0; j < NC; j++) cribcol[j] = cpos[j] % W;
        long long n0 = nodes, s0 = survivors;
        for (DIR = 0; DIR < 2; DIR++)
            for (int fam = 0; fam < 8; fam++)
                for (ORDB = 0; ORDB < 2; ORDB++)
                    for (PER = 1; PER <= pmax; PER++) {
                        BEAU = fam >> 2; XA = (fam >> 1) & 1; YA = fam & 1;
                        memset(cnt, 0, sizeof cnt); sp = 0; checks_now = 0;
                        dfs(0, 0);
                    }
        fprintf(stderr, "width %d: %lld nodes, survivors %lld\n", W, nodes - n0, survivors - s0);
        fflush(stdout);
    }
    return 0;
}
