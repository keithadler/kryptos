"""Plant known encryptions in a fake K4 and confirm each test finds them (guards against silent 'none')."""
import random, io, contextlib
import kryptos, attacks
from kryptos import AZ, KA, CRIBS

def fake_pt():
    rnd = random.Random(7)
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    return "".join(pt)

def enc(pt, keyvals, x=KA, y=KA):
    xi = {c: i for i, c in enumerate(x)}
    return "".join(y[(xi[p] + k) % 26] for p, k in zip(pt, keyvals))

def run(name, ct, needle):
    attacks.K4 = ct
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        getattr(attacks, name)()
    out = buf.getvalue()
    ok = needle in out
    print(f"{'PASS' if ok else 'FAIL'} {name}: looking for {needle!r}")
    if not ok:
        print(out)
    return ok

pt = fake_pt()
kai = {c: i for i, c in enumerate(KA)}
key = [kai[c] for c in "KRYPTOSCLOCK"]
ok = run("test_periodic", enc(pt, [key[i % 12] for i in range(97)]), "vig  P:KA C:KA  falsifiable survivors: [(12,")
left = attacks.running_key_texts()["K2 plaintext"]
ok &= run("test_running_key", enc(pt, [kai[left[100 + i]] for i in range(97)]), "('vig', 'KA', 'KA', 'x', 100)")
ct = []
for i, p in enumerate(pt):
    k = kai["Q"] if i < 5 else kai[ct[i - 5]]
    ct.append(KA[(kai[p] + k) % 26])
ok &= run("test_autokey", "".join(ct), "vig  P:KA C:KA key=ct via x-alphabet  survivors: [(5,")
print("ALL PASS" if ok else "SOME FAILED")
