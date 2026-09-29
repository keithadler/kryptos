"""How often does RANDOM ciphertext satisfy general Quagmire III/IV at the periods K4 satisfies?"""
import random, sys
import quag34
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
real = quag34.K4
cases = [("IV", "vig", p) for p in (8, 13, 16, 19, 20, 23, 24, 26)] + [("III", "beau", p) for p in (23, 26)]
rnd = random.Random(99)
randoms = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(30)]
for mode, kind, per in cases:
    res = []
    for r in randoms:
        quag34.K4 = r
        res.append(quag34.solve(mode, per, kind, limit=100_000)[0])
    quag34.K4 = real
    print(f"Quagmire {mode} {kind} period {per:2}: random SAT {res.count(True)}/30, UNSAT {res.count(False)}, timeout {res.count(None)}")
    sys.stdout.flush()
