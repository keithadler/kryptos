"""Generate the README figures (light and dark SVG variants) into docs/.

  k4-carved-{light,dark}.svg   K4 as carved, the 24 decoded letters marked with their plaintext
  map-{light,dark}.svg         What the 24 letters rule out, by cipher family and key length

The map's cells are transcribed from the evidence logs named on each row (results/NN_*).
Colors are the data-viz reference palette's categorical slots 1-2, validated for both surfaces.
usage: python3 docs/make_figures.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kryptos import K4, CRIBS  # noqa: E402

THEMES = {
    "light": dict(surface="#fcfcfb", text="#0b0b0b", text2="#52514e", muted="#8a8984", grid="#e4e3df",
                  ruled="#2a78d6", chance="#eb6834", untestable="#e4e3df", open_line="#b9b8b2", on_mark="#ffffff"),
    "dark": dict(surface="#1a1a19", text="#ffffff", text2="#c3c2b7", muted="#8a897f", grid="#383835",
                 ruled="#3987e5", chance="#d95926", untestable="#383835", open_line="#5c5b56", on_mark="#ffffff"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- figure 1: K4 as carved
def carved(t):
    lines = [K4[0:4], K4[4:35], K4[35:66], K4[66:97]]      # the four carved lines
    starts = [0, 4, 35, 66]
    cw, top, lh, left = 24, 58, 58, 20
    W = left * 2 + 31 * cw
    H = top + lh * 4 + 20
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="K4 as carved on the sculpture, four lines, with the 24 decoded letters marked">',
           f'<rect width="{W}" height="{H}" fill="{t["surface"]}"/>',
           f'<text x="{left}" y="24" font-family="{SANS}" font-size="15" font-weight="600" fill="{t["text"]}">K4 as carved</text>',
           f'<text x="{left}" y="42" font-family="{SANS}" font-size="12" fill="{t["text2"]}">'
           f'The 24 letters Sanborn has decoded are marked, with their plaintext underneath. The other 73 are unknown.</text>']
    for li, (line, s0) in enumerate(zip(lines, starts)):
        y = top + li * lh + 22
        for ci, ch in enumerate(line):
            pos = s0 + ci
            x = left + ci * cw
            if pos in CRIBS:
                out.append(f'<rect x="{x + 1}" y="{y - 17}" width="{cw - 2}" height="23" rx="4" fill="{t["ruled"]}"/>')
                out.append(f'<text x="{x + cw / 2}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="16" '
                           f'font-weight="600" fill="{t["on_mark"]}">{ch}</text>')
                out.append(f'<text x="{x + cw / 2}" y="{y + 22}" text-anchor="middle" font-family="{MONO}" '
                           f'font-size="13" fill="{t["text2"]}">{CRIBS[pos]}</text>')
            else:
                out.append(f'<text x="{x + cw / 2}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="16" '
                           f'fill="{t["text"]}">{ch}</text>')
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- figure 2: the map
# R ruled out, C fits but random text fits as often, U too few known letters to test,
# T search did not finish, N not tested / not meaningful
def cells(spec, default="R"):
    row = [default] * 26
    for code, periods in spec.items():
        for p in periods:
            row[p - 1] = code
    return row


ROWS = [
    ("Repeating key, standard or KRYPTOS alphabet", cells({}), "01"),
    ("  same, with any of 209k dictionary-word alphabets", cells({"C": [26]}), "09"),
    ("  same, after or before columnar transposition (every order, widths 2–14)", cells({}), "05, 08"),
    ("  same, with K3’s grid rotation", cells({}), "06"),
    ("Digit keys (Gronsfeld, Gromark), any alphabet", cells({}), "11"),
    ("Any masking alphabet, then a repeating key", cells({"U": [13, 16, 19, 20, 23, 24, 26]}), "13"),
    ("K1/K2’s cipher with any alphabet, Vigenère form", cells({}), "14, 14b"),
    ("  same, Beaufort form", cells({"T": [13, 18], "C": [23, 26]}), "14, 14b, 15"),
    ("Two independent unknown alphabets", cells({"C": [8, 13, 16, 19, 20, 23, 24, 26], "T": [11, 12, 14, 18, 21]}), "14, 15, 21b"),
    ("Trifid, any cube (key length = group size)", cells({"N": [1, 25, 26]}), "12"),
]
LEGEND = [
    ("R", "Ruled out: no key of this length fits all 24 known letters"),
    ("C", "Fits, but random text fits just as often: not evidence"),
    ("U", "Too few known letters to test"),
    ("T", "Search did not finish"),
    ("N", "Not tested"),
]


def swatch(t, code, x, y, w, h, pid):
    if code == "R":
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{t["ruled"]}"/>'
    if code == "C":
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{t["chance"]}"/>'
    if code == "U":
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{t["untestable"]}"/>'
    if code == "T":
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="url(#{pid})" '
                f'stroke="{t["open_line"]}" stroke-width="1"/>')
    return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="3" fill="none" '
            f'stroke="{t["open_line"]}" stroke-width="1" stroke-dasharray="2 2"/>')


def the_map(t, mode):
    pid = f"hatch-{mode}"
    label_w, cw, ch, gap = 430, 20, 20, 2
    left, top = 20, 78
    grid_x = left + label_w
    W = grid_x + 26 * (cw + gap) + 50
    H = top + len(ROWS) * (ch + gap) + 40 + len(LEGEND) * 20 + 10
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Map of which cipher families the 24 known letters rule out at each key length 1 to 26">',
         f'<defs><pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         f'<rect width="6" height="6" fill="{t["surface"]}"/><line x1="0" y1="0" x2="0" y2="6" '
         f'stroke="{t["open_line"]}" stroke-width="2"/></pattern></defs>',
         f'<rect width="{W}" height="{H}" fill="{t["surface"]}"/>',
         f'<text x="{left}" y="24" font-family="{SANS}" font-size="15" font-weight="600" fill="{t["text"]}">'
         f'What the 24 known letters rule out</text>',
         f'<text x="{left}" y="42" font-family="{SANS}" font-size="12" fill="{t["text2"]}">'
         f'Each cell is one cipher family at one key length. Evidence log for each row in results/.</text>',
         f'<text x="{grid_x + 13 * (cw + gap)}" y="{top - 22}" text-anchor="middle" font-family="{SANS}" '
         f'font-size="11" fill="{t["text2"]}">key length</text>',
         f'<text x="{W - 44}" y="{top - 8}" font-family="{SANS}" font-size="11" fill="{t["muted"]}">log</text>']
    for p in range(1, 27):
        if p in (1, 5, 10, 15, 20, 25, 26):
            o.append(f'<text x="{grid_x + (p - 1) * (cw + gap) + cw / 2}" y="{top - 8}" text-anchor="middle" '
                     f'font-family="{SANS}" font-size="11" fill="{t["text2"]}">{p}</text>')
    for r, (label, row, ev) in enumerate(ROWS):
        y = top + r * (ch + gap)
        indent = label.startswith("  ")
        o.append(f'<text x="{left + (14 if indent else 0)}" y="{y + 14}" font-family="{SANS}" font-size="12.5" '
                 f'fill="{t["text2"] if indent else t["text"]}">{esc(label.strip())}</text>')
        for p, code in enumerate(row):
            o.append(swatch(t, code, grid_x + p * (cw + gap), y, cw, ch, pid))
        o.append(f'<text x="{W - 44}" y="{y + 14}" font-family="{SANS}" font-size="11" fill="{t["muted"]}">'
                 f'{esc(ev.split(",")[0])}</text>')
    ly = top + len(ROWS) * (ch + gap) + 26
    for i, (code, text) in enumerate(LEGEND):
        y = ly + i * 20
        o.append(swatch(t, code, left, y, 14, 14, pid))
        o.append(f'<text x="{left + 22}" y="{y + 11.5}" font-family="{SANS}" font-size="12" fill="{t["text2"]}">'
                 f'{esc(text)}</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    for mode, t in THEMES.items():
        for name, svg in (("k4-carved", carved(t)), ("map", the_map(t, mode))):
            path = os.path.join(HERE, f"{name}-{mode}.svg")
            with open(path, "w") as f:
                f.write(svg + "\n")
            print("wrote", os.path.relpath(path, os.path.dirname(HERE)))
