#!/usr/bin/env python3
"""Build the neofetch-style info card as an animated SVG.

Colored key/value rows fade and slide in on a short stagger so the panel
looks like it is printing next to the portrait. Set STATIC=1 to emit a
frozen frame (handy for Quick Look previews).
"""
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# --- edit these -----------------------------------------------------------
HEADER = "dhruv@github"
LINES = [
    ("Role", "AI Engineer"),
    ("Focus", "Conversational AI · LLM agents · RAG"),
    ("AI", "LangChain · LangGraph · OpenAI · Anthropic"),
    ("Backend", "Python · FastAPI · Node.js"),
    ("Web", "Next.js · React · TypeScript · Tailwind"),
    ("Voice", "LiveKit · WebRTC"),
    ("Data", "MongoDB Atlas"),
    ("Cloud", "AWS · Docker · GitHub Actions"),
    ("Repos", "35 public"),
    ("Contact", "dhruvrajkotia999@gmail.com"),
]
# --------------------------------------------------------------------------

WIDTH = 520
PAD = 20
BAR_H = 30
LINE_H = 26
BG, BORDER = "#0d1117", "#30363d"
KEY, VAL, ACCENT, DIM = "#7ee787", "#c9d1d9", "#79c0ff", "#8b949e"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]
SWATCHES = ["#ff5f56", "#ffbd2e", "#27c93f", "#58a6ff", "#bc8cff", "#f778ba", "#7ee787", "#c9d1d9"]
MONO = "'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FONT_SIZE = 13
STAGGER, DUR, START = 0.12, 0.35, 0.3


def animated_group(index: int, inner: str) -> str:
    if STATIC:
        return f"<g>{inner}</g>"
    begin = START + index * STAGGER
    return (
        f'<g opacity="0" transform="translate(0,6)">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="{DUR}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" '
        f'begin="{begin:.2f}s" dur="{DUR}s" fill="freeze"/>{inner}</g>'
    )


def main() -> None:
    # header + separator + key/value lines + palette row
    n_rows = 2 + len(LINES) + 1
    height = BAR_H + PAD + n_rows * LINE_H + PAD - 6

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="About Dhruv">',
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<line x1="1" y1="{BAR_H}" x2="{WIDTH - 1}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(DOTS):
        parts.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2:.0f}" r="5.5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2:.0f}" y="{BAR_H / 2 + 3.5:.0f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{DIM}">dhruv@github: ~/whoami</text>'
    )

    y = BAR_H + PAD + 16
    row = 0

    parts.append(animated_group(row, (
        f'<text x="{PAD}" y="{y}" font-family="{MONO}" font-size="15" font-weight="bold" '
        f'fill="{ACCENT}">{escape(HEADER)}</text>'
    )))
    row += 1
    y += LINE_H

    parts.append(animated_group(row, (
        f'<text x="{PAD}" y="{y - 8}" font-family="{MONO}" font-size="{FONT_SIZE}" '
        f'fill="{DIM}">{"─" * 38}</text>'
    )))
    row += 1
    y += LINE_H - 8

    key_w = max(len(k) for k, _ in LINES)
    for key, value in LINES:
        label = f"{key}:".ljust(key_w + 2)
        parts.append(animated_group(row, (
            f'<text x="{PAD}" y="{y}" xml:space="preserve" font-family="{MONO}" '
            f'font-size="{FONT_SIZE}">'
            f'<tspan fill="{KEY}" font-weight="bold">{escape(label)}</tspan>'
            f'<tspan fill="{VAL}">{escape(value)}</tspan></text>'
        )))
        row += 1
        y += LINE_H

    swatches = "".join(
        f'<rect x="{PAD + i * 26}" y="{y - 12}" width="20" height="12" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    parts.append(animated_group(row, swatches))
    parts.append("</svg>")
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUT.name} ({WIDTH}x{height}, static={STATIC})")


if __name__ == "__main__":
    main()
