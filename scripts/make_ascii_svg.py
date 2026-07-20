#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII-art SVG.

Each row wipes in left-to-right (a small block cursor rides the wipe edge),
staggered top to bottom. Prints once and freezes — no loop. SMIL/CSS inside
the SVG so GitHub renders it.

Usage: python scripts/make_ascii_svg.py
Output: avi-ascii.svg
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "avi-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FILL = "#b9c0c8"        # one light-gray fill — monochrome, not rainbow


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    if not SRC.exists():
        raise SystemExit(f"missing {SRC} — run prep_photo.py first")
    img = Image.open(SRC).convert("L")
    # Character cells are taller than wide; correct the aspect.
    img = img.resize((COLS, ROWS))
    px = img.load()

    rows_text = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            b = px[x, y]  # 0=black .. 255=white
            idx = int((255 - b) / 255 * (len(RAMP) - 1))
            line.append(RAMP[idx])
        rows_text.append("".join(line).rstrip())

    width = int(COLS * CHAR_W) + 20
    height = int(ROWS * CHAR_H) + 20

    groups = []
    per_row = 0.06
    wipe_dur = 0.5
    for i, line in enumerate(rows_text):
        y = 14 + i * CHAR_H
        begin = i * per_row
        w = len(line) * CHAR_W
        clip_id = f"clip{i}"
        # A clip rect grows from width 0 -> full, wiping the row in.
        groups.append(
            f'<clipPath id="{clip_id}"><rect x="10" y="{y-CHAR_H}" '
            f'width="0" height="{CHAR_H+2}">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" '
            f'begin="{begin:.2f}s" dur="{wipe_dur}s" fill="freeze"/>'
            f'</rect></clipPath>'
            f'<text x="10" y="{y}" clip-path="url(#{clip_id})" '
            f'xml:space="preserve">{esc(line)}</text>'
            # cursor block riding the wipe edge
            f'<rect class="cur" x="10" y="{y-CHAR_H+1}" width="{CHAR_W:.1f}" '
            f'height="{CHAR_H}" opacity="0">'
            f'<animate attributeName="x" from="10" to="{10+w:.1f}" '
            f'begin="{begin:.2f}s" dur="{wipe_dur}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'begin="{begin:.2f}s" dur="{wipe_dur}s" fill="freeze"/>'
            f'</rect>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    text {{ font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace;
            font-size:{CHAR_H}px; fill:{FILL}; white-space:pre; letter-spacing:0; }}
    .bg {{ fill:#0d1117; }}
    .cur {{ fill:{FILL}; }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>
  {''.join(groups)}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT} ({COLS}x{ROWS})")


if __name__ == "__main__":
    main()
