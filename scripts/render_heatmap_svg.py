#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap SVG.

Boxes slide in diagonally (line after line) once on load, then freeze — no loop.
Pure SVG + CSS keyframes so GitHub renders the animation.
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none  ->  brightest (level 5 is a neon top end)

CELL = 13     # box size
GAP = 3       # gap between boxes
PAD = 22      # outer padding
TOP = 42      # room for the title / month labels
LEGEND_H = 26
FOOTER_H = 30

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count, level):
    if count <= 0 and level <= 0:
        return 0
    if level >= 4:
        return 5 if count >= 20 else 4
    return max(1, min(5, level))


def build_weeks(days):
    """Group days into GitHub-style columns of 7 (Sun..Sat)."""
    if not days:
        return []
    # Pad the front so the first column starts on Sunday.
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead = (first.weekday() + 1) % 7  # Python Mon=0; GitHub weeks start Sunday
    cells = [None] * lead + days
    weeks = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    return weeks


def main():
    payload = json.loads(DATA.read_text())
    days = payload["days"]
    stats = payload.get("stats", {})
    weeks = build_weeks(days)

    n_weeks = len(weeks)
    grid_w = n_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = grid_w + PAD * 2
    height = TOP + grid_h + LEGEND_H + FOOTER_H + PAD

    rects = []
    delay_step = 0.012  # diagonal stagger
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = PAD + wi * (CELL + GAP)
            y = TOP + di * (CELL + GAP)
            if day is None:
                continue
            lvl = level_for(day.get("count", 0), day.get("level", 0))
            fill = PALETTE[lvl]
            delay = (wi + di) * delay_step
            title = f'{day["count"]} on {day["date"]}'
            rects.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="3" ry="3" fill="{fill}" style="animation-delay:{delay:.3f}s">'
                f'<title>{title}</title></rect>'
            )

    # Month labels along the top
    month_labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        first_day = next((d for d in week if d), None)
        if not first_day:
            continue
        m = int(first_day["date"][5:7])
        if m != last_month:
            last_month = m
            x = PAD + wi * (CELL + GAP)
            month_labels.append(
                f'<text x="{x}" y="{TOP - 8}" class="mlabel">{MONTHS[m-1]}</text>'
            )

    # Legend
    legend_y = TOP + grid_h + 20
    legend = [f'<text x="{PAD}" y="{legend_y+11}" class="legend">Less</text>']
    lx = PAD + 40
    for i, c in enumerate(PALETTE):
        legend.append(
            f'<rect x="{lx + i*(CELL+GAP)}" y="{legend_y}" width="{CELL}" '
            f'height="{CELL}" rx="3" fill="{c}"/>'
        )
    legend.append(
        f'<text x="{lx + len(PALETTE)*(CELL+GAP) + 6}" y="{legend_y+11}" '
        f'class="legend">More</text>'
    )

    total = stats.get("total", sum(d["count"] for d in days))
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_y = legend_y + LEGEND_H + 6
    footer = (
        f'<text x="{PAD}" y="{footer_y}" class="footer">'
        f'{total:,} contributions in the last year'
        f'  •  \U0001f525 {streak}d current  •  ⚡ {longest}d longest'
        f'</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="'JetBrains Mono','SFMono-Regular',Consolas,monospace">
  <style>
    .bg {{ fill:#0d1117; }}
    .c {{ opacity:0; transform:translateY(-6px); animation:pop .45s ease-out forwards; }}
    @keyframes pop {{ to {{ opacity:1; transform:translateY(0); }} }}
    .title {{ fill:#c9d1d9; font-size:14px; font-weight:700; }}
    .mlabel {{ fill:#8b949e; font-size:10px; }}
    .legend {{ fill:#8b949e; font-size:11px; }}
    .footer {{ fill:#39d353; font-size:12px; font-weight:600; }}
    text {{ font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace; }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>
  <text x="{PAD}" y="24" class="title">contributions — @{payload["username"]}</text>
  {''.join(month_labels)}
  {''.join(rects)}
  {''.join(legend)}
  {footer}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT} ({n_weeks} weeks, {total:,} contributions)")


if __name__ == "__main__":
    main()
