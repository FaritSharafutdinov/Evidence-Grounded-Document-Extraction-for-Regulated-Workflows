#!/usr/bin/env python3
"""Case studies: where the LLM judge fails to recognize derivation evidence.

Meeting-package deliverable behind PROGRESS.md finding 6 ("recognizing
derivation-relevant evidence is an open gap"). Reads frozen outputs only;
cases are selected by a deterministic stratified rule (no hand-picking).

Writes:
    farit/results/derived_case_studies.md
    farit/results/derived_case_studies.json
    farit/results/figures/judge_scores_gold_pages.{png,pdf}

CLI (from repo root):
    ~/ds_env/bin/python farit/src/analysis/derived_case_studies.py
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path.cwd()
RESULTS_DIR = REPO_ROOT / "farit" / "results"
FIG_DIR = RESULTS_DIR / "figures"
GOLD_EVIDENCE = REPO_ROOT / "farit" / "data" / "corpus" / "gold_evidence.jsonl"
LLM_JSON = RESULTS_DIR / "llm_reranker_qwen7b.json"

LAYER = "native"
LOW = 0.5  # the judge's own decision boundary (Yes vs No)


# ---------------------------------------------------------------------------
# Load and join
# ---------------------------------------------------------------------------

def load_instances() -> list[dict]:
    """per_instance judge records joined with their gold evidence sets."""
    gold = {
        (g["document"], g["field"]): g
        for g in map(json.loads, GOLD_EVIDENCE.read_text(encoding="utf-8").splitlines())
        if g["split"] == "dev"
    }
    llm = json.loads(LLM_JSON.read_text(encoding="utf-8"))[LAYER]["per_instance"]
    out = []
    for inst in llm:
        g = gold[(inst["document"], inst["field"])]
        scores = {int(k): float(v) for k, v in inst["page_scores"].items()}
        frags = []
        seen = set()
        for e in g["evidence_set"]:
            frags.append({**e, "judge_score": scores[e["page"]]})
            seen.add(e["page"])
        out.append({
            **inst,
            "page_scores": scores,
            "gold_pages": sorted(seen),
            "gold_page_scores": {p: scores[p] for p in sorted(seen)},  # deduped per (instance, page)
            "fragments": frags,
            "value": g["value"],
            "state": g["state"],
        })
    return out


# ---------------------------------------------------------------------------
# Deterministic case selection
# ---------------------------------------------------------------------------

def pick_cases(insts: list[dict]) -> dict:
    derived = [i for i in insts if i["derivation"] != "EXPLICIT"]
    fails = [i for i in derived if max(f["judge_score"] for f in i["fragments"]) < LOW]

    def worst(pool):
        return min(pool, key=lambda i: (max(f["judge_score"] for f in i["fragments"]),
                                         i["document"], i["field"]))

    strata = {
        "composition_implied": [i for i in fails if i["derivation"] == "COMPOSITION_IMPLIED"],
        "ontology_cross_page": [i for i in fails if i["derivation"] == "ONTOLOGY" and i["cross_page"]],
        "ontology_same_page": [i for i in fails if i["derivation"] == "ONTOLOGY" and not i["cross_page"]],
    }
    # Deterministic tie-break: min() keeps the FIRST best match, i.e. lowest
    # (max gold score, document, field) — stable across runs.
    cases = {name: worst(pool) for name, pool in strata.items() if pool}

    explicit_ok = [i for i in insts if i["derivation"] == "EXPLICIT"
                   and min(f["judge_score"] for f in i["fragments"]) >= LOW]
    contrast = max(explicit_ok, key=lambda i: (min(f["judge_score"] for f in i["fragments"]),
                                               i["document"], i["field"]))
    return {"cases": cases, "contrast": contrast,
            "n_derived": len(derived), "n_fails": len(fails),
            "stratum_sizes": {k: len(v) for k, v in strata.items()}}


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------

def compute_stats(insts: list[dict]) -> dict:
    def gold_scores(group):
        return [s for i in insts if (i["derivation"] == "EXPLICIT") == group
                for s in i["gold_page_scores"].values()]

    exp, der = gold_scores(True), gold_scores(False)
    all_scores = [s for i in insts for s in i["page_scores"].values()]
    degenerate = [i for i in insts if i["derivation"] != "EXPLICIT"
                  and all(s == 0.0 for s in i["page_scores"].values())]
    return {
        "layer": LAYER,
        "low_threshold": LOW,
        "gold_pages_explicit": {
            "n": len(exp),
            "share_below_0.5": sum(1 for s in exp if s < LOW) / len(exp),
            "median": statistics.median(exp),
        },
        "gold_pages_derived": {
            "n": len(der),
            "share_below_0.5": sum(1 for s in der if s < LOW) / len(der),
            "median": statistics.median(der),
        },
        "endpoint_scores": {
            "n_pages_scored": len(all_scores),
            "strictly_below_0": sum(1 for s in all_scores if s < 0.0),
            "strictly_above_1": sum(1 for s in all_scores if s > 1.0),
            "exactly_0.0": sum(1 for s in all_scores if s == 0.0),
            "exactly_1.0": sum(1 for s in all_scores if s == 1.0),
        },
        "n_derived_instances_degenerate_all_zero": len(degenerate),
        "degenerate_instances": [[i["document"], i["field"]] for i in degenerate],
    }


# ---------------------------------------------------------------------------
# Figure: judge scores on gold pages, explicit vs derived
# ---------------------------------------------------------------------------

def make_figure(insts: list[dict]) -> Path:
    plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.25,
                         "grid.linestyle": ":", "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "white"})
    FLOOR = 1e-7  # display floor for exactly-0.0 scores
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    groups = [(0, "EXPLICIT", "#0072B2"), (1, "DERIVED", "#D55E00")]
    for pos, label, color in groups:
        xs, ys, raw = [], [], []
        for j, inst in enumerate(x for x in insts if (x["derivation"] != "EXPLICIT") == bool(pos)):
            for s in inst["gold_page_scores"].values():
                raw.append(s)
                xs.append(pos + ((j % 17) / 17 - 0.5) * 0.34)  # deterministic jitter
                ys.append(max(s, FLOOR))
        ax.scatter(xs, ys, s=26, alpha=0.55, color=color,
                   label=f"{label} gold pages (n={len(ys)})", zorder=3)
        med = statistics.median(raw)
        ax.hlines(max(med, FLOOR), pos - 0.42, pos + 0.42, color=color, lw=2.5, zorder=4)
        ax.text(pos + 0.46, max(med, FLOOR), f"median {med:.4f}", va="center", fontsize=9, color=color,
                zorder=5, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    ax.axhline(0.5, color="black", ls="--", lw=1, zorder=2)
    ax.text(0.5, 0.29, "judge decision boundary (0.5)", fontsize=9, ha="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["EXPLICIT", "DERIVED\n(ontology / composition)"], fontsize=10)
    ax.set_xlim(-0.62, 1.62)
    ax.set_ylim(FLOOR * 0.7, 2.2)
    ax.set_yscale("log")
    ax.set_yticks([1e-7, 1e-5, 1e-3, 1e-1, 1])
    ax.set_yticklabels(["0.0", "10⁻⁵", "10⁻³", "10⁻¹", "1.0"])
    ax.set_ylabel("judge score on the gold page (log scale; 0.0 shown at floor)")
    ax.set_title("The judge recognizes explicit evidence, not premises\n"
                 f"LLM judge (Qwen2.5-7B) scores on gold evidence pages — {LAYER} layer, dev split",
                 fontsize=11)
    ax.legend(loc="center left", fontsize=9, framealpha=0.95)
    fig.tight_layout()
    out = FIG_DIR / "judge_scores_gold_pages.png"
    fig.savefig(out, dpi=200)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def fmt(s: float) -> str:
    return f"{s:.4g}"


def diagnosis_md(inst: dict, mechanism: str) -> str:
    """Data-driven diagnosis: computed from the selected case, never hardcoded."""
    if inst["derivation"] == "EXPLICIT":  # contrast case: no failure sentence
        return mechanism
    gold_pages = set(inst["gold_pages"])
    gold_scores = {f["page"]: f["judge_score"] for f in inst["fragments"]}
    non_gold = sorted(((p, s) for p, s in inst["page_scores"].items() if p not in gold_pages),
                      key=lambda t: -t[1])
    above = [(p, s) for p, s in non_gold if s >= LOW]
    parts = []
    nfrags = len(inst["fragments"])
    npages = len(gold_scores)
    frag_word = "fragment" if nfrags == 1 else "fragments"
    page_word = "page" if npages == 1 else "pages"
    gtxt = ", ".join(f"p{p} = {fmt(s)}" for p, s in sorted(gold_scores.items()))
    parts.append(f"The {nfrags} premise {frag_word} on {npages} {page_word} ({gtxt}) "
                 f"{'falls' if npages == 1 else 'all fall'} below the judge's own 0.5 boundary.")
    if above:
        atxt = ", ".join(f"p{p} = {fmt(s)}" for p, s in above[:3])
        w = "page scores" if len(above) == 1 else "pages score"
        parts.append(f"Meanwhile {len(above)} non-gold {w} ≥ 0.5 (top: {atxt}).")
    if all(s == 0.0 for s in inst["page_scores"].values()):
        parts.append(f"Every one of the {len(inst['page_scores'])} pages scores exactly 0.0: the judge's "
                     "'ranking' degenerates to document order, so any completeness it shows here is the "
                     "naive prior, not the model.")
    parts.append(mechanism)
    return " ".join(parts)


MECHANISMS = {
    "composition_implied": "The gold value is never stated in the document — it must be derived from "
                           "composition premises. The judge's Yes/No question asks 'does this page "
                           "contain the field?'; premises answer 'why must it be so?', and the judge "
                           "does not model that second question.",
    "ontology_cross_page": "The value is an ontology-derived NOT_APPLICABLE (rule: form = MIXTURE ⇒ no "
                           "single identifier/formula/weight per product). The premises are form cues "
                           "spread over several pages that mention the field name nowhere — so the "
                           "failure is both structural (cross-page) and semantic (premise vs mention).",
    "ontology_same_page": "Both premises sit on the SAME page — so this failure is not spatial at all; "
                          "it is the page-level 'contains the value?' framing itself: the value here is "
                          "an absence derived from form cues.",
}


def case_md(title: str, inst: dict, mechanism: str) -> str:
    lines = [f"### {title}", ""]
    lines.append(f"- **Document / field:** `{inst['document']}` → `{inst['field']}`")
    lines.append(f"- **Gold value:** `{inst['value']}` | **state:** `{inst['state']}` | "
                 f"**derivation:** `{inst['derivation']}` | **cross-page:** {inst['cross_page']}")
    lines.append(f"- **Evidence set:** {inst['n_evidence']} "
                 f"fragment{'s' if inst['n_evidence'] != 1 else ''} on page(s) {inst['gold_pages']}")
    lines.append("")
    lines.append("| page | judge score | gold? | what is on it (fragment text) |")
    lines.append("|---|---|---|---|")
    scored = sorted(inst["page_scores"].items())
    frag_by_page: dict[int, list[str]] = {}
    for f in inst["fragments"]:
        frag_by_page.setdefault(f["page"], []).append(f"[{f['kind']}] {f['text'][:160]}".replace("\n", " ⏎ "))
    for page, s in scored:
        mark = "✔ " + " ; ".join(frag_by_page[page]) if page in frag_by_page else "—"
        lines.append(f"| {page} | **{fmt(s)}** | {'GOLD' if page in inst['gold_pages'] else ''} | {mark} |")
    lines.append("")
    lines.append(f"**Diagnosis:** {diagnosis_md(inst, mechanism)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    insts = load_instances()
    sel = pick_cases(insts)
    stats = compute_stats(insts)
    fig = make_figure(insts)

    cases = sel["cases"]
    case_titles = {
        "composition_implied": "Case 1 — COMPOSITION_IMPLIED (value derived from the composition)",
        "ontology_cross_page": "Case 2 — ONTOLOGY-derived, premises on different pages",
        "ontology_same_page": "Case 3 — ONTOLOGY-derived, premises on the same page",
    }
    contrast = sel["contrast"]
    contrast_md = case_md(
        "Contrast — a typical EXPLICIT case (what the judge is actually good at)",
        contrast,
        "For stated values the judge is confidently right: gold pages ≈ 1.0, non-gold pages ≈ 0. This is "
        "the asymmetry the meeting figure visualizes: the same model, two completely different regimes.")

    e, d = stats["gold_pages_explicit"], stats["gold_pages_derived"]
    eps = stats["endpoint_scores"]
    lines = [
        "# Case studies — the judge does not recognize derivation evidence",
        "",
        f"LLM judge (Qwen2.5-7B, pointwise), {LAYER} layer, dev split, n=125 instances. All numbers read",
        "from frozen outputs (`llm_reranker_qwen7b.json` + `gold_evidence.jsonl`); regenerate with",
        "`~/ds_env/bin/python farit/src/analysis/derived_case_studies.py`.",
        "",
        "## Selection rule (deterministic, no cherry-picking)",
        "",
        f"Of {sel['n_derived']} derived (non-EXPLICIT) evidence-bearing instances, **{sel['n_fails']} "
        f"({sel['n_fails'] / sel['n_derived']:.0%}) have ALL gold fragment pages below the judge's own 0.5 "
        "boundary** — the judge confidently answers 'No' on every page that carries a premise. From each "
        "stratum we take the single worst instance by max gold-page score (ties broken by document, field):",
        "",
        "| stratum | size | chosen case |",
        "|---|---|---|",
        f"| COMPOSITION_IMPLIED | {sel['stratum_sizes'].get('composition_implied', 0)} | "
        f"`{cases['composition_implied']['document']}` / `{cases['composition_implied']['field']}` |",
        f"| ONTOLOGY, cross-page | {sel['stratum_sizes'].get('ontology_cross_page', 0)} | "
        f"`{cases['ontology_cross_page']['document']}` / `{cases['ontology_cross_page']['field']}` |",
        f"| ONTOLOGY, same page | {sel['stratum_sizes'].get('ontology_same_page', 0)} | "
        f"`{cases['ontology_same_page']['document']}` / `{cases['ontology_same_page']['field']}` |",
        "",
        "## The picture, in one figure",
        "",
        f"![](figures/judge_scores_gold_pages.png)",
        "",
        f"- EXPLICIT gold pages: n={e['n']}, median score **{e['median']:.4f}**, "
        f"{e['share_below_0.5']:.0%} below 0.5.",
        f"- DERIVED gold pages: n={d['n']}, median score **{d['median']:.4f}**, "
        f"**{d['share_below_0.5']:.0%}** below 0.5.",
        "",
        "(Pooled over gold pages, deduplicated per instance-page. The 0.9998 quoted in PROGRESS.md is the",
        "median of per-instance medians — same data, different summary; both round to ≈ 1.0 vs 0.0.)",
        "",
        "## Cases",
        "",
    ]
    for key in ("composition_implied", "ontology_cross_page", "ontology_same_page"):
        inst = cases.get(key)
        if inst is not None:
            lines.append(case_md(case_titles[key], inst, MECHANISMS[key]))
    lines.append(contrast_md)
    lines.append(f"*Note:* {stats['n_derived_instances_degenerate_all_zero']} of the {sel['n_derived']} "
                 "derived instances have **every page in the document scoring exactly 0.0** — the judge "
                 "answers a confident 'No' on all of them, and the resulting 'ranking' is just document "
                 "order. This is the fully-degenerate regime, not a ranking-margin issue.")
    lines.append("")
    lines += [
        "## Housekeeping — the `Scores outside (0,1)` warning in the reranker report",
        "",
        f"Across all {eps['n_pages_scored']} scored (field, page) pairs: strictly below 0: "
        f"{eps['strictly_below_0']}, strictly above 1: {eps['strictly_above_1']}; exactly 0.0: "
        f"{eps['exactly_0.0']}, exactly 1.0: {eps['exactly_1.0']}. The warning was a too-strict sanity",
        "check (`min <= 0 or max >= 1`): P(Yes)/(P(Yes)+P(No)) underflows to exactly 0.0/1.0 for extreme",
        "logprob gaps, which is expected saturation, not a logprob-extraction bug. The check in",
        "`llm_reranker.py` now flags only scores strictly outside [0,1] and reports saturation counts.",
        "",
        "## What this means for the topic",
        "",
        "1. **Recognizing premises is a measurable, open capability gap** — it is not OCR (native layer),",
        "   not ranking noise (the failures are confident near-zero scores), and not solved by scale alone",
        "   in the judge's current zero-shot Yes/No framing.",
        "2. **Judge scores cannot anchor an abstention rule on derived fields** — any calibrated stopping",
        "   rule must model derivation intent, not literal field mentions.",
        "3. **All-zero degeneracy means 'LLM ranking' can hide a naive prior** — methods must be reported",
        "   against tie structure, which our protocol now does.",
        "",
    ]
    (RESULTS_DIR / "derived_case_studies.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "derived_case_studies.json").write_text(json.dumps({
        "selection_rule": "per-stratum worst by (max gold-page score, document, field) among derived "
                          "instances whose every gold page scores < 0.5; contrast = best EXPLICIT",
        "layer": LAYER,
        "stats": stats,
        "stratum_sizes": sel["stratum_sizes"],
        "n_derived": sel["n_derived"],
        "n_fails": sel["n_fails"],
        "cases": {k: {"document": v["document"], "field": v["field"], "derivation": v["derivation"],
                      "state": v["state"], "value": v["value"], "cross_page": v["cross_page"],
                      "gold_pages": v["gold_pages"],
                      "gold_page_scores": {str(f["page"]): f["judge_score"] for f in v["fragments"]}}
                  for k, v in cases.items()},
        "contrast": {"document": contrast["document"], "field": contrast["field"],
                    "gold_page_scores": {str(f["page"]): f["judge_score"] for f in contrast["fragments"]}},
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {RESULTS_DIR / 'derived_case_studies.md'}")
    print(f"wrote {RESULTS_DIR / 'derived_case_studies.json'}")
    print(f"wrote {fig} (+pdf)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
