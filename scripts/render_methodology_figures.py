"""Render researcher-facing vector methodology figures; never launch experiments.

Requires ReportLab and pdftoppm (both available in the bundled document runtime).
Run with that runtime's Python. Existing output files are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

WIDTH = 1000
HEIGHT = 740
INK = "#18242F"
MUTED = "#4B5864"
BLUE = "#245777"
PALE = "#F1F6F9"
PRIVATE = "#F7F3EE"


class Figure:
    """Top-origin drawing helpers with text-bound checks for paper figures."""

    def __init__(self, title: str, subtitle: str) -> None:
        self.drawing = Drawing(WIDTH, HEIGHT)
        self.drawing.add(Rect(0, 0, WIDTH, HEIGHT, fillColor=HexColor("#FFFFFF"), strokeColor=None))
        self.text(40, 35, title, 23, bold=True)
        self.text(40, 65, subtitle, 13, color=MUTED)

    def text(self, x: float, top: float, value: str, size: float = 14,
             *, bold: bool = False, color: str = INK, max_width: float | None = None) -> None:
        font = "Helvetica-Bold" if bold else "Helvetica"
        width = stringWidth(value, font, size)
        if max_width is not None and width > max_width:
            raise ValueError(f"Text exceeds allocated width: {value!r} ({width:.1f}>{max_width})")
        if x < 0 or x + width > WIDTH or top < 0 or top + size > HEIGHT:
            raise ValueError(f"Text outside figure: {value!r}")
        self.drawing.add(String(x, HEIGHT - top - size, value,
                                fontName=font, fontSize=size, fillColor=HexColor(color)))

    def box(self, x: float, top: float, width: float, height: float,
            title: str, lines: list[str], *, fill: str = PALE,
            size: float = 13, title_size: float = 16) -> None:
        self.drawing.add(Rect(x, HEIGHT - top - height, width, height,
                              rx=6, ry=6, fillColor=HexColor(fill),
                              strokeColor=HexColor(BLUE), strokeWidth=1.2))
        self.text(x + 16, top + 12, title, title_size, bold=True, max_width=width - 32)
        for index, line in enumerate(lines):
            baseline_top = top + 38 + index * (size + 5)
            if baseline_top + size > top + height - 8:
                raise ValueError(f"Text outside box: {line!r}")
            self.text(x + 16, baseline_top, line, size, max_width=width - 32)

    def border(self, x: float, top: float, width: float, height: float,
               *, fill: str, dashed: bool = False) -> None:
        self.drawing.add(Rect(x, HEIGHT - top - height, width, height,
                              rx=8, ry=8, fillColor=HexColor(fill),
                              strokeColor=HexColor(MUTED), strokeWidth=1.2,
                              strokeDashArray=[5, 4] if dashed else None))

    def arrow(self, points: list[tuple[float, float]], *, color: str = MUTED,
              dashed: bool = False, head: bool = True) -> None:
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            self.drawing.add(Line(x1, HEIGHT-y1, x2, HEIGHT-y2,
                                  strokeColor=HexColor(color), strokeWidth=1.5,
                                  strokeDashArray=[4, 3] if dashed else None))
        if head:
            x1, y1 = points[-2]
            x2, y2 = points[-1]
            angle = math.atan2(y2-y1, x2-x1)
            coords = [x2, HEIGHT-y2]
            for offset in (-0.5, 0.5):
                coords.extend([x2 - 9*math.cos(angle+offset), HEIGHT-(y2 - 9*math.sin(angle+offset))])
            self.drawing.add(Polygon(coords, fillColor=HexColor(color), strokeColor=None))


def methodology() -> Figure:
    f = Figure("Controlled evidence methodology", "Single-case pilot: 1 RepoPairBench scenario x 3 evidence conditions x 2 harnesses")
    f.box(40, 100, 435, 82, "1  Paired repository source", ["Scenario 24e78349 / iRedAdmin", "Vulnerable + fixed snapshots: researcher inspection"], fill=PRIVATE)
    f.box(525, 100, 435, 82, "2  Researcher validation", ["Scoped label, threat model and evidence dependency", "Fixed source and answer key stay researcher-only"], fill=PRIVATE)
    f.arrow([(475, 141), (525, 141)])
    f.box(40, 223, 920, 66, "3  Deterministic condition construction", ["Unchanged vulnerable target; physical source copies; SHA-256 manifests; leakage and boundary checks"])
    f.arrow([(742, 182), (742, 223)])
    cols = [(40, "E1  Sufficient initially", ["Expanded initial source packet", "Context also available in workspace", "19 files / 22 initial items"]),
            (355, "E2  Retrievable context", ["Shared limited initial packet", "Missing context can be read", "19 files / 4 initial items"]),
            (670, "E3  Unavailable context", ["Same initial packet as E2", "Renderer and templates omitted", "13 files / 4 initial items"])]
    for x, title, lines in cols:
        f.box(x, 332, 290, 119, title, lines)
        f.arrow([(500, 289), (500, 310), (x+145, 310), (x+145, 332)])
    f.text(40, 468, "CONTROL A: E1/E2 source identical", 13, bold=True, color=BLUE)
    f.text(510, 468, "CONTROL B: E2/E3 initial evidence identical", 13, bold=True, color=BLUE)
    for x, _, _ in cols:
        f.arrow([(x+145, 451), (x+145, 460), (500, 460)], head=False)
    f.box(40, 512, 920, 80, "4  Fresh sessions in six experimental cells", ["Same frozen task instructions; Qwen Code 0.24.6 or OpenCode 1.18.30", "Same qwen3.5:9b-q4_K_M via Ollama; 16,384-token configured context; read-only source tools"])
    f.arrow([(500, 460), (500, 512)])
    f.box(40, 627, 435, 69, "5  Preserve and normalize", ["Raw traces + answers; mechanical metrics"], size=14)
    f.box(525, 627, 435, 69, "6  Researcher scoring", ["Recognition / acquisition / abstention / grounding"], size=13)
    f.arrow([(257, 592), (257, 627)])
    f.arrow([(475, 661), (525, 661)])
    f.text(40, 712, "Six draft cells; eight recorded attempts retained. No replicated sampling or harness ranking.", 12, color=MUTED)
    return f


def architecture() -> Figure:
    f = Figure("Execution architecture and evidence boundary", "Researcher-only preparation is separated from the evidence available to each experimental agent")
    f.border(40, 105, 260, 415, fill=PRIVATE, dashed=True)
    f.text(57, 124, "RESEARCHER-ONLY", 16, bold=True, max_width=226)
    f.text(57, 148, "Outside every agent workspace", 12, color=MUTED)
    f.text(57, 167, "No agent access to answer key", 11, bold=True, color=BLUE, max_width=226)
    f.box(57, 188, 226, 83, "Paired snapshots", ["Vulnerable / fixed source", "Patch and metadata"], fill="#FFFFFF", size=12)
    f.box(57, 297, 226, 83, "Validated scenario card", ["Threat model and scoped label", "Evidence manifest / allowlist"], fill="#FFFFFF", size=12, title_size=14)
    f.box(57, 406, 226, 83, "Scoring reference", ["Source-based rationale", "Researcher judgments"], fill="#FFFFFF", size=12)
    f.border(340, 105, 620, 310, fill="#FFFFFF")
    f.text(357, 124, "CONFINED RUN: ONE FRESH HARNESS SESSION", 16, bold=True, max_width=586)
    f.text(357, 148, "Condition source read-only; isolated runtime home writable", 12, color=MUTED)
    f.box(357, 188, 269, 78, "Initial source packet", ["Frozen task + condition evidence", "No researcher labels or fix"], size=12, title_size=15)
    f.box(674, 188, 269, 78, "Condition workspace", ["One of E1 / E2 / E3", "Only allowed vulnerable-source files"], size=12, title_size=15)
    f.box(357, 313, 269, 83, "Agent harness", ["Qwen Code OR OpenCode", "Own orchestration / native tool schema"], size=12, title_size=15)
    f.box(674, 313, 269, 83, "Read-only tool interface", ["Read / search / list", "Requests, results and errors recorded"], size=12, title_size=15)
    f.arrow([(491, 266), (491, 313)])
    f.arrow([(809, 313), (809, 266)])
    f.arrow([(900, 266), (900, 313)])
    f.arrow([(626, 351), (674, 351)])
    f.arrow([(674, 377), (626, 377)])
    f.box(357, 438, 586, 62, "Shared inference service (outside agent process)", ["Ollama / qwen3.5:9b-q4_K_M / configured context 16,384"], size=13, title_size=15)
    f.arrow([(491, 396), (491, 438)])
    f.arrow([(605, 438), (605, 396)])
    f.text(345, 538, "OS + tool policy deny private files, sibling conditions and workspace writes.", 12, color=MUTED)
    f.box(340, 585, 620, 67, "External collection and mechanical normalization", ["Raw stdout / stderr / metadata / final text -> preserved traces and draft CSV"], size=12)
    f.arrow([(943, 396), (952, 396), (952, 565), (650, 565), (650, 585)])
    f.box(40, 679, 920, 49, "Researcher review: source + observed trace -> manual scores with citations", [], fill=PRIVATE, title_size=16)
    f.arrow([(650, 652), (650, 679)])
    f.arrow([(170, 520), (170, 679)], dashed=True)
    return f


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1]/"docs"/"figures")
    parser.add_argument("--dpi", type=int, default=216, help="Raster preview DPI; vector exports retain editable text")
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise SystemExit("pdftoppm is required for figure previews; no dependency is installed automatically")
    output = args.output_dir.resolve()
    names = ["pilot_methodology", "pilot_architecture"]
    planned = [output/f"{name}.{ext}" for name in names for ext in ("pdf", "svg", "png")]
    planned.append(output/"figure_manifest.json")
    if any(p.exists() for p in planned):
        raise SystemExit("Refusing to overwrite a figure; choose a new --output-dir")
    output.mkdir(parents=True, exist_ok=True)
    for name, figure in zip(names, (methodology(), architecture())):
        renderPDF.drawToFile(figure.drawing, str(output/f"{name}.pdf"), title=name.replace("_", " "))
        renderSVG.drawToFile(figure.drawing, str(output/f"{name}.svg"))
        subprocess.run([renderer, "-singlefile", "-r", str(args.dpi), "-png",
                        str(output/f"{name}.pdf"), str(output/name)], check=True, capture_output=True)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audience": "RESEARCHER_ONLY",
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canvas_points": [WIDTH, HEIGHT], "preview_dpi": args.dpi,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in planned[:-1]},
        "scope": "Design and execution architecture only; no scientific scores or model conclusions",
    }
    with planned[-1].open("x") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"Created two vector figures and raster previews in {output}")


if __name__ == "__main__":
    main()
