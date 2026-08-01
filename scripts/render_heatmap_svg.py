#!/usr/bin/env python3
"""Render data/contributions.json as an animated heatmap SVG.

53 weeks of rounded boxes that reveal themselves in a diagonal wave, with
month labels, a stats footer, and the classic Less->More legend. SMIL
only, terminal-card styling to match the other panels.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

CELL, GAP, RADIUS = 12, 3, 3
PAD = 16
BAR_H = 30
LABEL_W = 30           # Mon/Wed/Fri gutter
LABEL_H = 20           # month row
BG, BORDER, DIM, FG = "#0d1117", "#30363d", "#8b949e", "#c9d1d9"
LEVEL_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]
MONO = "'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
WEEK_DELAY, DAY_DELAY, DUR, START = 0.018, 0.04, 0.3, 0.2
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main() -> None:
    payload = json.loads(SRC.read_text())
    days, stats = payload["days"], payload["stats"]

    first = dt.date.fromisoformat(days[0]["date"])
    first_sunday = first - dt.timedelta(days=first.isoweekday() % 7)
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - first_sunday).days // 7 + 1

    grid_w = weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = PAD + LABEL_W + grid_w + PAD
    height = BAR_H + LABEL_H + grid_h + 40 + PAD

    x0, y0 = PAD + LABEL_W, BAR_H + LABEL_H + 6

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="GitHub contribution calendar, {stats["total"]} contributions in the last year">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<line x1="1" y1="{BAR_H}" x2="{width - 1}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(DOTS):
        parts.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2:.0f}" r="5.5" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2:.0f}" y="{BAR_H / 2 + 3.5:.0f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{DIM}">dhruv@github: ~/contributions --last-year</text>'
    )

    # month labels: mark each column where the month changes, but never
    # closer than 3 columns to the previous label (avoids overlap at the edges)
    seen_month = None
    last_label_w = -10
    for w in range(weeks):
        week_start = first_sunday + dt.timedelta(weeks=w)
        if week_start.month != seen_month:
            seen_month = week_start.month
            if w - last_label_w < 3:
                continue
            last_label_w = w
            parts.append(
                f'<text x="{x0 + w * (CELL + GAP)}" y="{BAR_H + LABEL_H - 4}" '
                f'font-family="{MONO}" font-size="10" fill="{DIM}">{MONTHS[week_start.month - 1]}</text>'
            )
    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(
            f'<text x="{PAD}" y="{y0 + row * (CELL + GAP) + CELL - 2}" '
            f'font-family="{MONO}" font-size="10" fill="{DIM}">{label}</text>'
        )

    by_date = {d["date"]: d for d in days}
    for w in range(weeks):
        for row in range(7):
            date = first_sunday + dt.timedelta(weeks=w, days=row)
            day = by_date.get(date.isoformat())
            if day is None:
                continue
            x = x0 + w * (CELL + GAP)
            y = y0 + row * (CELL + GAP)
            begin = START + w * WEEK_DELAY + row * DAY_DELAY
            color = LEVEL_COLORS[day["level"]]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RADIUS}" '
                f'fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" '
                f'dur="{DUR}s" fill="freeze"/></rect>'
            )

    # stats footer + legend
    footer_y = y0 + grid_h + 24
    best = stats["best_day"]
    footer = (
        f'{stats["total"]:,} contributions in the last year   ·   '
        f'current streak {stats["current_streak"]}d   ·   '
        f'longest {stats["longest_streak"]}d   ·   '
        f'best day {best["count"]}'
    )
    parts.append(
        f'<text x="{PAD + LABEL_W}" y="{footer_y}" font-family="{MONO}" font-size="11" '
        f'fill="{FG}" opacity="0">{footer}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{START + 1.2:.2f}s" '
        f'dur="0.5s" fill="freeze"/></text>'
    )
    legend_x = width - PAD - 5 * (CELL + GAP) - 66
    parts.append(
        f'<text x="{legend_x - 6}" y="{footer_y}" text-anchor="end" font-family="{MONO}" '
        f'font-size="10" fill="{DIM}">Less</text>'
    )
    for i, color in enumerate(LEVEL_COLORS):
        parts.append(
            f'<rect x="{legend_x + i * (CELL + GAP)}" y="{footer_y - CELL + 2}" width="{CELL}" '
            f'height="{CELL}" rx="{RADIUS}" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{legend_x + 5 * (CELL + GAP) + 6}" y="{footer_y}" font-family="{MONO}" '
        f'font-size="10" fill="{DIM}">More</text>'
    )
    parts.append("</svg>")
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUT.name} ({width}x{height}, {weeks} weeks)")


if __name__ == "__main__":
    main()
