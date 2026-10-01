# Data sources

| File | What | Source |
|---|---|---|
| `wiki_kryptos.txt` | Raw wikitext of the English Wikipedia *Kryptos* article (CC BY-SA 4.0), fetched 2026-09-28 | `https://en.wikipedia.org/w/index.php?title=Kryptos&action=raw` |
| `sculpture_left.txt` | The left side of the sculpture, K1–K4 ciphertext as carved (869 characters: 865 letters, 4 `?`) | extracted from `wiki_kryptos.txt` |
| `tableau.txt` | The right side: the KRYPTOS-keyed Vigenère tableau (867 letters, including the extra L) | extracted from `wiki_kryptos.txt` |
| `weltzeituhr_de.txt` | Raw wikitext of the German Wikipedia *Weltzeituhr (Alexanderplatz)* article (CC BY-SA 4.0), fetched 2026-09-28 | `https://de.wikipedia.org/w/index.php?title=Weltzeituhr_(Alexanderplatz)&action=raw` |
| `weltzeituhr_cities.txt` | The 147 entries on the World Clock's 24 faces (146 places and the date line), German spellings, state since the 1997 renovation; transcribed from the list in Hungarian Wikipedia's *Uránia világóra* (CC BY-SA 4.0), read 2026-10-01, not checked against the monument | `https://hu.wikipedia.org/wiki/Uránia_világóra` |
| `running_keys/*.txt` (not committed) | Public-domain texts tried as running keys: Carter's *The Tomb of Tut-ankh-Amen* vols 1–3 (Internet Archive OCR), the King James Bible, the Declaration of Independence, the Bill of Rights, the Constitution, Poe's *Works* vol 1, and a 1923 Tutankhamen account (Project Gutenberg) | `checks/fetch_texts.sh` |
| `quadgrams.bin` (not committed) | English four-letter-group log-probabilities built from `running_keys/` (KJV down-weighted) | `python3 quadgrams.py` |
| `quadgrams_local.bin`, `quadgrams_de_local.bin`, `words_de_local.txt` (not committed) | English and German four-letter-group statistics and a German word list built from text already on a Mac: man pages and Perl pods (English), the German strings of macOS's localisation tables (German) | `python3 checks/quadgrams_local.py [german]` |
| `keyword_orders.txt` (not committed) | Column orders from 115k dictionary words, proper names and theme phrases, widths 12–30 | `python3 keywords.py > data/keyword_orders.txt` |

Counts check: the left side has 869 characters and the tableau 867, matching Wikipedia's published counts.
`kryptos.py` holds K4 and the plaintexts of K1–K3; `verify.py` checks that K1 decrypts with KRYPTOS + PALIMPSEST.
The dictionary is macOS's `/usr/share/dict/words` and `propernames` (Webster's Second, public domain).
