#!/usr/bin/env python3
"""Schematic mini-figures explaining the two completeness metrics.

Pure illustration (no data): a 6-page document, gold evidence pages,
a method's top-3 selection. Written for the supervisor report.

Writes:
    farit/results/figures/metric_example_strict.png
    farit/results/figures/metric_example_lenient.png

CLI (from repo root):
    ~/ds_env/bin/python farit/src/analysis/metric_examples.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

FIG_DIR = Path.cwd() / "farit" / "results" / "figures"

GOLD_FILL = "#F5A623"      # orange: gold evidence page
SEL_EDGE = "#0072B2"       # blue: selected within budget
MISS_EDGE = "#C0392B"      # red: gold page missed
PAGE_FACE = "#F2F2F2"
PAGE_EDGE = "#BBBBBB"

N_PAGES = 6
PAGE_W, PAGE_H, GAP = 1.0, 0.62, 0.18
ROW_W = N_PAGES * (PAGE_W + GAP) - GAP


def draw_row(ax, y0, gold_pages, ranked, verdict, verdict_color, fragments=None):
    """One document row: pages 1..6 with gold/selection/miss markings.
    `ranked` = the method's top pages IN RANK ORDER (badge shows the rank),
    verdict text on its own line below the boxes."""
    selected = set(ranked)
    for i in range(1, N_PAGES + 1):
        x = (i - 1) * (PAGE_W + GAP)
        is_gold = i in gold_pages
        is_sel = i in selected
        face = GOLD_FILL if is_gold else PAGE_FACE
        edge = SEL_EDGE if is_sel else PAGE_EDGE
        lw = 2.4 if is_sel else 1.0
        ax.add_patch(FancyBboxPatch((x, y0), PAGE_W, PAGE_H,
                                    boxstyle="round,pad=0.03",
                                    facecolor=face, edgecolor=edge,
                                    linewidth=lw, zorder=2))
        if is_gold and not is_sel:
            ax.add_patch(Rectangle((x - 0.07, y0 - 0.07), PAGE_W + 0.14, PAGE_H + 0.14,
                                   fill=False, edgecolor=MISS_EDGE, lw=2.0, ls="--", zorder=3))
        ax.text(x + PAGE_W / 2, y0 + PAGE_H / 2, f"p{i}", ha="center", va="center",
                fontsize=11, color="#222222" if is_gold else "#555555", zorder=4)
        # rank badge on selected pages: blue circle with the method's rank
        if is_sel:
            bx, by = x - 0.06, y0 + PAGE_H + 0.06
            ax.add_patch(plt.Circle((bx, by), 0.14, color=SEL_EDGE, zorder=5))
            ax.text(bx, by, str(ranked.index(i) + 1), ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold", zorder=6)
        if fragments and i in fragments:
            for j in range(fragments[i]):
                fx = x + PAGE_W / 2 + (j - (fragments[i] - 1) / 2) * 0.22
                ax.add_patch(plt.Circle((fx, y0 - 0.14), 0.07,
                                        color="#7A3E00", zorder=4))
    ax.text(0, y0 - 0.42, verdict, ha="left", va="center",
            fontsize=10.5, color=verdict_color, fontweight="bold")


def make_strict(path: Path):
    fig, ax = plt.subplots(figsize=(7.6, 2.9))
    ax.axis("off")
    ax.text(0, 2.58, "blue badge = rank of the page in the method's ranking (not its position in the document)",
            ha="left", fontsize=9.5, color="#666666")
    draw_row(ax, 1.6, gold_pages={2, 5}, ranked=[5, 2, 3],
             verdict="both gold pages are inside the method's top-3  →  complete@3 = 1",
             verdict_color="#1A7A3C")
    draw_row(ax, 0.15, gold_pages={2, 5}, ranked=[1, 2, 3],
             verdict="p5 carries evidence but is outside the top-3  →  complete@3 = 0",
             verdict_color="#C0392B")
    ax.set_xlim(-0.3, ROW_W + 0.1)
    ax.set_ylim(-0.42, 2.76)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_lenient(path: Path):
    fig, ax = plt.subplots(figsize=(7.6, 2.3))
    ax.axis("off")
    ax.text(0, 1.62, "dark dots (below the box) = individual evidence fragments — here: p2 has one, p5 has two",
            ha="left", fontsize=9.5, color="#666666")
    draw_row(ax, 0.65, gold_pages={2, 5}, ranked=[1, 2, 3],
             verdict="1 of 3 fragments found  →  piece-recall@3 = 0.33   "
                     "(the set is incomplete: complete@3 = 0)",
             verdict_color="#0072B2",
             fragments={2: 1, 5: 2})
    ax.set_xlim(-0.3, ROW_W + 0.1)
    ax.set_ylim(-0.18, 1.8)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    make_strict(FIG_DIR / "metric_example_strict.png")
    make_lenient(FIG_DIR / "metric_example_lenient.png")
    print(f"wrote {FIG_DIR / 'metric_example_strict.png'}")
    print(f"wrote {FIG_DIR / 'metric_example_lenient.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
