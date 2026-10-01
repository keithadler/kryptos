"""Build quadgram models without downloading anything.

  python3 checks/quadgrams_local.py          English -> data/quadgrams_local.bin
  python3 checks/quadgrams_local.py german   German  -> data/quadgrams_de_local.bin

English: the prose of this Mac's man pages and Perl pods, plus data/wiki_kryptos.txt (about 12M
letters). Technical vocabulary, but ordinary English letter statistics: K3's plaintext scores -4.2
per quadgram and K4's ciphertext -6.5. quadgrams.py builds the preferred model from the
running-key texts once checks/fetch_texts.sh has been run.

German: the German strings of macOS's own localisation tables (*.loctable), umlauts written out
(AE, OE, UE, SS) as a hand cipher would. data/weltzeituhr_de.txt is held out as the test text.
Also writes data/words_de_local.txt, the German words seen, for keyed alphabets.
"""
import glob
import gzip
import pathlib
import plistlib
import re
import sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import kryptos

UMLAUT = str.maketrans({"Ä": "AE", "Ö": "OE", "Ü": "UE", "ä": "AE", "ö": "OE", "ü": "UE", "ß": "SS"})


def german_letters(s):
    return "".join(c for c in s.translate(UMLAUT).upper() if "A" <= c <= "Z")


def wikitext_prose(path):
    """Readable text of a raw wikitext file: templates, refs, link targets and markup removed."""
    t = pathlib.Path(path).read_text()
    for _ in range(4):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<[^>]+>", " ", t, flags=re.S)
    t = re.sub(r"\[\[(?:Datei|File|Kategorie)[^\]]*\]\]", " ", t)
    t = re.sub(r"\[\[[^\]|]*\|", " ", t)
    return re.sub(r"https?://\S+|&nbsp;", " ", t)


def english_text():
    parts = []
    for f in glob.glob("/usr/share/man/man[1-8]/*") + glob.glob("/System/Library/Perl/*/pod/*.pod"):
        try:
            raw = (gzip.open(f).read() if f.endswith(".gz") else open(f, "rb").read()).decode("latin-1")
        except OSError:
            continue
        lines = [l for l in raw.splitlines() if not l.startswith((".", "'", "=")) and len(l) > 40]   # prose, not macros
        parts.append(re.sub(r"\\f.|\\\(..|\\[a-zA-Z&-]", " ", " ".join(lines)))
    parts.append((ROOT / "data" / "wiki_kryptos.txt").read_text())
    return "".join(c for c in " ".join(parts).upper() if "A" <= c <= "Z")


def german_text():
    seen = set()

    def walk(v):
        if isinstance(v, str):
            if len(v) > 25:
                seen.add(re.sub(r"%[\d$]*[@a-zA-Z]+|\\[nt]|<[^>]+>", " ", v))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    roots = ("/System/Applications", "/System/Library/CoreServices", "/System/Library/Frameworks",
             "/System/Library/PrivateFrameworks")
    for root in roots:
        for f in pathlib.Path(root).rglob("*.loctable"):
            try:
                walk(plistlib.load(open(f, "rb")).get("de"))
            except Exception:
                continue
    text = " ".join(sorted(seen))
    words = {german_letters(w) for w in re.findall(r"[A-Za-zÄÖÜäöüß]{4,20}", text + " " + wikitext_prose(ROOT / "data" / "weltzeituhr_de.txt"))}
    (ROOT / "data" / "words_de_local.txt").write_text("\n".join(sorted(words)) + "\n")
    return german_letters(text)


def build(letters, out):
    b = (np.frombuffer(letters.encode(), dtype=np.uint8) - 65).astype(np.int64)
    q = ((b[:-3] * 26 + b[1:-2]) * 26 + b[2:-1]) * 26 + b[3:]
    counts = np.bincount(q, minlength=26 ** 4).astype(np.float64)
    logp = np.log10(np.maximum(counts, 0.01) / counts.sum()).astype(np.float32)
    logp.tofile(ROOT / "data" / out)

    def score(s):
        a = np.frombuffer(s.encode(), dtype=np.uint8).astype(np.int64) - 65
        return float(logp[((a[:-3] * 26 + a[1:-2]) * 26 + a[2:-1]) * 26 + a[3:]].mean())
    return score


if __name__ == "__main__":
    de = german_letters(wikitext_prose(ROOT / "data" / "weltzeituhr_de.txt"))
    if sys.argv[1:] == ["german"]:
        t = german_text()
        score = build(t, "quadgrams_de_local.bin")
        print(f"{len(t)} letters; per-quadgram score: German article {score(de):.2f}  "
              f"K3 plaintext (English) {score(kryptos.K3_PT):.2f}  K4 ciphertext {score(kryptos.K4):.2f}")
    else:
        t = english_text()
        score = build(t, "quadgrams_local.bin")
        print(f"{len(t)} letters; per-quadgram score: K3 plaintext {score(kryptos.K3_PT):.2f}  "
              f"K2 plaintext {score(kryptos.K2_PT):.2f}  German article {score(de):.2f}  "
              f"K4 ciphertext {score(kryptos.K4):.2f}")
