"""Keyword-alphabet annealing (bin/sakw) at the key lengths the clues leave open: planted recovery,
then K4, then random ciphertexts, for the Vigenere and Beaufort forms.

usage: checks/run_sakw.py [MODE] [MAXKW] [RESTARTS] [ITERS] [LENGTHS]     defaults: 4 10 24 3000000 all-open
A length counts only where planted ciphers (random letter-string keywords, real English, clue words
in place) are recovered. Recovered = at least 90 of 97 letters.
"""
import os
import random
import subprocess
import sys
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODE = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MAXKW = int(sys.argv[2]) if len(sys.argv) > 2 else 10
RESTARTS = sys.argv[3] if len(sys.argv) > 3 else "24"
ITERS = sys.argv[4] if len(sys.argv) > 4 else "3000000"
ONE = (13, 16, 19, 20, 23, 24, 26)          # open for one free alphabet (Quagmire I/II, SEARCH.md 4.E)
OPEN = {4: {"vig": (8, 13, 16, 19, 20, 23, 24, 26), "beau": (8, 13, 16, 19, 20, 23, 24, 26)},
        3: {"vig": (), "beau": (23, 26)}}.get(MODE, {"vig": ONE, "beau": ONE})
if len(sys.argv) > 5:
    OPEN = {k: tuple(p for p in v if str(p) in sys.argv[5].split(",")) for k, v in OPEN.items()}
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NPLANT, NK4, NRANDOM = 8, 4, 4


def sakw(kind, per, ct, seed):
    env = dict(os.environ, MAXKW=str(MAXKW), BEAU="1" if kind == "beau" else "0")
    out = subprocess.run([os.path.join(ROOT, "bin", "sakw"), str(MODE), str(per), RESTARTS, ITERS, ct, str(seed)],
                         capture_output=True, text=True, cwd=ROOT, env=env).stdout
    f = [l for l in out.splitlines() if l.startswith("BEST")][0].split()
    return float(f[3]), int(f[5].split("/")[0]), f[6], " ".join(f[7:])      # quad/letter, cribs, plaintext, keys


def job(a):
    what, kind, per, i = a
    if what == "plant":
        o = subprocess.run([sys.executable, os.path.join(ROOT, "checks", "plant_sakw.py"), str(MODE), str(per), str(i),
                            str(MAXKW - 1)] + (["beau"] if kind == "beau" else []), capture_output=True, text=True).stdout.split("\n")
        q, c, pt, keys = sakw(kind, per, o[0], i)
        return a, (sum(x == y for x, y in zip(pt, o[1])), q)
    if what == "k4":
        return a, sakw(kind, per, "", 100 + i)
    rnd = random.Random(per * 100 + i)
    return a, sakw(kind, per, "".join(rnd.choice(AZ) for _ in range(97)), i)


if __name__ == "__main__":
    jobs = [(w, kind, per, i) for kind in OPEN for per in OPEN[kind]
            for w, n in (("plant", NPLANT), ("k4", NK4), ("random", NRANDOM)) for i in range(n)]
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        res = dict(pool.imap_unordered(job, jobs))
    name = {4: "IV, two keyword alphabets", 3: "III, one keyword alphabet on both sides", 1: "I, keyword plaintext alphabet, KRYPTOS ciphertext alphabet",
            5: "I, keyword plaintext alphabet, A-Z ciphertext alphabet", 2: "II, A-Z plaintext alphabet, keyword ciphertext alphabet",
            6: "II, KRYPTOS plaintext alphabet, keyword ciphertext alphabet"}[MODE]
    print(f"mode {MODE} (Quagmire {name}), keywords up to "
          f"{MAXKW} letters (planted: 4-{MAXKW - 1}), {RESTARTS} restarts x {ITERS} steps per run")
    for kind in OPEN:
        for per in OPEN[kind]:
            pl = [res[("plant", kind, per, i)] for i in range(NPLANT)]
            k4 = max((res[("k4", kind, per, i)] for i in range(NK4)), key=lambda r: r[0] * 94 + 10 * r[1])
            rd = [res[("random", kind, per, i)] for i in range(NRANDOM)]
            print(f"{kind:4} length {per:2}: planted recovered {sum(p[0] >= 90 for p in pl)}/{NPLANT} "
                  f"(letters {sorted(p[0] for p in pl)}, English {min(p[1] for p in pl if p[0] >= 90) if any(p[0] >= 90 for p in pl) else 0:.2f} "
                  f"to {max(p[1] for p in pl if p[0] >= 90) if any(p[0] >= 90 for p in pl) else 0:.2f})")
            print(f"       K4 best {k4[0]:.2f} with {k4[1]}/24 clues   random best {sorted(r[0] for r in rd)} clues {[r[1] for r in rd]}")
            print(f"       K4: {k4[2]}  {k4[3]}")
