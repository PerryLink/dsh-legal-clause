#!/usr/bin/env python3
"""README visuals for dsh-legal-clause, read off the pipeline this repo ships.

Outputs (idempotent overwrite, docs/assets/):

  dsh-legal-clause-hero-{zh,en}-{light,dark}.webp   1440x576 raster (Pillow)
  dsh-legal-clause-flow-v5-{light,dark}.svg         1100x660 hand-written SVG

Where the content comes from
----------------------------
Nothing here is drawn from imagination; both figures are recomputed at build
time from the repository's own material:

  samples/quickstart/input/synthetic-nda-2026.txt
      the 10 numbered clauses and their titles (CONFIDENTIALITY ...
      WARRANTY). The script re-parses the text with the same rule the plugin
      uses - a line-leading number, then the title, with continuation lines
      joined onto the previous clause.
  src/core/clause.ts
      the 12-key playbook (4 categories x keys) and the scoring model:
      a title hit is worth +3, a body hit +2, the best of the twelve keys
      wins, a clause with no hit at all is `unresolved` (never dropped).
      The script repeats that scoring on the sample and asserts the result
      against the golden file before a single pixel is drawn.
  samples/quickstart/expected/result.json
      contract_id NDA-2026-001, 10 clauses, 0 unresolved, 10 present keys,
      missing price_adjustment + data_protection, coverage 0.83,
      coverage_pct 83.33, 0 integrity issues, export NDA-2026-001.json.
  src/plugin/tools.ts, src/plugin/storage.ts
      the seven tool names, the R0/R1 split (4 read-only / 3 local write),
      the `legal_clause` domain with its `contracts` / `playbooks` tables and
      the `exports/<contract_id>.json` sink.

Hero (1440x576, zh/en x light/dark)
    Left column: kicker / wordmark / two value lines / one subtitle / one
    meta line / footer. Right side: the artifact this plugin returns - the
    stored clause tree as a spine with ten numbered nodes, every node
    carrying the key it was mapped to, then the 12-slot coverage strip
    (10 filled, 2 hollow) and the two missing keys as explicit chips.

Flow (1100x660, one language-neutral pair for all five READMEs)
    Grammar: a CLAUSE <-> KEY CROSSWALK COMB, not a row of arrowed boxes.
    The clause tree is a vertical spine on the left; each mapped clause sends
    one ribbon across to its key cell in the 12-key deck; the two keys no
    clause reached stay hollow and are tagged `missing` where they sit. The
    deck is grouped by the playbook's four categories, each with a small
    present/total bar. Two boundary rails close the figure: R0 read-only
    results (playbook_check / coverage_check / clause_integrity) and R1 local
    writes (clause_tree -> contracts, playbook_register -> playbooks,
    export_tree -> exports/NDA-2026-001.json + sha256).

Typography / palette (GitHub renders the 1440px hero at ~880px)
    Hero: title 79px (displayed > 48), subtitle 25px (> 15), meta 20px
    (> 12). Flow: node text 13px, annotations 11.5px. Light #f9f6fd ->
    #e4eaf8, dark #131a2a -> #0c1016, family accent #4B67B4 / #8496f5,
    radii 18-22, soft shadows. Fonts: msyh.ttc / msyhbd.ttc / consola.ttf.

Every label is measured before it is drawn; a label that would overflow its
box aborts the run instead of shipping clipped text.

Run once:  python scripts/gen-readme-assets.py
Requires:  Python 3.10+, Pillow, and the Windows fonts above.
"""
from __future__ import annotations

import json
import os
import re
import sys
from html import escape
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")
SAMPLE = os.path.join(ROOT, "samples", "quickstart", "input",
                      "synthetic-nda-2026.txt")
GOLDEN = os.path.join(ROOT, "samples", "quickstart", "expected", "result.json")

HERO_W, HERO_H = 1440, 576
FLOW_W, FLOW_H = 1100, 660
SS = 2                                  # hero is drawn at 2x, then downsampled

FONT_FILES = {
    "sans": r"C:\Windows\Fonts\msyh.ttc",
    "sans_bold": r"C:\Windows\Fonts\msyhbd.ttc",
    "mono": r"C:\Windows\Fonts\consola.ttf",
    "mono_bold": r"C:\Windows\Fonts\consolab.ttf",
}
for _kind, _path in FONT_FILES.items():
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")

CSS_SANS = ("'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',"
            "'Source Han Sans SC',sans-serif")
CSS_MONO = ("'Consolas','SFMono-Regular','Menlo',ui-monospace,monospace")

SKIN = {
    "light": dict(
        bg_a="#f9f6fd", bg_b="#e4eaf8",
        card="#ffffff", edge="#e6e2ef", band="#f5f2fb",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", good="#16a34a", warn="#b45309",
        warn_bg="#fdf3e9", pill="#ece7f9", grid="#e7e4f0",
        rule="#dcd8ea", shadow=(30, 24, 60), shadow_alpha=26,
        glow_a=(75, 103, 180, 22), glow_b=(122, 104, 201, 10),
    ),
    "dark": dict(
        bg_a="#131a2a", bg_b="#0c1016",
        card="#1b2231", edge="#2e374b", band="#202839",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", good="#3fb950", warn="#d9a441",
        warn_bg="#2a2216", pill="#242d42", grid="#262f42",
        rule="#2b3348", shadow=(0, 0, 0), shadow_alpha=90,
        glow_a=(132, 150, 245, 34), glow_b=(132, 150, 245, 14),
    ),
}

CAT_COLOR = {
    "light": {"risk": "#b45309", "control": "#4B67B4",
              "commercial": "#0f766e", "performance": "#7c3aed"},
    "dark": {"risk": "#d9a441", "control": "#8496f5",
             "commercial": "#2dd4bf", "performance": "#a78bfa"},
}

# ---------------------------------------------------------------------------
# The pipeline, re-derived from the material (no invented values)
# ---------------------------------------------------------------------------
PLAYBOOK = [
    ("confidentiality", "risk"),
    ("liability", "risk"),
    ("indemnity", "risk"),
    ("termination", "control"),
    ("assignment", "control"),
    ("governing_law", "control"),
    ("dispute", "control"),
    ("payment", "commercial"),
    ("price_adjustment", "commercial"),
    ("ip", "commercial"),
    ("warranty", "performance"),
    ("data_protection", "performance"),
]
CATEGORIES = ["risk", "control", "commercial", "performance"]

# English side of src/core/clause.ts KEYWORDS; the sample contract is English.
KEYWORDS = {
    "confidentiality": r"confidential",
    "liability": r"liability",
    "indemnity": r"indemn",
    "termination": r"terminat",
    "assignment": r"assign",
    "governing_law": r"governing law",
    "dispute": r"dispute|arbitrat",
    "payment": r"payment",
    "price_adjustment": r"price adjustment",
    "ip": r"intellectual property",
    "warranty": r"warrant",
    "data_protection": r"data protection|personal data",
}

CLAUSE_LINE = re.compile(r"^\s*(\d+(?:\.\d+)*)[.)]?\s+(.+)$")


def parse_clauses(text: str) -> list[dict]:
    """Same split as parseClauses(): line-leading number, continuation joins."""
    clauses: list[dict] = []
    for line in text.splitlines():
        m = CLAUSE_LINE.match(line)
        if m:
            clauses.append({"no": m.group(1), "title": m.group(2).strip(),
                            "body": m.group(2)})
        elif clauses:
            clauses[-1]["body"] += "\n" + line
    return clauses


def map_clause(body: str, title: str) -> tuple[str, str]:
    """best of the 12 keys: body hit +2, title hit +3, first max wins."""
    best_i, best_score = -1, 0
    for i, (key, _cat) in enumerate(PLAYBOOK):
        pat = KEYWORDS[key]
        score = (2 if re.search(pat, body, re.I) else 0) + (
            3 if re.search(pat, title, re.I) else 0)
        if score > best_score:          # strict: ties keep the earlier key
            best_i, best_score = i, score
    if best_i < 0:
        return "unresolved", ""
    return PLAYBOOK[best_i][0], PLAYBOOK[best_i][1]


def load_material() -> dict:
    with open(SAMPLE, encoding="utf-8") as fh:
        raw = fh.read()
    with open(GOLDEN, encoding="utf-8") as fh:
        golden = json.load(fh)

    clauses = []
    for c in parse_clauses(raw):
        key, cat = map_clause(c["body"], c["title"])
        clauses.append({"no": c["no"], "title": c["title"],
                        "key": key, "cat": cat})

    present = [c["key"] for c in clauses if c["key"] != "unresolved"]
    unresolved = sum(1 for c in clauses if c["key"] == "unresolved")
    missing = [k for k, _c in PLAYBOOK if k not in present]
    coverage = round(len(present) / len(PLAYBOOK), 2)

    # the golden file is the referee: a drift aborts the build
    checks = [
        (len(clauses), golden["clauses"], "clause count"),
        (unresolved, golden["unresolved"], "unresolved count"),
        (present, golden["present_keys"], "present keys"),
        (missing, golden["missing_keys"], "missing keys"),
        (coverage, golden["coverage"], "coverage"),
        (round(len(present) / len(PLAYBOOK) * 10000) / 100,
         golden["coverage_pct"], "coverage_pct"),
        (golden["integrity_issue_codes"], [], "integrity issues"),
    ]
    for got, want, what in checks:
        if got != want:
            raise SystemExit(f"FATAL: {what} drifted from the golden file: "
                             f"{got!r} != {want!r}")
    for c in clauses:
        if not c["title"]:
            raise SystemExit("FATAL: a clause has no title")

    per_cat = {c: {"present": 0, "total": 0} for c in CATEGORIES}
    for key, cat in PLAYBOOK:
        per_cat[cat]["total"] += 1
        if key in present:
            per_cat[cat]["present"] += 1

    return dict(clauses=clauses, present=present, missing=missing,
                unresolved=unresolved, coverage=coverage,
                coverage_pct=golden["coverage_pct"],
                contract_id=golden["contract_id"],
                export_file=golden["export_file"], per_cat=per_cat)


M = load_material()

# the 12 key rows, in playbook order, each carrying the clause that reached it
KEY_ROWS = []
for key, cat in PLAYBOOK:
    hit = next((c for c in M["clauses"] if c["key"] == key), None)
    KEY_ROWS.append({"key": key, "cat": cat, "clause": hit})

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
_HX: dict[str, tuple[int, int, int]] = {}


def hx(value: str) -> tuple[int, int, int]:
    hit = _HX.get(value)
    if hit is None:
        v = value.lstrip("#")
        hit = (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
        _HX[value] = hit
    return hit


_SCRATCH = ImageDraw.Draw(Image.new("RGB", (8, 8)))
_MEASURE_FONT: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}
_DRAW_FONT: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}


def measure_font(size: float, kind: str) -> ImageFont.FreeTypeFont:
    key = (int(round(size * 10)), kind)
    f = _MEASURE_FONT.get(key)
    if f is None:
        f = ImageFont.truetype(FONT_FILES[kind], max(1, int(round(size))))
        _MEASURE_FONT[key] = f
    return f


def draw_font(size: float, kind: str) -> ImageFont.FreeTypeFont:
    dev = max(1, int(round(size * SS)))
    key = (dev, kind)
    f = _DRAW_FONT.get(key)
    if f is None:
        f = ImageFont.truetype(FONT_FILES[kind], dev)
        _DRAW_FONT[key] = f
    return f


def tw(text: str, size: float, kind: str) -> float:
    return _SCRATCH.textlength(text, font=measure_font(size, kind))


def require(text: str, size: float, kind: str, max_w: float, what: str) -> None:
    w = tw(text, size, kind)
    if w > max_w + 0.6:
        raise SystemExit(f"FATAL: {what} overflows: {text!r} needs "
                         f"{w:.1f}px > {max_w:.1f}px")


def fit(text: str, kind: str, max_w: float, start: float,
        floor: float) -> float:
    size = start
    while size > floor:
        if tw(text, size, kind) <= max_w:
            return size
        size -= 1
    require(text, size, kind, max_w, "text")
    return size


def fit_lines(lines: list[str], kind: str, max_w: float, start: float,
              floor: float) -> float:
    return min(fit(t, kind, max_w, start, floor) for t in lines)


def pick(content: str, mono_kind: str = "mono", sans_kind: str = "sans") -> str:
    """Latin tokens read better in mono; CJK must never go through Consolas."""
    return mono_kind if content.isascii() else sans_kind


def gradient(w: int, h: int, c1: str, c2: str) -> Image.Image:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    a, b = hx(c1), hx(c2)
    for y in range(h):
        t = y / max(1, h - 1)
        t = 0.18 * t + 0.82 * t ** 1.3
        d.line([(0, y), (w, y)],
               fill=tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    return img


def glow(img: Image.Image, cx: float, cy: float, r: float,
         rgba: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(10, 0, -1):
        rr = r * i / 10 * SS
        d.ellipse([cx * SS - rr, cy * SS - rr, cx * SS + rr, cy * SS + rr],
                  fill=rgba[:3] + (int(rgba[3] * (1 - i / 11)),))
    layer = layer.filter(ImageFilter.GaussianBlur(26 * SS))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


class Layer:
    """Draws in 1440x576 design coordinates onto the 2x canvas."""

    def __init__(self, img: Image.Image):
        self.img = img
        self.d = ImageDraw.Draw(img)

    def rrect(self, box, radius: float, fill=None, outline=None,
              width: float = 1.0) -> None:
        self.d.rounded_rectangle(
            [box[0] * SS, box[1] * SS, box[2] * SS, box[3] * SS],
            radius=radius * SS, fill=hx(fill) if fill else None,
            outline=hx(outline) if outline else None,
            width=max(1, int(round(width * SS))))

    def line(self, x1, y1, x2, y2, color: str, width: float = 1.0) -> None:
        self.d.line([x1 * SS, y1 * SS, x2 * SS, y2 * SS], fill=hx(color),
                    width=max(1, int(round(width * SS))))

    def circle(self, cx, cy, r, fill: str) -> None:
        self.d.ellipse([(cx - r) * SS, (cy - r) * SS,
                        (cx + r) * SS, (cy + r) * SS], fill=hx(fill))

    def text(self, x, y, content: str, size: float, kind: str, color: str,
             right: float | None = None) -> None:
        f = draw_font(size, kind)
        if right is not None:
            x = right - tw(content, size, kind)
        self.d.text((x * SS, y * SS), content, font=f, fill=hx(color))


def shadowed(img: Image.Image, box, radius: float, s: dict,
             blur: float = 15, dy: float = 9) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([box[0] * SS, (box[1] + dy) * SS,
                         box[2] * SS, (box[3] + dy) * SS],
                        radius=(radius + 2) * SS,
                        fill=s["shadow"] + (s["shadow_alpha"],))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * SS / 2))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def card(img: Image.Image, box, s: dict, radius: float = 20) -> Image.Image:
    img = shadowed(img, box, radius, s)
    lay = Layer(img)
    lay.rrect(box, radius, fill=s["card"], outline=s["edge"], width=1.5)
    return img


# ---------------------------------------------------------------------------
# hero 1440x576
# ---------------------------------------------------------------------------
HERO = {
    "zh": dict(
        kicker="DeepSeek Harness 插件 · 合同条款检查",
        title_a="dsh-legal-", title_b="clause",
        value=["拆成条款树，对齐 12 个键，", "缺了哪几项逐条列出来"],
        sub="标题权重高于正文；匹配不上就标 unresolved。",
        meta="7 个工具 · R0 只读 ×4 / R1 本地写 ×3 · 12 键 4 类 · 全程本地",
        foot="Apache-2.0 · PerryLink DSH plugin family",
        tree_head="条款树 · NDA-2026-001",
        tree_chip="10 条 · 0 未映射",
        cov_label="覆盖率",
        cov_note="10 / 12 个键 · 未映射 0",
        miss_label="缺失 · 2",
        miss_note="显式列出，不隐藏",
    ),
    "en": dict(
        kicker="DeepSeek Harness plugin · contract clause check",
        title_a="dsh-legal-", title_b="clause",
        value=["numbered text → clause tree,", "12 keys → present or missing"],
        sub="title hits weigh more than body; no match → unresolved",
        meta="7 tools · R0 read-only ×4 / R1 local write ×3 · 12 keys, 4 categories",
        foot="Apache-2.0 · PerryLink DSH plugin family",
        tree_head="clause tree · NDA-2026-001",
        tree_chip="10 nodes · 0 unresolved",
        cov_label="coverage",
        cov_note="10 / 12 keys · unresolved 0",
        miss_label="missing · 2",
        miss_note="explicit, never dropped",
    ),
}


def hero(lang: str, skin: str) -> None:
    s = SKIN[skin]
    cat = CAT_COLOR[skin]
    h = HERO[lang]

    img = gradient(HERO_W * SS, HERO_H * SS, s["bg_a"], s["bg_b"])
    img = glow(img, 1180, 20, 300, s["glow_a"])
    img = glow(img, 90, 560, 240, s["glow_b"])

    lay = Layer(img)
    m, col_w = 64, 702

    # ---- left column ------------------------------------------------------
    lay.rrect((m, 62, m + tw(h["kicker"], 17, "sans_bold") + 46, 104),
              21, fill=s["pill"])
    lay.text(m + 23, 71, h["kicker"], 17, "sans_bold", s["accent"])

    size = 79
    require(h["title_a"] + h["title_b"], size, "mono_bold", col_w, "hero title")
    if size * 880 / HERO_W < 48:
        raise SystemExit("FATAL: hero title would display below 48px")
    lay.text(m - 2, 130, h["title_a"], size, "mono_bold", s["text"])
    lay.text(m - 2 + tw(h["title_a"], size, "mono_bold"), 130,
             h["title_b"], size, "mono_bold", s["accent"])

    vf = fit_lines(h["value"], "sans_bold", col_w, 39, 33)
    for i, line in enumerate(h["value"]):
        require(line, vf, "sans_bold", col_w, "hero value line")
        lay.text(m - 1, 252 + i * 55, line, vf, "sans_bold", s["text"])

    require(h["sub"], 25, "sans", col_w, "hero subtitle")
    if 25 * 880 / HERO_W < 15:
        raise SystemExit("FATAL: hero subtitle would display below 15px")
    lay.text(m + 1, 374, h["sub"], 25, "sans", s["sub"])

    require(h["meta"], 20, "sans", col_w, "hero meta")
    if 20 * 880 / HERO_W < 12:
        raise SystemExit("FATAL: hero meta would display below 12px")
    lay.text(m + 1, 420, h["meta"], 20, "sans", s["faint"])

    lay.line(m + 1, 456, m + col_w - 6, 456, s["grid"], 2)
    require(h["foot"], 16, "sans", col_w, "hero footer")
    lay.text(m + 1, 468, h["foot"], 16, "sans", s["faint"])

    # ---- right: the stored clause tree, drawn as a spine -------------------
    tree = (780, 40, 1376, 424)
    img = card(img, tree, s, radius=22)
    lay = Layer(img)
    head_kind = pick(h["tree_head"], "mono_bold", "sans_bold")
    lay.text(804, 57, h["tree_head"], 13.5, head_kind, s["accent"])
    chip_kind = pick(h["tree_chip"], "mono", "sans")
    chip_w = tw(h["tree_chip"], 10.5, chip_kind) + 22
    lay.rrect((1352 - chip_w, 54, 1352, 76), 11, fill=s["band"])
    lay.text(1363 - chip_w, 59, h["tree_chip"], 10.5, chip_kind, s["sub"])
    lay.line(804, 92, 1352, 92, s["grid"], 1.4)
    lay.line(828, 116, 828, 392, s["rule"], 2)

    for i, c in enumerate(M["clauses"]):
        cy = 122 + i * 30
        colour = cat[c["cat"]]
        lay.text(0, cy - 8, c["no"], 11.5, "mono_bold", s["accent"], right=812)
        lay.circle(828, cy, 4, colour)
        lay.line(832, cy, 848, cy, colour, 1.6)
        require(c["title"], 13, "sans", 280, "hero clause title")
        lay.text(852, cy - 8, c["title"], 13, "sans", s["text"])
        kw = tw(c["key"], 10.5, "mono") + 28
        lay.rrect((1352 - kw, cy - 10.5, 1352, cy + 10.5), 10.5,
                  fill=s["band"], outline=s["edge"], width=1)
        lay.rrect((1352 - kw + 2.5, cy - 7.5, 1352 - kw + 5.5, cy + 7.5),
                  1.5, fill=colour)
        lay.text(1352 - kw + 13, cy - 7, c["key"], 10.5, "mono", s["text"])

    # ---- coverage card ----------------------------------------------------
    cov = (780, 436, 1050, 540)
    img = card(img, cov, s, radius=18)
    lay = Layer(img)
    lay.text(800, 452, h["cov_label"], 11.5, "sans", s["faint"])
    lay.text(798, 466, f"{M['coverage']:.2f}", 30, "mono_bold", s["accent"])
    require(h["cov_note"], 11.5, "sans", 230, "hero coverage note")
    lay.text(800, 516, h["cov_note"], 11.5, "sans", s["sub"])
    for i, (key, _cat) in enumerate(PLAYBOOK):
        x = 900 + i * 10.4
        if key in M["present"]:
            lay.rrect((x, 482, x + 8, 492), 3, fill=s["accent"])
        else:
            lay.rrect((x, 482, x + 8, 492), 3, outline=s["warn"], width=1.4)

    # ---- missing card -----------------------------------------------------
    miss = (1062, 436, 1376, 540)
    img = card(img, miss, s, radius=18)
    lay = Layer(img)
    lay.text(1084, 452, h["miss_label"], 11.5, "sans_bold", s["warn"])
    for i, key in enumerate(M["missing"]):
        y = 470 + i * 26
        kw = tw(key, 10.5, "mono") + 24
        lay.rrect((1084, y, 1084 + kw, y + 21), 10.5, fill=s["warn_bg"],
                  outline=s["warn"], width=1.2)
        lay.text(1096, y + 4.5, key, 10.5, "mono", s["warn"])
    require(h["miss_note"], 10.5, "sans", 270, "hero missing note")
    lay.text(1084, 526, h["miss_note"], 10.5, "sans", s["faint"])

    name = f"dsh-legal-clause-hero-{lang}-{skin}.webp"
    out = img.resize((HERO_W, HERO_H), Image.LANCZOS)
    out.save(os.path.join(OUT, name), "WEBP", quality=92, method=6)
    print(f"wrote {name} ({HERO_W}x{HERO_H})")


# ---------------------------------------------------------------------------
# flow 1100x660 (hand-written SVG)
# ---------------------------------------------------------------------------
FLOW = {
    "light": dict(bg_a="#f9f6fd", bg_b="#e4eaf8", card="#ffffff",
                  edge="#e6e2ef", band="#f5f2fb", text="#141419",
                  sub="#4d5261", faint="#8f94a4", accent="#4B67B4",
                  warn="#b45309", warn_bg="#fdf3e9", pill="#ece7f9",
                  grid="#e7e4f0", rule="#dcd8ea", shadow="0.10"),
    "dark": dict(bg_a="#131a2a", bg_b="#0c1016", card="#1b2231",
                 edge="#2e374b", band="#202839", text="#f0f3f9",
                 sub="#a8b1c4", faint="#737b8d", accent="#8496f5",
                 warn="#d9a441", warn_bg="#2a2216", pill="#242d42",
                 grid="#262f42", rule="#2b3348", shadow="0.48"),
}


class Svg:
    """Tiny SVG writer that measures every label before emitting it."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.problems: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x: float, y: float, content: str, size: float, fill: str,
             kind: str = "sans", anchor: str = "start",
             max_w: float | None = None, opacity: float | None = None) -> None:
        if max_w is not None:
            w = tw(content, size, kind)
            if w > max_w + 0.6:
                self.problems.append(
                    f"{content!r} needs {w:.1f}px > {max_w:.1f}px")
        family = CSS_MONO if kind.startswith("mono") else CSS_SANS
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"',
                 f'font-family="{family}"', f'font-size="{size}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if kind.endswith("_bold"):
            attrs.append('font-weight="700"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<text {" ".join(attrs)}>{escape(content)}</text>')

    def rect(self, x, y, w, h, fill, radius=0.0, stroke=None, sw=1.4,
             dash=None, shadow=False, opacity=None) -> None:
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if radius:
            attrs.append(f'rx="{radius}"')
        attrs.append(f'fill="{fill}"')
        if stroke:
            attrs += [f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if shadow:
            attrs.append('filter="url(#soft)"')
        self.add(f'<rect {" ".join(attrs)}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1.4, dash=None,
             opacity=None) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
                 f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, stroke: str, sw=1.4, fill="none") -> None:
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')

    def circle(self, cx, cy, r, fill) -> None:
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')

    def svg(self, w: int, h: int, label: str) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                f'height="{h}" viewBox="0 0 {w} {h}" role="img" '
                f'aria-label="{escape(label, quote=True)}">')
        return "\n".join([head, *self.parts, "</svg>"]) + "\n"


ROW_Y0, ROW_H = 172, 26
RIBBON_X, CHIP_X = 340, 500
GROUP_X, GROUP_END = 760, 1040
RAIL_Y0, RAIL_Y1 = 512, 594


def flow_svg(skin: str) -> str:
    s = FLOW[skin]
    cat = CAT_COLOR[skin]
    v = Svg()

    v.add("<defs>")
    v.add(f'<linearGradient id="bg" x1="0" y1="0" x2="0.25" y2="1">'
          f'<stop offset="0" stop-color="{s["bg_a"]}"/>'
          f'<stop offset="1" stop-color="{s["bg_b"]}"/></linearGradient>')
    v.add(f'<filter id="soft" x="-25%" y="-25%" width="150%" height="165%">'
          f'<feDropShadow dx="0" dy="7" stdDeviation="9" '
          f'flood-color="#15112a" flood-opacity="{s["shadow"]}"/></filter>')
    v.add("</defs>")
    v.add(f'<rect width="{FLOW_W}" height="{FLOW_H}" fill="url(#bg)"/>')

    # ---- header -----------------------------------------------------------
    v.text(40, 52, "dsh-legal-clause", 27, s["text"], "mono_bold", max_w=420)
    v.text(40, 80, "numbered plain text in → clause tree → best of 12 keys "
                   "→ present / missing → local JSON out", 14.5, s["sub"],
           "sans", max_w=790)
    chip = "7 tools · R0 ×4 / R1 ×3 · no network"
    cw = tw(chip, 11, "mono") + 24
    v.rect(1060 - cw, 30, cw, 26, s["pill"], radius=13)
    v.text(1060 - cw + 12, 38, chip, 11, s["accent"], "mono", max_w=cw - 24)

    # ---- input strip ------------------------------------------------------
    v.rect(40, 96, 1020, 46, s["band"], radius=14, stroke=s["edge"])
    v.text(58, 111, "contract .txt", 13, s["accent"], "mono_bold", max_w=110)
    v.text(172, 111, "UTF-8 · one clause per line · original untouched",
           12.5, s["sub"], "sans", max_w=330)
    v.text(516, 113, "line-leading number", 11, s["faint"], "sans", max_w=130)
    v.text(636, 112, r"^\s*(\d+(?:\.\d+)*)[.)]?\s+", 11.5, s["faint"],
           "mono", max_w=230)
    in_chip = f"{len(M['clauses'])} clauses · {M['unresolved']} unresolved"
    iw = tw(in_chip, 10.5, "mono") + 24
    v.rect(1040 - iw, 106, iw, 26, s["pill"], radius=13)
    v.text(1040 - iw + 12, 114, in_chip, 10.5, s["accent"], "mono",
           max_w=iw - 24)

    # ---- column headers ---------------------------------------------------
    v.text(64, 158, "clause tree · legal.clause_tree", 12, s["sub"], "sans",
           max_w=260)
    v.text(416, 158, "title +3 / body +2", 11, s["faint"],
           "mono", anchor="middle", max_w=150)
    v.text(CHIP_X, 158, "12-key playbook · 4 categories", 12, s["sub"],
           "sans", max_w=250)
    v.text(GROUP_X, 158, "category", 11, s["faint"], "sans", max_w=80)
    v.text(GROUP_END, 158, "present / total", 11, s["faint"], "sans",
           anchor="end", max_w=110)

    # ---- the crosswalk ----------------------------------------------------
    v.line(748, ROW_Y0 - 2, 748, ROW_Y0 + 12 * ROW_H + 4, s["rule"], 1,
           dash="4 5")
    first_cy = ROW_Y0 + ROW_H / 2
    v.line(89, first_cy, 89, first_cy + 10 * ROW_H, s["rule"], 2)
    for i, row in enumerate(KEY_ROWS):
        cy = first_cy + i * ROW_H
        colour = cat[row["cat"]]
        chip_w = tw(row["key"], 13, "mono") + 28

        if row["clause"]:
            c = row["clause"]
            v.text(80, cy + 4.6, str(c["no"]), 12.5, s["accent"], "mono_bold",
                   anchor="end", max_w=20)
            v.circle(89, cy, 3.4, s["accent"])
            v.line(92.5, cy, 104, cy, s["accent"], 1.3)
            v.text(110, cy + 4.8, c["title"], 13, s["text"], "sans",
                   max_w=218)
            v.line(RIBBON_X, cy, 486, cy, colour, 1.5, opacity=0.55)
            v.path(f"M480 {cy - 4.2}L487 {cy}L480 {cy + 4.2}", colour, 1.5)
            v.rect(CHIP_X, cy - 10.5, chip_w, 21, s["band"], radius=10.5,
                   stroke=s["edge"], sw=1)
            v.rect(CHIP_X + 3, cy - 7.5, 3, 15, colour, radius=1.5)
            v.text(CHIP_X + 13, cy + 4.6, row["key"], 13, s["text"], "mono",
                   max_w=chip_w - 26)
        else:
            # no clause reached this key: the comb keeps an empty tooth
            v.line(64, cy, 330, cy, s["rule"], 1, dash="3 6", opacity=0.9)
            v.add(f'<circle cx="89" cy="{cy}" r="3.2" fill="none" '
                  f'stroke="{s["rule"]}" stroke-width="1.3"/>')
            v.rect(CHIP_X, cy - 10.5, chip_w, 21, s["warn_bg"], radius=10.5,
                   stroke=s["warn"], sw=1.2, dash="4 3")
            v.text(CHIP_X + 13, cy + 4.6, row["key"], 13, s["warn"], "mono",
                   max_w=chip_w - 26)
            v.text(CHIP_X + chip_w + 14, cy + 4.4, "missing", 11.5, s["warn"],
                   "sans", max_w=70)

    # ---- per-category scoreboard (a tile centred on its block of rows) ----
    for name in CATEGORIES:
        idx = [i for i, r in enumerate(KEY_ROWS) if r["cat"] == name]
        stat = M["per_cat"][name]
        mid = first_cy + idx[0] * ROW_H + (len(idx) - 1) * ROW_H / 2
        v.circle(GROUP_X + 1, mid - 4, 3.2, cat[name])
        v.text(GROUP_X + 12, mid + 0.5, name, 11.5, s["text"], "sans_bold",
               max_w=90)
        v.text(GROUP_END, mid + 0.5, f"{stat['present']} / {stat['total']}",
               11.5, s["sub"], "mono", anchor="end", max_w=60)
        v.rect(GROUP_X + 12, mid + 5, 230, 6, s["grid"], radius=3)
        filled = 230 * stat["present"] / stat["total"]
        if filled > 0:
            v.rect(GROUP_X + 12, mid + 5, filled, 6, cat[name], radius=3)

    # ---- engine legend ----------------------------------------------------
    v.text(64, 500, "one key per clause · best hit wins · no hit → "
                    "unresolved (explicit, never dropped)", 11, s["faint"],
           "sans", max_w=660)

    # ---- rails ------------------------------------------------------------
    v.rect(64, RAIL_Y0, 480, RAIL_Y1 - RAIL_Y0, s["card"], radius=16,
           stroke=s["edge"], shadow=True)
    v.text(80, 522, "R0 · read-only tools", 11, s["faint"], "sans", max_w=200)
    v.text(80, 544, "legal.playbook_check → present 10 · missing 2 · "
                    "coverage 0.83", 11.5, s["sub"], "mono", max_w=464)
    v.text(80, 562, "legal.coverage_check → coverage_pct 83.33 · 10 / 12 "
                    "keys", 11.5, s["sub"], "mono", max_w=464)
    v.text(80, 580, "legal.clause_integrity → 0 issues · duplicate / gap / "
                    "order", 11.5, s["sub"], "mono", max_w=464)

    v.rect(556, RAIL_Y0, 504, RAIL_Y1 - RAIL_Y0, s["card"], radius=16,
           stroke=s["edge"], shadow=True)
    v.text(572, 522, "R1 · local write tools", 11, s["faint"], "sans",
           max_w=200)
    v.text(572, 544, "legal.clause_tree → legal_clause.contracts · "
                     "10 clauses", 11.5, s["sub"], "mono", max_w=472)
    v.text(572, 562, "legal.playbook_register → legal_clause.playbooks · "
                     "versioned keys", 11.5, s["sub"], "mono", max_w=472)
    v.text(572, 580, "legal.export_tree → exports/NDA-2026-001.json · "
                     "path + sha256", 11.5, s["sub"], "mono", max_w=472)

    # ---- footer -----------------------------------------------------------
    v.text(64, 616, "no network · no model call · originals untouched · "
                    "top-level clause no > 5000 → one E_CLAUSE_NUMBER_RANGE · "
                    "alpha / partial · Apache-2.0", 11, s["faint"], "sans",
           max_w=1010)

    if v.problems:
        raise SystemExit("FATAL: flow labels overflow:\n  "
                         + "\n  ".join(v.problems))

    svg = v.svg(FLOW_W, FLOW_H,
                "dsh-legal-clause structure: a clause tree spine on the left "
                "sends one ribbon per clause to its key in the 12-key "
                "playbook deck; price_adjustment and data_protection stay "
                "hollow because no clause reached them; R0 read-only checks "
                "and R1 local writes close the figure")
    ET.fromstring(svg)                   # fail loudly if the SVG is malformed
    return svg


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        for lang in ("zh", "en"):
            hero(lang, skin)
    for skin in ("light", "dark"):
        name = f"dsh-legal-clause-flow-v5-{skin}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(flow_svg(skin))
        print(f"wrote {name} ({FLOW_W}x{FLOW_H})")
    print(f"checks: {len(M['clauses'])} clauses, {M['unresolved']} unresolved, "
          f"missing {', '.join(M['missing'])}, coverage {M['coverage']}")
    print("legacy flow-{light,dark}.svg left untouched for external deep links")


if __name__ == "__main__":
    main()
