#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints line by line.

Edit the ROWS / HEADER below to change the content — the graph already covers
your GitHub stats, so keep this for the story the numbers can't tell.

STATIC=1 emits a frozen frame (for local Quick Look previews).
"""
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ---- content ---------------------------------------------------------------
USER = "bhavik@vocallabs"
HEADER_ART = [
    "     ___      ",
    "    ( o.o )   ",
    "     > ^ <    ",
]
ROWS = [
    ("Now",        "Engineer @ VocalLabs — voice AI"),
    ("Prev",       "Systems / backend, C++ & Go"),
    ("Stack",      " · C++ · TypeScript · LLMs"),
    ("Focus",      "Vector DBs · voice agents · infra"),
    ("Highlights", "Building Vector-DB-CPP from scratch"),
    ("Contact",    "tarun@vocallabs.ai"),
]
# ---------------------------------------------------------------------------

KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
ART_COLOR = "#58a6ff"
DIM = "#8b949e"

LINE_H = 22
PAD = 20
TOP = 46
CHAR_W = 8.2
WIDTH = 490
HEIGHT = TOP + (len(HEADER_ART) + len(ROWS) + 2) * LINE_H + PAD


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    lines = []
    y = TOP
    delay = 0.0
    step = 0.11

    def emit(svg_frag):
        nonlocal delay
        anim = "" if STATIC else f'style="animation-delay:{delay:.2f}s"'
        cls = "" if STATIC else 'class="ln"'
        lines.append(f'<g {cls} {anim}>{svg_frag}</g>')
        delay += step

    # Title bar: user@host + a rule
    emit(f'<text x="{PAD}" y="{y}" class="user">{esc(USER)}</text>'
         f'<text x="{PAD + len(USER)*CHAR_W + 6}" y="{y}" class="dim">~ neofetch</text>')
    y += LINE_H
    emit(f'<line x1="{PAD}" y1="{y-14}" x2="{WIDTH-PAD}" y2="{y-14}" class="rule"/>')
    y += 6

    # ASCII header art
    for art in HEADER_ART:
        emit(f'<text x="{PAD}" y="{y}" class="art" xml:space="preserve">{esc(art)}</text>')
        y += LINE_H

    y += 4
    # key/value rows
    key_w = max(len(k) for k, _ in ROWS)
    for k, v in ROWS:
        key = k.ljust(key_w)
        emit(
            f'<text x="{PAD}" y="{y}" xml:space="preserve">'
            f'<tspan class="key">{esc(key)}</tspan>'
            f'<tspan class="dim"> : </tspan>'
            f'<tspan class="val">{esc(v)}</tspan></text>'
        )
        y += LINE_H

    anim_css = "" if STATIC else '''
    .ln { opacity:0; transform:translateX(-8px);
          animation:slidein .4s ease-out forwards; }
    @keyframes slidein { to { opacity:1; transform:translateX(0); } }'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{int(HEIGHT)}" viewBox="0 0 {WIDTH} {int(HEIGHT)}">
  <style>
    text {{ font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace; font-size:13px; }}
    .bg {{ fill:#0d1117; }}
    .user {{ fill:{KEY_COLOR}; font-weight:700; font-size:14px; }}
    .art  {{ fill:{ART_COLOR}; font-size:13px; }}
    .key  {{ fill:{KEY_COLOR}; font-weight:700; }}
    .val  {{ fill:{VAL_COLOR}; }}
    .dim  {{ fill:{DIM}; }}
    .rule {{ stroke:#21262d; stroke-width:1; }}{anim_css}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{int(HEIGHT)}" rx="10"/>
  {''.join(lines)}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT}{' (static)' if STATIC else ''}")


if __name__ == "__main__":
    main()
