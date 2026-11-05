#!/usr/bin/env python3
"""Generate README image assets for dsh-legal-clause (docs/assets/).

Outputs (idempotent overwrite):
  dsh-legal-clause-flow-light.svg / dsh-legal-clause-flow-dark.svg
      Hero pipeline diagram. Two hand-written SVG files (vector - never
      rasterized to webp). Text inside is command-surface tokens only
      (legal.clause_tree, legal.playbook_check, ...), so all five README
      languages share the same pair.

No raster outputs for this repo: it has no UI/client half to screenshot and
no benchmark dataset for an evidence chart (acceptance rows live in
ACCEPTANCE.csv and are quoted in the README text instead). The CJK font probe
below is kept from the family skeleton so that adding a raster chart later
fails loudly instead of rendering tofu; the SVG text here is Latin tokens.
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# --- palette: PerryLink family (accent) + GitHub page backgrounds ----------
FAMILY = "#4B67B4"   # family accent (badges keep labelColor #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
WEBP_QUALITY = 90    # reserved for future raster charts
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a", track="#eaeef2"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e", track="#21262d"),
}

# --- CJK font probe: Chinese must never render as tofu boxes ----------------
# Only required when a raster (webp) chart is added; the SVG hero below
# carries Latin command tokens only. Kept from the family skeleton.
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]


def require_cjk_font() -> str:
    path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if path is None:
        sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
                 "Deng.ttf, Noto Sans CJK, PingFang). Refusing to render "
                 "Chinese as tofu boxes; install one of the probed fonts "
                 "and re-run.")
    return path


# ---------------------------------------------------------------------------
# Hero pipeline SVG (light + dark): contract text -> clause tree -> domain ->
# playbook / coverage checks -> JSON export.
# ---------------------------------------------------------------------------
FLOW_NODES = [
    ("contract .txt", "UTF-8 · 1. 2. 3."),
    ("legal.clause_tree", "clauses · unresolved"),
    ("legal_clause", "contracts · playbooks"),
    ("legal.playbook_check", "present · missing"),
    ("legal.coverage_check", "12 keys · coverage %"),
    ("legal.export_tree", "exports/*.json"),
]


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    w, h = 1200, 360
    nw, nh, gap = 170, 96, 18
    x0, y0 = 45, 150
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="dsh-legal-clause pipeline">',
        '<title>dsh-legal-clause pipeline</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="{x0}" y="62" fill="{s["text"]}" font-family="ui-sans-serif,'
        f'system-ui,sans-serif" font-size="30" font-weight="700">'
        f'dsh-legal-clause</text>',
        f'<text x="{x0}" y="94" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="16">legal.clause_tree · legal.playbook_check · '
        f'legal.coverage_check · legal.export_tree</text>',
        f'<line x1="{x0}" y1="116" x2="{w - x0}" y2="116" stroke="{s["border"]}"/>',
    ]
    for i, (label, sub) in enumerate(FLOW_NODES):
        x = x0 + i * (nw + gap)
        accent = GREEN[skin] if i == len(FLOW_NODES) - 1 else (
            FAMILY if i in (1, 3, 5) else s["border"])
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 40}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="13" font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 68}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="11">{sub}</text>')
        if i < len(FLOW_NODES) - 1:
            ax = x + nw + 2
            ay = y0 + nh // 2
            parts.append(
                f'<path d="M{ax} {ay}h{gap - 8}" stroke="{s["sub"]}" '
                f'stroke-width="2"/>')
            parts.append(
                f'<path d="M{ax + gap - 10} {ay - 6}l8 6-8 6" fill="none" '
                f'stroke="{s["sub"]}" stroke-width="2" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append(
        f'<text x="{x0}" y="300" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">legal.playbook · legal.playbook_register · '
        f'legal.clause_integrity · R0 read-only · R1 local write</text>')
    parts.append(
        f'<text x="{x0}" y="328" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">no network · no model call · originals '
        f'untouched · alpha / partial</text>')
    parts.append('</svg>')
    svg = "\n".join(parts) + "\n"
    ET.fromstring(svg)  # fail loudly if the generated SVG is malformed
    return svg


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        with open(os.path.join(OUT, f"dsh-legal-clause-flow-{skin}.svg"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/")


if __name__ == "__main__":
    main()
