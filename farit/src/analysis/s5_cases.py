#!/usr/bin/env python3
"""S5 — real extraction error cases + a 5-category error taxonomy (TASK-018).

Reads the S4 battery predictions (5 methods x 2 layers, Qwen3.5-2B) and gold
v1.3 ``dev``, selects a deterministic sample of **24** ``(document, field)``
cases (18 hard from the derived / cross-page / multi-evidence slices where at
least one method fails joint, plus 6 random controls, seed=42), scores each case
with ``sdsbench.evaluator`` in every method x layer cell, classifies the residual
error into one of five categories (annotations / entity attribution / reasoning /
values / evidence), records which methods solve the case and at what cost, and
writes ``farit/results/s5_cases.{json,md}``.

The S4 predictions are a frozen input (never written). Only ``farit/`` is
written. The locked split is refused by ``guard_split`` and by the loader.

CLI (from the repository root)::

    ~/ds_env/bin/python farit/src/analysis/s5_cases.py            # full run
    ~/ds_env/bin/python farit/src/analysis/s5_cases.py --check    # readiness only
    ~/ds_env/bin/python farit/src/analysis/s5_cases.py --smoke    # logic test on _smoke files

Unit and rule
-------------
A case is a ``(document, field)`` pair, not a layer or a method: the two text
layers and all six methods are analysed *inside* one case, so 24 pairs stay 24
cases. Hard pool = pairs in the slices ``derived``/``cross_page``/
``multi_evidence`` (primary-slice priority derived > cross_page > multi_evidence
> single_evidence) where at least one method fails the 7-axis joint on at least
one layer. Selection is deterministic: both pools are sorted by
``(document, field)`` and sampled with ``random.Random(42)``; the control pool
excludes the 18 hard pairs by construction.

Category priority (tie-break): annotations -> entity attribution -> reasoning ->
values -> evidence.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_DIR = Path(__file__).resolve().parent
for _path in (str(REPO_ROOT), str(ANALYSIS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sdsbench import annotations, derivation as sds_derivation  # noqa: E402
from sdsbench.evaluator import AXES, PASSING, evaluate  # noqa: E402
from sdsbench.matching import names_equal, normalize_cas, values_equal  # noqa: E402
from sdsbench.ontology import (  # noqa: E402
    FIELD_SPECS,
    PRODUCT_FIELD_NAMES,
    FieldState,
)
from sdsbench.schema import PredictionSet  # noqa: E402
from scripts.evaluate import guard_split  # noqa: E402

METHODS: tuple[str, ...] = ("M1", "M2", "M3", "M4", "M5", "M6")
LAYERS: tuple[str, ...] = ("native", "ocr")
# Preference order when ranking methods (M4 = the strong non-LLM rule baseline).
METHOD_ORDER: dict[str, int] = {"M4": 0, "M1": 1, "M3": 2, "M5": 3, "M2": 4, "M6": 5}
LLM_METHODS: tuple[str, ...] = ("M1", "M2", "M3", "M5", "M6")
IDENTIFIER_FIELDS: tuple[str, ...] = (
    "product_cas_number",
    "chemical_formula",
    "molecular_weight",
)

HARD_SLICES: tuple[str, ...] = ("derived", "cross_page", "multi_evidence")
SLICE_PRIORITY: tuple[str, ...] = ("derived", "cross_page", "multi_evidence", "single_evidence")
TAXONOMY_ORDER: tuple[str, ...] = (
    "annotations",
    "entity attribution",
    "reasoning",
    "values",
    "evidence",
)
CATEGORY_NONE = "none"

SEED = 42
N_HARD = 18
N_TOTAL = 24

DEFAULT_PRED_DIR = REPO_ROOT / "farit" / "data" / "predictions"
DEFAULT_RESULTS = REPO_ROOT / "farit" / "results" / "s5_cases"
DEFAULT_SMOKE_RESULTS = REPO_ROOT / "farit" / "logs" / "TASK-018" / "s5_cases_smoke"

CAS_RE = re.compile(r"(?<![\d-])\d{2,7}-\d{2}-\d(?![\d-])")

# Manual overrides for cases where the gold itself is the defect. Kept empty by
# default: the automatic rule only fires on gold fields the annotation admits as
# ambiguous (an accepted alternative state/value), which is the defensible,
# citable signal. Add ``(document, field) -> {"defect": ..., "ref": ...}`` after a
# manual read-through to force the ``annotations`` category.
ANNOTATION_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {}


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------


def candidate_path(pred_dir: Path, method: str, layer: str, smoke: bool) -> Path:
    stem = f"s4_{method}_{layer}" + ("_smoke" if smoke else "")
    return pred_dir / f"{stem}.json"


def meta_path(path: Path) -> Path:
    return path.with_name(path.stem + ".meta.json")


def _dev_documents() -> list:
    gold = annotations.load_gold(split="dev")
    guard_split(gold, allow_locked=False)
    return gold


def readiness(pred_dir: Path, smoke: bool, expected_docs: list[str]) -> dict:
    """Which method x layer prediction files exist and what document set they cover."""
    expected = set(expected_docs)
    cells: dict[str, dict] = {}
    ready = True
    for method in METHODS:
        for layer in LAYERS:
            path = candidate_path(pred_dir, method, layer, smoke)
            key = f"{method}/{layer}"
            if not path.exists():
                cells[key] = {"present": False, "documents": 0, "missing": sorted(expected)}
                ready = False
                continue
            prediction_set = PredictionSet.load(path)
            documents = set(prediction_set.document_names)
            missing = sorted(expected - documents)
            scope = prediction_set.configuration.get("scope")
            cells[key] = {
                "present": True,
                "file": path.name,
                "scope": scope,
                "documents": len(documents),
                "missing_documents": missing,
            }
            if missing:
                ready = False
    return {"ready": ready, "smoke": smoke, "expected_documents": len(expected), "cells": cells}


def load_evaluations(
    pred_dir: Path, smoke: bool, gold: list
) -> tuple[dict, dict, list[str]]:
    """Score every available method x layer cell; index instances by (document, field)."""
    evals: dict[tuple[str, str], dict] = {}
    meta: dict[tuple[str, str], dict] = {}
    skipped: list[str] = []
    for method in METHODS:
        for layer in LAYERS:
            path = candidate_path(pred_dir, method, layer, smoke)
            key = f"{method}/{layer}"
            if not path.exists():
                skipped.append(key)
                continue
            prediction_set = PredictionSet.load(path)
            predicted = set(prediction_set.document_names)
            subset = [item for item in gold if item.document in predicted]
            guard_split(subset, allow_locked=False)
            summary = evaluate(subset, prediction_set)
            evals[(method, layer)] = {
                (item.document, item.field): item for item in summary.instances
            }
            meta[(method, layer)] = load_cost(path)
    return evals, meta, skipped


def load_cost(path: Path) -> dict:
    """Aggregate per-call cost, keyed by document (meta.calls carry the document)."""
    meta_file = meta_path(path)
    result = {"cost": None, "info": None, "backend": None, "model": None, "per_document": {}}
    if not meta_file.exists():
        return result
    with open(meta_file, encoding="utf-8") as handle:
        meta = json.load(handle)
    per_document: dict[str, dict] = defaultdict(
        lambda: {"latency_s": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "n_calls": 0}
    )
    for call in meta.get("calls", []):
        document = call.get("document")
        if document is None:
            continue
        bucket = per_document[document]
        bucket["latency_s"] += float(call.get("latency_s", 0.0) or 0.0)
        bucket["prompt_tokens"] += int(call.get("prompt_tokens", 0) or 0)
        bucket["completion_tokens"] += int(call.get("completion_tokens", 0) or 0)
        bucket["n_calls"] += int(call.get("n_calls", 0) or 0)
    result.update(
        cost=meta.get("cost"),
        info=meta.get("info"),
        backend=meta.get("backend"),
        model=meta.get("model"),
        per_document=dict(per_document),
    )
    return result


# ---------------------------------------------------------------------------
# Slices
# ---------------------------------------------------------------------------


def slices_for(gold_field) -> list[str]:
    targets = gold_field.gold_targets
    pages = {item.page for item in targets}
    tags: list[str] = []
    if gold_field.derivation.is_derived:
        tags.append("derived")
    if len(pages) > 1:
        tags.append("cross_page")
    if len(targets) >= 2:
        tags.append("multi_evidence")
    elif len(targets) == 1:
        tags.append("single_evidence")
    return tags


def primary_slice(tags: list[str]) -> str:
    for name in SLICE_PRIORITY:
        if name in tags:
            return name
    return "unknown"


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class Pair:
    document: str
    field: str


def build_pairs(gold: list) -> list[tuple[Pair, object, object]]:
    """Every (document, field) dev pair with its gold field + document annotation."""
    out = []
    for document in gold:
        for name in PRODUCT_FIELD_NAMES:
            field = document.fields.get(name)
            if field is None:
                continue
            out.append((Pair(document=document.document, field=name), field, document))
    return out


def joint_map(evals: dict) -> dict[tuple[str, str], dict[Pair, bool]]:
    """joint_correct per method x layer, keyed by pair; None where unscored."""
    result: dict[tuple[str, str], dict[Pair, bool]] = {}
    for key, by_pair in evals.items():
        result[key] = {
            Pair(document=doc, field=field): instance.joint_correct
            for (doc, field), instance in by_pair.items()
        }
    return result


def select_pairs(
    pairs: list[tuple[Pair, object, object]], joints: dict, smoke: bool
) -> tuple[list[Pair], list[Pair], dict]:
    """Deterministically pick the hard pairs and the random controls."""
    fields = {pair: field for pair, field, _ in pairs}
    hard_pool: list[Pair] = []
    for pair, field, _ in pairs:
        tags = set(slices_for(field))
        if not (tags & set(HARD_SLICES)):
            continue
        failed = any(
            joints[key].get(pair) is False for key in joints
        )
        if failed:
            hard_pool.append(pair)
    hard_pool.sort()

    rng_hard = random.Random(SEED)
    n_hard = len(hard_pool) if smoke else min(N_HARD, len(hard_pool))
    hard = sorted(rng_hard.sample(hard_pool, n_hard)) if n_hard else []

    all_pairs = sorted(pair for pair, _, _ in pairs)
    control_pool = [pair for pair in all_pairs if pair not in set(hard)]
    rng_control = random.Random(SEED)
    n_total = len(hard) + 6 if smoke else N_TOTAL
    n_control = min(n_total - len(hard), len(control_pool))
    controls = sorted(rng_control.sample(control_pool, n_control))

    selection_info = {
        "seed": SEED,
        "n_total_pairs": len(pairs),
        "n_hard_pool": len(hard_pool),
        "n_hard": len(hard),
        "n_control": len(controls),
        "n_control_pool": len(control_pool),
        "hard_slices": list(HARD_SLICES),
        "slice_priority": list(SLICE_PRIORITY),
        "hard_rule": (
            "pairs whose slices include any of derived/cross_page/multi_evidence "
            "and where at least one method fails the 7-axis joint on at least one layer"
        ),
        "control_rule": "random sample (seed=42) from all dev pairs minus the hard pairs",
        "primary_slices_hard": dict(Counter(primary_slice(slices_for(fields[pair])) for pair in hard)),
        "primary_slices_control": dict(
            Counter(primary_slice(slices_for(fields[pair])) for pair in controls)
        ),
    }
    return hard, controls, selection_info


# ---------------------------------------------------------------------------
# Per-instance payload
# ---------------------------------------------------------------------------


def _inst_payload(instance) -> dict | None:
    if instance is None:
        return None
    return {
        "joint": instance.joint_correct,
        "axes": dict(instance.axes),
        "failed_axes": [axis for axis in AXES if instance.axes[axis] not in PASSING],
        "predicted_state": instance.predicted_state.value if instance.predicted_state else None,
        "predicted_value": instance.predicted_value,
        "predicted_derivation": instance.predicted_derivation,
        "predicted_rule": instance.predicted_rule,
        "predicted_page": instance.predicted_page,
        "predicted_evidence": instance.predicted_evidence,
        "verbatim": instance.verbatim,
        "verbatim_fuzzy_score": round(instance.verbatim_fuzzy_score, 3),
        "support": instance.axes.get("support"),
        "support_note": instance.support_note,
        "span_iou": round(instance.span_iou, 4),
        "span_coverage": round(instance.span_coverage, 4),
        "bbox_iou": round(instance.bbox_iou, 4),
        "bbox_coverage": round(instance.bbox_coverage, 4),
        "target_groups": instance.target_groups,
        "groups_located": instance.groups_located,
        "premise_roles_described": instance.premise_roles_described,
        "gold_requires_evidence": instance.gold_requires_evidence,
        "gold_derivation": instance.gold_derivation,
        "gold_rule": instance.gold_rule,
        "evidence_role": instance.evidence_role,
        "gold_pages": list(instance.gold_pages),
        "gold_evidence": instance.gold_evidence,
        "note": instance.note,
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def _entity_reasons(field: str, payload: dict, doc_ann, gold_field) -> list[str]:
    reasons: list[str] = []
    items = doc_ann.ingredients.items
    ingredient_cas = {normalize_cas(item.cas_number) for item in items if item.cas_number}
    ingredient_names = [item.name for item in items if item.name]
    text = f"{payload.get('predicted_value') or ''} || {payload.get('predicted_evidence') or ''}"
    cited_cas = {normalize_cas(match) for match in CAS_RE.findall(text)}

    if field in IDENTIFIER_FIELDS and (cited_cas & ingredient_cas):
        shared = ", ".join(sorted(cited_cas & ingredient_cas))
        reasons.append(
            f"the value/citation carries a declared ingredient CAS ({shared}) for a "
            "product-level identifier"
        )

    if field in IDENTIFIER_FIELDS and payload.get("predicted_evidence"):
        # A product-level identifier under identifier_undefined must rest on a form
        # declaration; citing a composition row is component-level evidence.
        roles = sds_derivation.premise_roles(payload["predicted_evidence"])
        component_roles = {
            sds_derivation.PremiseRole.COMPOSITION_HEADER,
            sds_derivation.PremiseRole.SOLE_CONSTITUENT,
            sds_derivation.PremiseRole.PARTIAL_CONSTITUENT,
        }
        if (roles & component_roles) and sds_derivation.PremiseRole.FORM_DECLARATION not in roles:
            reasons.append(
                "a component/composition row is cited as the premise of a product-level "
                f"'{field}' claim"
            )

    predicted_value = payload.get("predicted_value")
    product_name_field = doc_ann.fields.get("product_name")
    supplier_field = doc_ann.fields.get("supplier_name")
    if predicted_value and field == "product_name" and supplier_field and supplier_field.value:
        if names_equal(predicted_value, supplier_field.value):
            reasons.append("product_name took the supplier's name")
    if predicted_value and field == "supplier_name" and product_name_field and product_name_field.value:
        if names_equal(predicted_value, product_name_field.value):
            reasons.append("supplier_name took the product's trade name")
    if predicted_value and field == "product_name":
        for name in ingredient_names:
            if names_equal(predicted_value, name):
                reasons.append(f"product_name took a declared ingredient name ({name!r})")
                break
    return reasons


def _reasoning_reasons(payload: dict, gold_field) -> list[str]:
    """Derivation-level defects: a derived conclusion that is wrong or missing,
    or a spurious derivation declared for an explicit (direct) gold claim."""
    reasons: list[str] = []
    derivation_violated = payload["axes"].get("derivation") == "violated"
    if gold_field.derivation.is_derived:
        if payload.get("predicted_state") == FieldState.NOT_STATED.value:
            reasons.append("no derived conclusion produced (prediction is NOT_STATED)")
        if derivation_violated:
            if payload.get("predicted_rule") != payload.get("gold_rule"):
                reasons.append(
                    f"rule {payload.get('predicted_rule')!r} vs gold {payload.get('gold_rule')!r}"
                )
            reasons.append(
                f"derivation {payload.get('predicted_derivation')} vs gold DERIVED"
            )
        groups = payload.get("target_groups") or 0
        located = payload.get("groups_located") or 0
        if groups and located < groups:
            reasons.append(f"located {located}/{groups} required premise role(s)")
    elif derivation_violated:
        rule = payload.get("predicted_rule")
        reasons.append(
            f"gold is a direct (EXPLICIT) claim but the prediction declares "
            f"{payload.get('predicted_derivation')}"
            + (f" with rule {rule!r}" if rule else "")
        )
    return reasons


def _annotation_reason(payload: dict, gold_field, pair: Pair) -> str | None:
    override = ANNOTATION_OVERRIDES.get((pair.document, pair.field))
    if override:
        return f"{override.get('defect', 'gold defect')} [{override.get('ref', '')}]".strip()
    if not gold_field.ambiguous:
        return None
    predicted_state = payload.get("predicted_state")
    alternative = gold_field.alternative_state
    if alternative is not None and predicted_state == alternative.value:
        return (
            f"gold marks '{pair.field}' ambiguous and admits {alternative.value} as an "
            "alternative state (gold note: "
            f"{gold_field.note or 'n/a'}); the prediction is that accepted alternative"
        )
    predicted_value = payload.get("predicted_value")
    if predicted_value:
        kind = FIELD_SPECS[pair.field].value_kind
        tolerance = FIELD_SPECS[pair.field].numeric_tolerance
        for accepted in gold_field.all_values:
            if values_equal(predicted_value, accepted, kind, tolerance):
                return (
                    f"gold marks '{pair.field}' ambiguous; the predicted value {predicted_value!r} "
                    f"is an accepted gold value"
                )
    return None


def classify(
    payload: dict, gold_field, doc_ann, pair: Pair
) -> tuple[str, str, str, list[str]]:
    """Return (taxonomy, actual_error, cause, reasons)."""
    annotation = _annotation_reason(payload, gold_field, pair)
    if annotation:
        return "annotations", "annotation", annotation, [annotation]

    entity = _entity_reasons(pair.field, payload, doc_ann, gold_field)
    if entity:
        return "entity attribution", "entity attribution", "; ".join(entity), entity

    reasoning = _reasoning_reasons(payload, gold_field)
    if reasoning:
        label = "reasoning (derived)" if gold_field.derivation.is_derived else "reasoning (derivation)"
        return "reasoning", label, "; ".join(reasoning), reasoning

    axes = payload["axes"]
    value_bad = axes.get("state") == "violated" or axes.get("value") == "violated"
    if value_bad:
        cause = (
            f"predicted {payload.get('predicted_state')}/{payload.get('predicted_value')!r} "
            f"vs gold {gold_field.state.value}/{gold_field.value!r}"
        )
        return "values", "value", cause, [cause]

    evidence_reasons: list[str] = []
    if axes.get("page") == "violated":
        evidence_reasons.append(
            f"cited page {payload.get('predicted_page')} vs gold page(s) {payload.get('gold_pages')}"
        )
    if axes.get("span") == "violated":
        evidence_reasons.append(
            f"span IoU {payload.get('span_iou')} / coverage {payload.get('span_coverage')} below threshold"
        )
    if axes.get("bbox") == "violated":
        evidence_reasons.append(
            f"bbox IoU {payload.get('bbox_iou')} / coverage {payload.get('bbox_coverage')} below threshold"
        )
    if payload.get("verbatim") is False:
        evidence_reasons.append("cited quote is not verbatim on its page")
    if axes.get("support") in ("violated", "undecidable"):
        evidence_reasons.append(f"support: {payload.get('support_note') or axes.get('support')}")
    if not evidence_reasons:
        evidence_reasons.append(
            "claim fails the joint conjunction on " + ", ".join(payload["failed_axes"])
        )
    return "evidence", "evidence localization", "; ".join(evidence_reasons), evidence_reasons


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------


def case_cost(costs: dict, method: str, pair: Pair) -> dict | None:
    """Total cost of one method on one case, summed over both layers."""
    total = {"latency_s": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "n_calls": 0}
    seen = False
    for layer in LAYERS:
        cell = costs.get((method, layer))
        if cell is None:
            continue
        bucket = cell["per_document"].get(pair.document)
        if bucket is None:
            continue
        seen = True
        total["latency_s"] += bucket["latency_s"]
        total["prompt_tokens"] += bucket["prompt_tokens"]
        total["completion_tokens"] += bucket["completion_tokens"]
        total["n_calls"] += bucket["n_calls"]
    if not seen:
        return None
    total["latency_s"] = round(total["latency_s"], 3)
    total["cost_basis"] = "latency_s (sum over native+ocr)"
    return total


def _min_cost(costs: dict, methods: list[str], pair: Pair) -> dict | None:
    best = None
    for method in methods:
        cost = case_cost(costs, method, pair)
        if cost is None:
            continue
        candidate = {"method": method, **cost}
        if best is None or candidate["latency_s"] < best["latency_s"]:
            best = candidate
    return best


# ---------------------------------------------------------------------------
# Case construction
# ---------------------------------------------------------------------------


def build_case(
    index: int,
    pair: Pair,
    gold_field,
    doc_ann,
    selection: str,
    evals: dict,
    costs: dict,
) -> dict:
    tags = slices_for(gold_field)
    per_layer: dict[str, dict] = {}
    joint: dict[tuple[str, str], bool | None] = {}
    for layer in LAYERS:
        per_layer[layer] = {}
        for method in METHODS:
            instance = evals.get((method, layer), {}).get((pair.document, pair.field))
            per_layer[layer][method] = _inst_payload(instance)
            joint[(method, layer)] = None if instance is None else instance.joint_correct

    solved_by = [
        method
        for method in METHODS
        if joint.get((method, "native")) is True and joint.get((method, "ocr")) is True
    ]

    def passes(method: str) -> int:
        return sum(1 for layer in LAYERS if joint.get((method, layer)) is True)

    failing = [
        method
        for method in METHODS
        if any(joint.get((method, layer)) is False for layer in LAYERS)
    ]

    if not failing:
        taxonomy, actual_error, cause, reasons = (
            CATEGORY_NONE,
            "none (control)",
            "all methods pass joint on both layers",
            [],
        )
        reference_method = None
        reference_layer = None
    else:
        reference_method = sorted(failing, key=lambda m: (-passes(m), METHOD_ORDER[m]))[0]
        reference_layer = (
            "native" if joint.get((reference_method, "native")) is False else "ocr"
        )
        payload = per_layer[reference_layer][reference_method]
        taxonomy, actual_error, cause, reasons = classify(
            payload, gold_field, doc_ann, pair
        )

    min_solved = _min_cost(costs, solved_by, pair)
    min_llm_solved = _min_cost(costs, [m for m in solved_by if m in LLM_METHODS], pair)

    per_method_passes = {method: passes(method) for method in METHODS}
    partial_coverage = any(joint.get((method, layer)) is None for method in METHODS for layer in LAYERS)

    return {
        "case_id": index,
        "document": pair.document,
        "field": pair.field,
        "selection": selection,
        "slices": tags,
        "primary_slice": primary_slice(tags),
        "evidence_set_size": len(gold_field.gold_targets),
        "partial_coverage": partial_coverage,
        "per_method_passes": per_method_passes,
        "gold": {
            "state": gold_field.state.value,
            "value": gold_field.value,
            "all_values": gold_field.all_values,
            "derivation": gold_field.derivation.value,
            "rule": gold_field.rule,
            "ambiguous": gold_field.ambiguous,
            "alternative_state": gold_field.alternative_state.value
            if gold_field.alternative_state
            else None,
            "note": gold_field.note,
            "pages": sorted({item.page for item in gold_field.gold_targets}),
            "evidence": [{"page": item.page, "text": item.text} for item in gold_field.gold_targets],
        },
        "reference_method": reference_method,
        "reference_layer": reference_layer,
        "per_layer": per_layer,
        "solved_by": solved_by,
        "min_cost_solved": min_solved,
        "min_cost_llm_solved": min_llm_solved,
        "actual_error": actual_error,
        "cause": cause,
        "taxonomy": taxonomy,
        "classification_reasons": reasons,
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize(cases: list[dict], costs: dict, selection_info: dict) -> dict:
    taxonomy_counts = Counter(case["taxonomy"] for case in cases)
    by_selection = {
        selection: dict(Counter(case["taxonomy"] for case in cases if case["selection"] == selection))
        for selection in ("hard", "control")
    }
    # Which methods solve which category (a method solves a case if joint on both layers).
    solvers: dict[str, dict[str, int]] = {category: {} for category in (*TAXONOMY_ORDER, CATEGORY_NONE)}
    for case in cases:
        bucket = solvers[case["taxonomy"]]
        for method in (case["solved_by"] or ["(none)"]):
            bucket[method] = bucket.get(method, 0) + 1
    category_totals = {
        category: sum(1 for case in cases if case["taxonomy"] == category)
        for category in (*TAXONOMY_ORDER, CATEGORY_NONE)
    }
    unresolved = [
        {
            "case_id": case["case_id"],
            "document": case["document"],
            "field": case["field"],
            "taxonomy": case["taxonomy"],
        }
        for case in cases
        if not case["solved_by"] and case["taxonomy"] != CATEGORY_NONE and not case["partial_coverage"]
    ]
    # Per-method cost aggregation (from *.meta.json), as in the S4 battery.
    method_cost: dict[str, dict] = {}
    for method in METHODS:
        for layer in LAYERS:
            cell = costs.get((method, layer))
            if cell is None:
                continue
            cost = cell.get("cost")
            method_cost[f"{method}/{layer}"] = {
                "backend": cell.get("backend"),
                "model": "rules-none" if method == "M4" else cell.get("model"),
                "cost": cost,
            }
    return {
        "n_cases": len(cases),
        "n_hard": sum(1 for case in cases if case["selection"] == "hard"),
        "n_control": sum(1 for case in cases if case["selection"] == "control"),
        "selection": selection_info,
        "taxonomy_counts": dict(taxonomy_counts),
        "category_totals": category_totals,
        "taxonomy_by_selection": by_selection,
        "category_solvers": solvers,
        "unresolved_cases": unresolved,
        "n_unresolved": len(unresolved),
        "method_cost": method_cost,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _fmt_cost(cost: dict | None) -> str:
    if cost is None:
        return "—"
    parts = [f"{cost['method']}: {cost['latency_s']:.1f}s"]
    if cost["n_calls"] == 0:
        parts.append("0 LLM calls")
    else:
        parts.append(f"{cost['n_calls']} calls, {cost['prompt_tokens']}→{cost['completion_tokens']} tok")
    return " ".join(parts)


def _joint_cell(payload: dict | None) -> str:
    if payload is None:
        return "·"
    if payload["joint"]:
        return "✔"
    return "✘ " + ",".join(payload["failed_axes"])


def render_markdown(result: dict, smoke: bool) -> str:
    summary = result["summary"]
    lines: list[str] = []
    lines.append("# S5 — real extraction cases and the error taxonomy" + (" (smoke)" if smoke else ""))
    lines.append("")
    lines.append(
        "Case = `(document, field)` (both text layers and all six S4 methods live inside one "
        "case). Gold v1.3, dev split. Scored with `sdsbench.evaluator` (7 axes + joint). "
        "S4 predictions are a frozen input."
    )
    lines.append("")
    if result.get("skipped_cells"):
        lines.append(f"**Skipped cells:** {', '.join(result['skipped_cells'])}")
        lines.append("")

    sel = summary["selection"]
    lines.append("## Selection (deterministic)")
    lines.append("")
    lines.append(f"- seed = {sel['seed']}; dev pairs = {sel['n_total_pairs']}")
    lines.append(
        f"- hard pool = {sel['n_hard_pool']} pairs ({sel['hard_rule']}); "
        f"**sampled {sel['n_hard']}**"
    )
    lines.append(
        f"- controls = {sel['n_control']} from {sel['n_control_pool']} remaining pairs "
        "(seed=42, disjoint from hard)"
    )
    lines.append(f"- hard primary slices: {sel['primary_slices_hard']}")
    lines.append(f"- control primary slices: {sel['primary_slices_control']}")
    lines.append(f"- deterministic: **{result['deterministic']}**")
    lines.append("")

    lines.append(f"## Taxonomy over {summary['n_cases']} cases")
    lines.append("")
    lines.append("| category | total | hard | control |")
    lines.append("| --- | ---: | ---: | ---: |")
    for category in (*TAXONOMY_ORDER, CATEGORY_NONE):
        total = summary["category_totals"].get(category, 0)
        hard = summary["taxonomy_by_selection"]["hard"].get(category, 0)
        control = summary["taxonomy_by_selection"]["control"].get(category, 0)
        lines.append(f"| {category} | {total} | {hard} | {control} |")
    lines.append("")

    lines.append("## Which methods solve which category")
    lines.append("")
    lines.append(
        "A method *solves* a case when it passes joint on **both** layers; `(none)` marks "
        "cases no simple method solves (the gap)."
    )
    lines.append("")
    header = "| category | " + " | ".join(METHODS) + " | (none) |"
    lines.append(header)
    lines.append("|" + "|".join(["---"] * (1 + len(METHODS) + 1)) + "|")
    for category in (*TAXONOMY_ORDER, CATEGORY_NONE):
        bucket = summary["category_solvers"].get(category, {})
        cells = [str(bucket.get(method, 0)) for method in METHODS]
        cells.append(str(bucket.get("(none)", 0)))
        lines.append(f"| {category} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Cost per method x layer (from *.meta.json)")
    lines.append("")
    lines.append("| method | layer | backend | n calls | prompt tok | completion tok | latency s |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: |")
    for method in METHODS:
        for layer in LAYERS:
            cell = summary["method_cost"].get(f"{method}/{layer}")
            if cell is None:
                lines.append(f"| {method} | {layer} | - | - | - | - | - |")
                continue
            cost = cell.get("cost") or {}
            lines.append(
                f"| {method} | {layer} | {cell.get('backend')} | {cost.get('n_calls', '-')} | "
                f"{cost.get('prompt_tokens', '-')} | {cost.get('completion_tokens', '-')} | "
                f"{cost.get('latency_s', '-')} |"
            )
    lines.append("")

    lines.append("## Unresolved cases (no simple method solves them)")
    lines.append("")
    if not summary["unresolved_cases"]:
        lines.append("_none_")
    else:
        lines.append("| case | document | field | taxonomy |")
        lines.append("| ---: | --- | --- | --- |")
        for item in summary["unresolved_cases"]:
            lines.append(
                f"| {item['case_id']} | {item['document']} | {item['field']} | {item['taxonomy']} |"
            )
    lines.append("")

    lines.append("## Cases")
    lines.append("")
    for case in result["cases"]:
        lines.append(render_case(case))
    return "\n".join(lines) + "\n"


def render_case(case: dict) -> str:
    gold = case["gold"]
    lines: list[str] = []
    lines.append(
        f"### Case {case['case_id']} — `{case['document']}` / `{case['field']}` "
        f"({case['selection']}, primary slice `{case['primary_slice']}`)"
    )
    lines.append("")
    lines.append(f"- **Slices:** [{', '.join(case['slices'])}] · evidence-set {case['evidence_set_size']}")
    lines.append(
        f"- **Gold:** state `{gold['state']}`, value `{gold['value']}`, derivation "
        f"`{gold['derivation']}`"
        + (f", rule `{gold['rule']}`" if gold["rule"] else "")
        + f", page(s) {gold['pages']}"
        + ("  · **ambiguous**" if gold["ambiguous"] else "")
    )
    lines.append(
        f"- **Taxonomy:** **{case['taxonomy']}** · actual_error: _{case['actual_error']}_"
    )
    lines.append(f"- **Cause:** {case['cause']}")
    if case["taxonomy"] == CATEGORY_NONE:
        lines.append("- **solved_by:** — (control; no error to solve)")
    elif case["solved_by"]:
        lines.append(f"- **solved_by:** {case['solved_by']}")
    elif case["partial_coverage"]:
        lines.append("- **solved_by:** — (partial coverage: not every method x layer was scored)")
    else:
        lines.append("- **solved_by:** — (gap: no simple method solves it)")
    lines.append(
        f"- **min_cost_solved:** {_fmt_cost(case['min_cost_solved'])} · "
        f"**min_cost_llm_solved:** {_fmt_cost(case['min_cost_llm_solved'])}"
    )
    if case["reference_method"]:
        lines.append(
            f"- **reference failure:** `{case['reference_method']}` on `{case['reference_layer']}`"
        )
    if case["partial_coverage"]:
        lines.append("- **coverage:** partial — some method x layer cells were not scored")
    lines.append("")
    lines.append("| method | native | ocr |")
    lines.append("| --- | --- | --- |")
    for method in METHODS:
        lines.append(
            f"| {method} | {_joint_cell(case['per_layer']['native'].get(method))} | "
            f"{_joint_cell(case['per_layer']['ocr'].get(method))} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S5 cases + taxonomy")
    parser.add_argument("--smoke", action="store_true", help="use the s4_*_smoke.json inputs")
    parser.add_argument("--check", action="store_true", help="report readiness only, write nothing")
    parser.add_argument("--predictions-dir", type=Path, default=DEFAULT_PRED_DIR)
    parser.add_argument("--out", type=Path, default=None, help="output stem (without extension)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    gold = _dev_documents()
    documents = [item.document for item in gold]
    gold_by_pair = {
        Pair(document=item.document, field=name): (field, item)
        for item in gold
        for name, field in item.fields.items()
    }
    pairs = build_pairs(gold)

    status = readiness(args.predictions_dir, args.smoke, documents)
    if args.check:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0 if status["ready"] else 3
    if not status["ready"] and not args.smoke:
        print("HARNESS READY, AWAITING FULL S4 RUN")
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 3

    evals, costs, skipped = load_evaluations(args.predictions_dir, args.smoke, gold)
    joints = joint_map(evals)

    hard, controls, selection_info = select_pairs(pairs, joints, args.smoke)
    # Determinism self-check: an independent second selection must agree.
    hard2, controls2, _ = select_pairs(pairs, joints, args.smoke)
    deterministic = hard == hard2 and controls == controls2

    cases: list[dict] = []
    index = 1
    for selection, group in (("hard", hard), ("control", controls)):
        for pair in group:
            gold_field, doc_ann = gold_by_pair[pair]
            cases.append(
                build_case(index, pair, gold_field, doc_ann, selection, evals, costs)
            )
            index += 1

    summary = summarize(cases, costs, selection_info)
    result = {
        "configuration": {
            "gold": "v1.3",
            "split": "dev",
            "scope": "smoke" if args.smoke else "full",
            "unit": "(document, field)",
            "methods": list(METHODS),
            "layers": list(LAYERS),
            "seed": SEED,
            "category_priority": list(TAXONOMY_ORDER),
        },
        "readiness": status,
        "skipped_cells": skipped,
        "deterministic": deterministic,
        "summary": summary,
        "cases": cases,
    }

    out = args.out or (DEFAULT_SMOKE_RESULTS if args.smoke else DEFAULT_RESULTS)
    out.parent.mkdir(parents=True, exist_ok=True)
    json_path = out.with_suffix(".json")
    md_path = out.with_suffix(".md")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(result, args.smoke))
    print(f"cases={len(cases)} (hard={len(hard)}, control={len(controls)}) deterministic={deterministic}")
    print(f"taxonomy: {summary['taxonomy_counts']}")
    print(f"wrote {json_path} and {md_path}")
    if skipped:
        print(f"skipped cells: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())