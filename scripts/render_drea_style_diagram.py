"""Draw a DREA-inspired presentation of the existing pilot; no experiment access.

Requires the bundled ReportLab runtime, Times New Roman fonts and pdftoppm.
All exports are researcher-facing. Existing output files are never overwritten.
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
from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, PolyLine, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WIDTH, HEIGHT = 1400, 875
INK = "#23232B"
GREEN, GREEN_EDGE = "#EFF3EC", "#B5C0AF"
BLUE, BLUE_EDGE = "#DEE5F3", "#A6B2C9"
TAN, TAN_EDGE = "#F2E7D6", "#BCA58B"
PURPLE, PURPLE_EDGE = "#E9DFF0", "#AE9BBC"
ARROW, ARROW_EDGE = "#D6E6FB", "#7A9AC8"
REFERENCE = "https://github.com/huhusmang/DREA/blob/main/figures/fig2_DREA.png"


class Diagram:
    def __init__(self, font_dir: Path) -> None:
        for name, file in (("PaperSerif", "Times New Roman.ttf"),
                           ("PaperSerif-Bold", "Times New Roman Bold.ttf")):
            pdfmetrics.registerFont(TTFont(name, str(font_dir/file)))
        self.d = Drawing(WIDTH, HEIGHT)
        self.d.add(Rect(0, 0, WIDTH, HEIGHT, fillColor=HexColor("#FFFFFF"), strokeColor=None))

    def text(self, x: float, top: float, value: str, size: float = 18,
             *, bold: bool = False, width: float | None = None,
             center: bool = False, color: str = INK) -> None:
        font = "PaperSerif-Bold" if bold else "PaperSerif"
        measured = pdfmetrics.stringWidth(value, font, size)
        if width is not None and measured > width:
            raise ValueError(f"Text does not fit: {value!r} ({measured:.1f}>{width})")
        left = x-measured/2 if center else x
        if left < 0 or left+measured > WIDTH or top < 0 or top+size > HEIGHT:
            raise ValueError(f"Text outside page: {value!r}")
        self.d.add(String(x, HEIGHT-top-size, value, fontName=font, fontSize=size,
                          textAnchor="middle" if center else "start", fillColor=HexColor(color)))

    def box(self, x: float, top: float, w: float, h: float,
            fill: str, edge: str, radius: float = 24, *, dashed: bool = False) -> None:
        self.d.add(Rect(x, HEIGHT-top-h, w, h, rx=radius, ry=radius,
                        fillColor=HexColor(fill), strokeColor=HexColor(edge), strokeWidth=1.5,
                        strokeDashArray=[7, 5] if dashed else None))

    def pill(self, x: float, top: float, w: float, h: float, text: str,
             *, size: float = 19) -> None:
        self.box(x, top, w, h, "#FAFBFE", "#FAFBFE", 7)
        self.text(x+w/2, top+(h-size)/2-1, text, size, center=True, width=w-20)

    def arrow(self, points: list[tuple[float, float]], *, fill: str = ARROW,
              edge: str = ARROW_EDGE, width: float = 10) -> None:
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        angle = math.atan2(y2-y1, x2-x1)
        length = width*1.7
        base = (x2-length*math.cos(angle), y2-length*math.sin(angle))
        path = points[:-1]+[base]
        coords = [v for x, y in path for v in (x, HEIGHT-y)]
        self.d.add(PolyLine(coords, strokeColor=HexColor(edge), strokeWidth=width+2,
                            strokeLineJoin=0))
        self.d.add(PolyLine(coords, strokeColor=HexColor(fill), strokeWidth=width,
                            strokeLineJoin=0))
        vertices = [x2, HEIGHT-y2]
        for sign in (-1, 1):
            vertices.extend([base[0]+sign*width*math.sin(angle),
                             HEIGHT-(base[1]-sign*width*math.cos(angle))])
        self.d.add(Polygon(vertices, fillColor=HexColor(fill), strokeColor=HexColor(edge), strokeWidth=1.2))

    def code_icon(self, x: float, top: float) -> None:
        self.box(x, top, 42, 48, "#FFFDF8", BLUE_EDGE, 3)
        self.text(x+21, top+9, "{ }", 24, center=True, bold=True, color="#506984")
        for dy, w in ((37, 26), (42, 18)):
            self.d.add(Line(x+8, HEIGHT-top-dy, x+8+w, HEIGHT-top-dy,
                            strokeColor=HexColor(BLUE_EDGE), strokeWidth=1.5))

    def repo_icon(self, x: float, top: float) -> None:
        self.box(x, top, 42, 34, "#E0C28A", TAN_EDGE, 4)
        self.box(x+2, top-5, 20, 10, "#E0C28A", TAN_EDGE, 3)
        for dx, dy in ((8, 10), (21, 18), (32, 8)):
            self.d.add(Circle(x+dx, HEIGHT-top-dy, 2.5, fillColor=HexColor("#786246"), strokeColor=None))
        self.d.add(Line(x+8, HEIGHT-top-10, x+21, HEIGHT-top-18, strokeColor=HexColor("#786246")))
        self.d.add(Line(x+21, HEIGHT-top-18, x+32, HEIGHT-top-8, strokeColor=HexColor("#786246")))


def build(font_dir: Path) -> Drawing:
    f = Diagram(font_dir)
    f.text(30, 20, "Controlled Evidence Acquisition and Explanation Grounding", 30, bold=True)
    f.text(30, 61, "RepoPairBench pilot: one scenario x three evidence conditions x two harnesses", 18, color="#5C5B65")

    # Left: agent-visible evidence, never paired fixed source or researcher metadata.
    f.box(30, 110, 290, 606, GREEN, GREEN_EDGE, 34)
    f.repo_icon(51, 149)
    f.text(116, 137, "Controlled", 28, bold=True)
    f.text(116, 171, "Source Evidence", 25, bold=True, width=188)
    f.box(50, 232, 250, 94, "#FFFFFF", GREEN_EDGE, 16)
    f.code_icon(65, 254)
    f.text(119, 246, "Unchanged target", 20, bold=True, width=165)
    f.text(119, 275, "Log.GET", 19)
    f.text(66, 300, "controllers/panel/log.py", 14, width=218)
    f.text(175, 346, "Evidence conditions", 22, bold=True, center=True, width=258)
    for top, title, desc in ((383, "E1: context supplied", "Sufficient initial source packet"),
                             (467, "E2: context retrievable", "Limited packet + available context"),
                             (551, "E3: context unavailable", "Same packet; output context absent")):
        f.box(50, top, 250, 68, "#DCE8D6", GREEN_EDGE, 15)
        f.text(175, top+9, title, 20, bold=True, center=True, width=228)
        f.text(175, top+39, desc, 15, center=True, width=228)
    f.text(175, 646, "Same frozen task instructions", 17, center=True, width=254)
    f.text(175, 674, "Allowed source files only", 17, center=True)

    # Middle: a conceptual loop in one agent session, not DREA's two-model roles.
    f.box(365, 110, 650, 606, "#FAFAFC", "#A8A9B2", 38, dashed=True)
    f.text(690, 128, "Agent Runtime", 30, bold=True, center=True)
    f.text(690, 167, "Qwen Code OR OpenCode - one fresh session", 18, center=True)
    f.box(402, 203, 576, 64, BLUE, BLUE_EDGE, 16)
    f.text(690, 212, "Shared model: qwen3.5:9b-q4_K_M", 21, bold=True, center=True)
    f.text(690, 240, "Ollama endpoint / configured context: 16,384", 16, center=True)
    f.box(402, 297, 310, 193, BLUE, BLUE_EDGE, 30)
    f.text(557, 311, "Assessment & Stopping", 23, bold=True, center=True, width=280)
    f.pill(417, 356, 280, 33, "Reason over available evidence", size=18)
    f.pill(417, 399, 280, 33, "Request context when needed", size=18)
    f.pill(417, 442, 280, 33, "Conclude or state uncertainty", size=18)
    f.box(402, 539, 310, 127, BLUE, BLUE_EDGE, 27)
    f.text(557, 551, "Repository Navigation", 23, bold=True, center=True, width=280)
    f.pill(417, 592, 280, 28, "Read-only tools", size=18)
    f.pill(417, 629, 280, 26, "Read / glob / grep / list", size=17)
    f.box(766, 480, 230, 186, BLUE, BLUE_EDGE, 28)
    f.text(881, 493, "Returned Evidence", 23, bold=True, center=True, width=210)
    f.pill(780, 536, 202, 30, "Source excerpts", size=18)
    f.pill(780, 577, 202, 30, "Search matches", size=18)
    f.pill(780, 618, 202, 30, "Errors / absent paths", size=17)
    f.arrow([(320, 393), (402, 393)], fill="#D9E8CC", edge="#90AF78")
    f.arrow([(557, 490), (557, 539)])
    f.arrow([(712, 626), (766, 626)])
    f.arrow([(881, 480), (881, 423), (712, 423)])
    f.text(784, 448, "Tool results", 16, width=85)
    f.text(690, 687, "Read-only workspace; no private-reference access", 16, center=True, width=600)

    # Right: requested answer structure and manual evaluation of every pilot cell.
    f.box(1060, 110, 310, 249, TAN, TAN_EDGE, 32)
    f.text(1215, 132, "Final Assessment", 28, bold=True, center=True)
    f.box(1077, 190, 126, 67, "#FFFAF3", TAN_EDGE, 12)
    f.box(1227, 190, 126, 67, "#FFFAF3", TAN_EDGE, 12)
    f.text(1140, 209, "Verdict", 23, center=True)
    f.text(1215, 209, "+", 24, center=True)
    f.text(1290, 209, "Rationale", 23, center=True)
    f.text(1215, 276, "Evidence used + unresolved gaps", 17, center=True, width=280)
    f.text(1215, 310, "Vulnerable / Not vulnerable /", 16, center=True)
    f.text(1215, 332, "Insufficient evidence", 16, center=True)
    f.arrow([(712, 329), (1060, 329)], fill="#F6EBD7", edge=ARROW_EDGE, width=11)
    f.text(871, 302, "Model output", 17, center=True)
    f.box(1060, 420, 310, 296, PURPLE, PURPLE_EDGE, 34)
    f.text(1215, 437, "Human Evaluation", 25, bold=True, center=True, width=280)
    f.text(1215, 476, "All six cells; manual scoring", 17, center=True)
    f.box(1078, 511, 274, 121, "#F8F4FB", PURPLE_EDGE, 14)
    for top, text in ((522, "Recognition of evidence gaps"), (548, "Evidence acquisition"),
                      (574, "Appropriate abstention"), (600, "Explanation grounding")):
        f.text(1215, top, text, 18, center=True, width=246)
    f.text(1215, 649, "Unsupported claims + trace citations", 16, center=True, width=280)
    f.text(1215, 682, "Trace-grounded human scoring", 16, center=True, width=280)
    f.arrow([(1215, 359), (1215, 420)], fill="#F4E5D5", edge=PURPLE_EDGE, width=12)

    # External log/reference paths go to evaluation, never into the agent loop.
    f.box(365, 733, 650, 29, "#F4F6FA", BLUE_EDGE, 6)
    f.text(690, 737, "Raw traces + final text -> separate mechanical normalization", 17, center=True, width=620)
    f.arrow([(1015, 747), (1041, 747), (1041, 648), (1060, 648)], width=5)
    f.box(30, 777, 930, 62, GREEN, GREEN_EDGE, 17)
    f.text(50, 785, "Private Evaluation Reference", 22, bold=True)
    f.text(50, 814, "Paired source, scoped label, patch and scoring rationale - never given to agents", 16, width=890)
    f.arrow([(960, 808), (1215, 808), (1215, 716)], fill="#D9E8CC", edge="#90AF78", width=11)
    f.text(985, 779, "Reference for scoring", 16, width=250)
    f.text(30, 851, "Conceptual workflow; navigation is optional in E1. Appearance adapted from DREA Fig. 2; no scientific scores are shown.", 13, width=1340, color="#5C5B65")
    return f.d


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1]/"docs"/"figures")
    parser.add_argument("--font-dir", type=Path, default=Path("/System/Library/Fonts/Supplemental"))
    parser.add_argument("--dpi", type=int, default=216)
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise SystemExit("pdftoppm is required; dependencies will not be installed automatically")
    output = args.output_dir.resolve()
    paths = [output/f"pilot_drea_style.{ext}" for ext in ("pdf", "svg", "png")]
    manifest = output/"pilot_drea_style_manifest.json"
    if any(p.exists() for p in [*paths, manifest]):
        raise SystemExit("Refusing to overwrite existing outputs; choose a new --output-dir")
    drawing = build(args.font_dir.resolve())
    output.mkdir(parents=True, exist_ok=True)
    renderPDF.drawToFile(drawing, str(paths[0]), title="Controlled evidence pilot - DREA-inspired diagram")
    renderSVG.drawToFile(drawing, str(paths[1]))
    # Keep SVG text editable and portable to systems with ordinary serif fonts.
    svg = paths[1].read_text()
    svg = svg.replace("font-family: PaperSerif-Bold", "font-family: 'Times New Roman', Times, serif; font-weight: bold")
    svg = svg.replace("font-family: PaperSerif", "font-family: 'Times New Roman', Times, serif")
    paths[1].write_text(svg)
    subprocess.run([renderer, "-singlefile", "-r", str(args.dpi), "-png", str(paths[0]),
                    str(output/"pilot_drea_style")], check=True, capture_output=True)
    record = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reference_figure": REFERENCE,
        "adaptation": "Visual organization only; single-model pilot and private researcher boundary retained",
        "audience": "RESEARCHER_ONLY", "canvas_points": [WIDTH, HEIGHT], "preview_dpi": args.dpi,
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }
    with manifest.open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"Created PDF, SVG, PNG and provenance manifest in {output}")


if __name__ == "__main__":
    main()
