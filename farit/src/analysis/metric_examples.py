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


def draw_row(ax, y0, gold_pages, selected, verdict, verdict_color, fragments=None):
    """One document row: pages 1..6 with gold/selection/miss markings,
    verdict text on its own line below the boxes."""
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
        if fragments and i in fragments:
            for j in range(fragments[i]):
                bx = x + PAGE_W / 2 + (j - (fragments[i] - 1) / 2) * 0.22
                ax.add_patch(plt.Circle((bx, y0 + PAGE_H + 0.12), 0.07,
                                        color="#7A3E00", zorder=4))
    ax.text(0, y0 - 0.22, verdict, ha="left", va="center",
            fontsize=10.5, color=verdict_color, fontweight="bold")


def make_strict(path: Path):
    fig, ax = plt.subplots(figsize=(7.6, 2.5))
    ax.axis("off")
    draw_row(ax, 1.35, gold_pages={2, 5}, selected={2, 3, 5},
             verdict="all gold pages inside the budget  →  complete@3 = 1",
             verdict_color="#1A7A3C")
    draw_row(ax, 0.15, gold_pages={2, 5}, selected={1, 2, 3},
             verdict="p5 carries evidence but is outside top-3  →  complete@3 = 0",
             verdict_color="#C0392B")
    ax.set_xlim(-0.1, ROW_W + 0.1)
    ax.set_ylim(-0.25, 2.35)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_lenient(path: Path):
    fig, ax = plt.subplots(figsize=(7.6, 1.9))
    ax.axis("off")
    ax.text(ROW_W / 2, 1.32, "dark dots = individual evidence fragments (p2: one, p5: two)",
            ha="center", fontsize=9.5, color="#666666")
    draw_row(ax, 0.35, gold_pages={2, 5}, selected={1, 2, 3},
             verdict="1 of 3 fragments found  →  piece-recall@3 = 0.33   "
                     "(but the set is incomplete: complete@3 = 0)",
             verdict_color="#0072B2",
             fragments={2: 1, 5: 2})
    ax.set_xlim(-0.1, ROW_W + 0.1)
    ax.set_ylim(-0.1, 1.55)
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
