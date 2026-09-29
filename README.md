# Kryptos K4: a documented search

K4, the 97-letter fourth passage of Jim Sanborn's *Kryptos* sculpture, is still publicly unsolved.
This repo records a systematic search: what the 24 plaintext letters Sanborn released rule out,
how each claim was checked, and what they cannot decide. It has not found a solution.

**Read [SEARCH.md](SEARCH.md)** for the method, every result with its evidence, the assumptions
behind "eliminated", and what remains open.

## In short

- **Eliminated**, wherever the clues can test it:
  - every repeating-key tableau cipher (Vigenère, Beaufort, Quagmire) up to key length 26, with standard, KRYPTOS, theme-word or any of 209k dictionary alphabets;
  - autokey, progressive and digit keys;
  - running keys from K1–K3, the sculpture, Carter's *Tomb of Tut-ankh-Amen* and the Bible;
  - Hill, Trifid, Playfair and every 5×5-square cipher;
  - columnar transposition with every column order up to width 14;
  - K3's rotation method;
  - the K1/K2 cipher with *any* alphabet on both sides;
  - the K1/K2 cipher applied twice ("LAYER TWO").
- **Every claim is checked against planted ciphers.** `make verify` shows each search finding a
  known example of the family it rules out.
- **Nothing beats chance.** Every apparent survivor was compared with what random ciphertexts
  produce under the same test, and none stood out.
- **Open:** families the 24 letters are too few to decide: two free alphabets, long keys, stacked
  layers, and hand methods with no clean form. The realistic way forward is more plaintext or the
  release of K5.

## Quick start

```
make verify                 # build the C searchers, run the 21 planted-cipher checks
checks/fetch_texts.sh       # optional: download the public-domain running-key texts
checks/reproduce.sh         # regenerate the evidence logs in results/
```

Python 3 with numpy, and a C compiler.

## Layout

| Path | What |
|---|---|
| `kryptos.py` | K4, the clues, the alphabets, the tableau operations, hypothesis mode |
| `attacks.py`, `typo.py`, `dictalpha.py`, `digits.py`, `trifid.py`, `mixedalpha.py`, `quag34.py`, `layer2.py`, `runkey.py`, `runkey_mixed.py`, `drag.py`, `guess_run.py` | The searches, one family each (see SEARCH.md §4) |
| `c/` | C searchers: columnar/rotation/keyword transposition (`trans`), pruned every-order columnar (`dfs`), Quagmire III/IV solver (`quag3`), annealing (`sa`) |
| `verify.py` | Planted-cipher checks for every search |
| `checks/` | Calibration against random ciphertexts, text download, evidence regeneration |
| `results/` | The evidence logs cited in SEARCH.md |
| `data/` | Sculpture text and other inputs, with provenance in `data/SOURCES.md` |

## License

Code: MIT (see `LICENSE`). The Wikipedia-derived files in `data/` (`wiki_kryptos.txt`,
`sculpture_left.txt`, `tableau.txt`, `weltzeituhr_de.txt`) are CC BY-SA 4.0, from the sources in `data/SOURCES.md`.
