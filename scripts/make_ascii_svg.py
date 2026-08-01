#!/usr/bin/env python3
"""Convert the prepped portrait into a self-typing animated SVG.

Each pixel row becomes a line of monospace glyphs picked from a density
ramp. Every line is wrapped in a clip that wipes left-to-right with a
block cursor riding the edge, staggered top to bottom. SMIL only — no
JavaScript — so GitHub plays it inside an <img>. Prints once, freezes.
"""
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "portrait_prepped.png"
OUT = ROOT / "dhruv-ascii.svg"

COLS = 96
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); space = background
WHITE_CUTOFF = 205      # pixels this bright are background — print nothing
GAMMA = 0.72            # <1 brightens midtones so faces don't turn into mush
CW, CH = 4.8, 8.0       # character cell in px
FONT_SIZE = 8
PAD = 16
BAR_H = 30
BG, BORDER, FG = "#0d1117", "#30363d", "#c9d1d9"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]
ROW_DUR = 0.45          # seconds for one line to wipe in
ROW_STAGGER = 0.045     # delay between consecutive lines
START = 0.2
MONO = "'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def autocrop(img: Image.Image, threshold: int = 245, pad_frac: float = 0.04) -> Image.Image:
    """Crop away the white margins so the subject fills the grid."""
    mask = img.point(lambda v: 255 if v < threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return img
    pad = round(max(img.size) * pad_frac)
    left, top, right, bottom = bbox
    return img.crop((
        max(0, left - pad), max(0, top - pad),
        min(img.width, right + pad), min(img.height, bottom + pad),
    ))


def image_to_lines() -> list[str]:
    img = autocrop(Image.open(SRC).convert("L"))
    # a character cell is ~2x taller than wide, so halve the row count
    rows = max(1, round(COLS * img.height / img.width * 0.5))
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = img.load()
    lines = []
    for y in range(rows):
        chars = []
        for x in range(COLS):
            v = px[x, y]
            if v >= WHITE_CUTOFF:
                chars.append(" ")
                continue
            v = round(255 * (v / 255) ** GAMMA)
            idx = min(len(RAMP) - 1, (255 - v) * len(RAMP) // 256)
            chars.append(RAMP[max(1, idx)])
        lines.append(chars)
    return ["".join(row).rstrip() for row in despeckle(lines)]


def despeckle(grid: list[list[str]], min_size: int = 4) -> list[list[str]]:
    """Blank out tiny isolated glyph islands left over from the photo cutout."""
    rows, cols = len(grid), len(grid[0]) if grid else 0
    seen = [[False] * cols for _ in range(rows)]
    for sy in range(rows):
        for sx in range(cols):
            if seen[sy][sx] or grid[sy][sx] == " ":
                continue
            component, queue = [], [(sy, sx)]
            seen[sy][sx] = True
            while queue:
                y, x = queue.pop()
                component.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and not seen[ny][nx] \
                                and grid[ny][nx] != " ":
                            seen[ny][nx] = True
                            queue.append((ny, nx))
            if len(component) < min_size:
                for y, x in component:
                    grid[y][x] = " "
    return grid


def main() -> None:
    lines = image_to_lines()
    grid_w, grid_h = COLS * CW, len(lines) * CH
    width = grid_w + 2 * PAD
    height = BAR_H + grid_h + 2 * PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'xml:space="preserve" role="img" aria-label="ASCII portrait of Dhruv">',
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="12" fill="{BG}" '
        f'stroke="{BORDER}"/>',
        f'<line x1="1" y1="{BAR_H}" x2="{width - 1:.0f}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(DOTS):
        parts.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2:.0f}" r="5.5" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2:.0f}" y="{BAR_H / 2 + 3.5:.0f}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="#8b949e">dhruv@github: ~/portrait</text>'
    )

    top = BAR_H + PAD
    defs, body = [], []
    for r, line in enumerate(lines):
        if not line:
            continue
        begin = START + r * ROW_STAGGER
        end = begin + ROW_DUR
        row_w = len(line) * CW
        y_top = top + r * CH
        baseline = y_top + CH - 1.6
        defs.append(
            f'<clipPath id="c{r}"><rect x="{PAD}" y="{y_top:.1f}" width="0" height="{CH + 0.5}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(
            f'<text x="{PAD}" y="{baseline:.1f}" clip-path="url(#c{r})" xml:space="preserve" '
            f'font-family="{MONO}" font-size="{FONT_SIZE}" fill="{FG}" '
            f'textLength="{row_w:.1f}" lengthAdjust="spacingAndGlyphs">{escape(line)}</text>'
        )
        # block cursor riding the wipe edge, hidden once its row is done
        body.append(
            f'<rect x="{PAD}" y="{y_top:.1f}" width="{CW}" height="{CH}" fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + row_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>'
        )

    parts.append("<defs>" + "".join(defs) + "</defs>")
    parts.extend(body)
    parts.append("</svg>")
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(lines)} rows, {OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
