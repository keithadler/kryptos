"""Build English 4-letter-group (quadgram) log-probabilities from data/running_keys/*.txt -> data/quadgrams.bin (float32, 26^4).
The KJV is down-weighted so archaic spelling doesn't dominate."""
import pathlib
import numpy as np
from runkey import load
counts = np.zeros(26 ** 4, dtype=np.float64)
for f in sorted(pathlib.Path("data/running_keys").glob("*.txt")):
    t = load(f).astype(np.int64)
    q = ((t[:-3] * 26 + t[1:-2]) * 26 + t[2:-1]) * 26 + t[3:]
    w = 0.25 if "kjv" in f.stem else 1.0
    counts += w * np.bincount(q, minlength=26 ** 4)
    print(f"{f.stem:20} {len(t):9} letters  weight {w}")
total = counts.sum()
logp = np.log10(np.maximum(counts, 0.01) / total).astype(np.float32)
logp.tofile("data/quadgrams.bin")
def score(s):
    a = np.frombuffer(s.encode(), dtype=np.uint8).astype(np.int64) - 65
    return float(logp[((a[:-3] * 26 + a[1:-2]) * 26 + a[2:-1]) * 26 + a[3:]].mean())
print("per-quadgram score: English", round(score("SLOWLYDESPARATLYSLOWLYTHEREMAINSOFPASSAGEDEBRISTHATENCUMBEREDTHELOWERPARTOFTHEDOORWAYWASREMOVED"), 2),
      " K4", round(score(__import__("kryptos").K4), 2))
