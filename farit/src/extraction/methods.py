#!/usr/bin/env python3
"""The five S4 extraction methods (TASK-015).

M1 all-fields-one-pass   one whole-document call -> every field + ingredients.
M2 individual-field      one call per (document, field) + one ingredients call.
M3 contextual citation   verifies each M1 citation against the cited page and its
                         neighbours, corrects page/quote; an unrepairable claim
                         degrades to NOT_STATED. Depends on M1.
M4 rules-v4              the inherited non-LLM rule baseline (rows layout),
                         re-scored against gold v1.3. Zero LLM calls.
M5 basic LLM verifier    per M1 claim, a Yes/No support call (gold-free). Yes
                         keeps the claim verbatim; No downgrades it to
                         NOT_STATED (value and evidence removed). Depends on M1.

All four LLM methods reuse Maria's contract machinery from
``sdsbench.extractors.llm`` (``build_messages``, ``LlmOutput``,
``to_document_prediction``, ``resolve_citation``) so the battery is scored on
exactly the same repaired predictions the older LLM baseline used. Because no
engine here enforces JSON-schema output, every model answer is parsed and
repaired before validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from sdsbench import textlayer
from sdsbench.extractors import llm, rules
from sdsbench.ontology import FIELD_SPECS, PRODUCT_FIELD_NAMES, FieldState
from sdsbench.schema import (
    DocumentPrediction,
    EvidenceSpan,
    FieldPrediction,
    IngredientPrediction,
    IngredientsPrediction,
)

try:  # package import (python -m farit.src.extraction.run_battery)
    from . import backends
except ImportError:  # script import (python farit/src/extraction/run_battery.py)
    import backends  # type: ignore

_LAYOUT = "rows"
_STATES = ("PRESENT", "NOT_APPLICABLE", "NO_DATA", "NOT_STATED")
_RULES = ("identifier_undefined_for_form", "composition_implies_form")

# Product fields extracted per call by M2 (ingredients are a separate call).
M2_FIELDS = PRODUCT_FIELD_NAMES


# ---------------------------------------------------------------------------
# Call accounting
# ---------------------------------------------------------------------------


@dataclass
class CallRecord:
    """One backend generation (or an explicit zero-call record for M4)."""

    method: str
    document: str
    layer: str
    backend: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    cached: bool = False
    n_calls: int = 1
    label: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _call(
    backend: backends.Backend,
    method: str,
    document: str,
    layer: str,
    system: str,
    user: str,
    json_schema: dict | None,
    max_tokens: int,
    label: str,
) -> tuple[str, CallRecord]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    try:
        generation = backend.generate(messages, json_schema, max_tokens)
    except Exception as error:  # noqa: BLE001 - recorded per call, the run continues
        return "", CallRecord(
            method=method,
            document=document,
            layer=layer,
            backend=backend.name,
            label=label,
            error=f"{type(error).__name__}: {error}",
        )
    usage = generation.usage
    return generation.text, CallRecord(
        method=method,
        document=document,
        layer=layer,
        backend=backend.name,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        latency_s=usage.latency_s,
        cached=usage.cached,
        label=label,
    )


# ---------------------------------------------------------------------------
# JSON parsing + repair
# ---------------------------------------------------------------------------


def extract_json_object(text: str) -> dict | None:
    """The first JSON object in the model text, tolerating code fences and prose."""
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped
        if stripped.rstrip().endswith("```"):
            stripped = stripped[: stripped.rfind("```")]
        stripped = stripped.strip()
    start = stripped.find("{")
    if start == -1:
        return None
    # raw_decode reads the first complete JSON value and tolerates trailing text
    # (a stray closing brace, an explanation the model appended).
    try:
        parsed, _ = json.JSONDecoder().raw_decode(stripped[start:])
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    end = stripped.rfind("}")
    if end > start:
        try:
            parsed = json.loads(stripped[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def _coerce_citation(obj: Any) -> dict | None:
    if not isinstance(obj, dict):
        return None
    quote = obj.get("quote")
    if quote is None:
        quote = obj.get("text")
    page = obj.get("page")
    if quote is None or page is None:
        return None
    try:
        page = int(page)
    except (TypeError, ValueError):
        return None
    if page < 1:
        page = 1
    return {"page": page, "quote": str(quote)}


def _coerce_citation_list(obj: Any) -> list[dict]:
    if not isinstance(obj, list):
        return []
    return [item for item in (_coerce_citation(entry) for entry in obj) if item]


def _repair_field(obj: Any) -> dict:
    """Coerce one raw field into something ``LlmField`` accepts.

    Accepts the nested shape (``evidence``/``premises`` objects) and the flat
    shape the battery prompts ask for (``page``/``quote`` plus parallel
    ``premise_pages``/``premise_quotes``), and a bare string (treated as a
    PRESENT value with no citation).
    """
    if isinstance(obj, str):
        text = obj.strip()
        if text:
            return {
                "state": "PRESENT",
                "value": text,
                "derivation": "DIRECT",
                "rule": None,
                "evidence": None,
                "premises": [],
            }
        obj = {}
    field = obj if isinstance(obj, dict) else {}
    state = field.get("state")
    if state not in _STATES:
        state = "NOT_STATED"
    value = field.get("value")
    if value is not None:
        value = str(value)
    derivation = field.get("derivation")
    if derivation not in ("DIRECT", "DERIVED"):
        derivation = "DIRECT"
    rule = field.get("rule")
    if rule not in _RULES:
        rule = None

    evidence = _coerce_citation(field.get("evidence"))
    premises = _coerce_citation_list(field.get("premises"))
    if evidence is None and not premises:  # flat shape
        evidence = _coerce_citation({"page": field.get("page"), "quote": field.get("quote")})
        pages = field.get("premise_pages")
        quotes = field.get("premise_quotes")
        if isinstance(pages, list) and isinstance(quotes, list):
            premises = [
                item
                for item in (
                    _coerce_citation({"page": page, "quote": quote})
                    for page, quote in zip(pages, quotes)
                )
                if item
            ]

    if state == "NOT_STATED":
        return {
            "state": "NOT_STATED",
            "value": None,
            "derivation": "DIRECT",
            "rule": None,
            "evidence": None,
            "premises": [],
        }
    if state != "PRESENT":
        value = None
    if derivation == "DERIVED":
        if rule is None or not premises:
            derivation, rule = "DIRECT", None
        else:
            evidence = None
    if derivation == "DIRECT":
        rule, premises = None, []
    return {
        "state": state,
        "value": value,
        "derivation": derivation,
        "rule": rule,
        "evidence": evidence,
        "premises": premises,
    }


def _repair_ingredient(obj: Any) -> dict:
    item = obj if isinstance(obj, dict) else {}
    name = item.get("name")
    cas = item.get("cas_number")
    concentration = item.get("concentration")
    cas_state = item.get("cas_state")
    if cas_state not in _STATES:
        cas_state = "NOT_STATED"
    citation = _coerce_citation(item.get("citation"))
    if citation is None:  # flat shape: page/quote at the item level
        citation = _coerce_citation({"page": item.get("page"), "quote": item.get("quote")})
    return {
        "name": None if name is None else str(name),
        "cas_number": None if cas is None else str(cas),
        "cas_state": cas_state,
        "concentration": None if concentration is None else str(concentration),
        "citation": citation,
    }


def parse_llm_output(text: str) -> llm.LlmOutput | None:
    """Parse + repair a full M1 document output into ``LlmOutput``."""
    data = extract_json_object(text)
    if data is None:
        return None
    repaired = {
        name: _repair_field(data.get(name)) for name in PRODUCT_FIELD_NAMES
    }
    ingredients = [
        _repair_ingredient(item)
        for item in (data.get("ingredients") or [])
        if isinstance(item, dict)
    ]
    state = data.get("ingredients_state")
    if state not in _STATES:
        state = "PRESENT" if ingredients else "NOT_STATED"
    repaired["ingredients_state"] = state
    repaired["ingredients"] = ingredients
    try:
        return llm.LlmOutput.model_validate(repaired)
    except Exception:  # noqa: BLE001 - repair is best effort, caller falls back
        return None


def parse_llm_field(text: str) -> llm.LlmField | None:
    data = extract_json_object(text)
    if data is None:
        return None
    try:
        return llm.LlmField.model_validate(_repair_field(data))
    except Exception:  # noqa: BLE001
        return None


def parse_llm_ingredients(text: str) -> dict | None:
    data = extract_json_object(text)
    if data is None:
        return None
    ingredients = [
        _repair_ingredient(item)
        for item in (data.get("ingredients") or [])
        if isinstance(item, dict)
    ]
    state = data.get("ingredients_state")
    if state not in _STATES:
        state = "PRESENT" if ingredients else "NOT_STATED"
    return {"ingredients_state": state, "ingredients": ingredients}


def _parse_bool_verdict(text: str, key: str) -> bool | None:
    data = extract_json_object(text)
    if data is not None and key in data:
        value = data[key]
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "1", "да")
    lowered = (text or "").strip().lower()
    if lowered.startswith("yes") or "true" in lowered[:20]:
        return True
    if lowered.startswith("no") or "false" in lowered[:20]:
        return False
    return None


# ---------------------------------------------------------------------------
# Output-format templates
#
# mlx enforces no JSON schema, and the 2B model will not fill the nested
# sdsbench output schema from the prose system prompt alone (it echoes the sheet
# back in markdown — see the K2 report). The battery therefore appends an
# explicit flat output template to the reused sdsbench prompt and maps the flat
# shape back onto the contract schema. This is the only prompt-side deviation
# from "reuse build_messages" and is documented in the K2 report.
# ---------------------------------------------------------------------------

_M1_FORMAT = '''Return ONLY one JSON object, filling this exact shape (replace the sample values, keep the keys):
{
  "product_name": {"state": "PRESENT", "value": "<text>", "derivation": "DIRECT", "rule": null, "page": 1, "quote": "<verbatim text>", "premise_pages": [], "premise_quotes": []},
  "supplier_name": {"state": "PRESENT", "value": "<text>", "derivation": "DIRECT", "rule": null, "page": 1, "quote": "<verbatim text>", "premise_pages": [], "premise_quotes": []},
  "substance_or_mixture": {"state": "PRESENT", "value": "MIXTURE", "derivation": "DIRECT", "rule": null, "page": 1, "quote": "<verbatim text>", "premise_pages": [], "premise_quotes": []},
  "product_cas_number": {"state": "NOT_APPLICABLE", "value": null, "derivation": "DERIVED", "rule": "identifier_undefined_for_form", "page": null, "quote": "", "premise_pages": [1], "premise_quotes": ["<verbatim form declaration>"]},
  "chemical_formula": {"state": "NOT_APPLICABLE", "value": null, "derivation": "DERIVED", "rule": "identifier_undefined_for_form", "page": null, "quote": "", "premise_pages": [1], "premise_quotes": ["<verbatim form declaration>"]},
  "molecular_weight": {"state": "NOT_APPLICABLE", "value": null, "derivation": "DERIVED", "rule": "identifier_undefined_for_form", "page": null, "quote": "", "premise_pages": [1], "premise_quotes": ["<verbatim form declaration>"]},
  "flash_point": {"state": "PRESENT", "value": "<text>", "derivation": "DIRECT", "rule": null, "page": 1, "quote": "<verbatim text>", "premise_pages": [], "premise_quotes": []},
  "ingredients": [{"name": "<text>", "cas_number": "<text or null>", "cas_state": "PRESENT", "concentration": "<text>", "page": 1, "quote": "<verbatim text>"}]
}
state is one of PRESENT, NOT_APPLICABLE, NO_DATA, NOT_STATED. A DIRECT claim fills page and quote with the cited page and the exact verbatim text. A DERIVED claim sets derivation "DERIVED", names rule ("identifier_undefined_for_form" or "composition_implies_form"), fills premise_pages and premise_quotes with the premises, and leaves page null and quote "". NOT_STATED leaves page null, quote "" and empty premise lists. Quote verbatim from the sheet. No markdown, no prose, no code fences.'''

_M2_FORMAT = '''Return ONLY one JSON object with exactly these keys:
{"state": "PRESENT|NOT_APPLICABLE|NO_DATA|NOT_STATED", "value": <string or null>, "derivation": "DIRECT|DERIVED", "rule": <"identifier_undefined_for_form"|"composition_implies_form"|null>, "page": <int or null>, "quote": "<exact verbatim text>", "premise_pages": [<int>], "premise_quotes": ["<exact verbatim text>"]}
A DIRECT claim fills page and quote. A DERIVED claim names rule and fills premise_pages/premise_quotes, with page null and quote "". NOT_STATED leaves page null, quote "" and empty lists. No markdown, no prose, no code fences.'''

_M2_INGREDIENTS_FORMAT = '''Return ONLY one JSON object:
{"ingredients_state": "PRESENT|NOT_APPLICABLE|NOT_STATED", "ingredients": [{"name": "<text>", "cas_number": "<text or null>", "cas_state": "PRESENT|NOT_APPLICABLE|NOT_STATED", "concentration": "<text>", "page": <int>, "quote": "<exact verbatim row text>"}]}
No markdown, no prose, no code fences.'''


# ---------------------------------------------------------------------------
# M1 — all fields, one pass (whole document)
# ---------------------------------------------------------------------------


def m1_all_fields(
    document: str,
    layer: str,
    backend: backends.Backend,
    max_tokens: int = 3000,
) -> tuple[DocumentPrediction, list[CallRecord], dict]:
    document_text = textlayer.load(document, layer)
    system, user = llm.build_messages(document, document_text, _LAYOUT)
    system = f"{system}\n\n{_M1_FORMAT}"
    text, record = _call(
        backend,
        "M1",
        document,
        layer,
        system,
        user,
        llm.LlmOutput.model_json_schema(),
        max_tokens,
        label="all-fields",
    )
    calls = [record]
    info: dict[str, Any] = {}
    if record.error:
        return DocumentPrediction(document=document, fields={}, error=record.error), calls, info
    output = parse_llm_output(text)
    if output is None:
        return (
            DocumentPrediction(
                document=document, fields={}, error="no structured output (M1)"
            ),
            calls,
            info,
        )
    prediction, violations = llm.to_document_prediction(
        document, output, document_text, _LAYOUT
    )
    counts: dict[str, int] = {}
    for violation in violations:
        counts[violation.code] = counts.get(violation.code, 0) + 1
    info["contract_violations"] = counts
    return prediction, calls, info


# ---------------------------------------------------------------------------
# M2 — one call per field (+ one ingredients call)
# ---------------------------------------------------------------------------

_M2_SYSTEM = """You extract ONE field from one safety data sheet (SDS) and cite verbatim evidence.

Field to extract: __NAME__ — __DESCRIPTION__

Input: the sheet's text layer, page by page, marked "=== PAGE n ===", in visual row order. It may contain OCR noise; quote it as it is.

States: PRESENT = the sheet states a usable value; NOT_APPLICABLE = the sheet says the property does not apply, or a derivation rule below rules it out; NO_DATA = the sheet says the value is not available / not determined / not specified, or leaves the slot empty with a dash; NOT_STATED = the sheet is silent. Only NOT_STATED carries no citation.

Citation: page number plus a quote copied exactly from that page's text: contiguous, same spelling, punctuation and case, no paraphrase, no ellipsis. It may run across a line break. Prefer the label together with the value ("Flash point: 12 C (53.6 F)"); when the label and the value are not adjacent in the text, quote the value alone.

Derived claims: a claim is DERIVED when it follows from the sheet through a rule rather than being stated:
- identifier_undefined_for_form: product_cas_number, chemical_formula and molecular_weight are NOT_APPLICABLE for a MIXTURE or an ARTICLE. Set derivation DERIVED, rule identifier_undefined_for_form, premises = the quote(s) that establish the product form (the form declaration), evidence null.
- composition_implies_form: only for substance_or_mixture, when the sheet never says the form but the composition table establishes it; premises = the composition rows.
For a SUBSTANCE the identifier fields are PRESENT when stated and NOT_STATED when not.

Return only JSON:
{"state": "PRESENT|NOT_APPLICABLE|NO_DATA|NOT_STATED", "value": <string or null>, "derivation": "DIRECT|DERIVED", "rule": <"identifier_undefined_for_form"|"composition_implies_form"|null>, "evidence": {"page": <int>, "quote": <string>} or null, "premises": [{"page": <int>, "quote": <string>}]}"""

_M2_INGREDIENTS_SYSTEM = """You extract the Section 3 composition table from one safety data sheet (SDS).

Input: the sheet's text layer, page by page, marked "=== PAGE n ===", in visual row order.

ingredients_state: PRESENT when the sheet declares components, NOT_APPLICABLE when it says no component needs disclosure, NOT_STATED when there is no composition information.

For every row of the composition table return one item: name, CAS number (or null), cas_state (PRESENT when a CAS is printed, else NOT_APPLICABLE or NOT_STATED), concentration as printed, and a citation {"page": <int>, "quote": <exact verbatim row text>}.

Return only JSON:
{"ingredients_state": "PRESENT|NOT_APPLICABLE|NOT_STATED", "ingredients": [{"name": <string>, "cas_number": <string or null>, "cas_state": "PRESENT|NOT_APPLICABLE|NOT_STATED", "concentration": <string or null>, "citation": {"page": <int>, "quote": <string>}}]}"""


def m2_individual_field(
    document: str,
    layer: str,
    backend: backends.Backend,
    max_tokens: int = 600,
    ingredients_max_tokens: int = 1200,
) -> tuple[DocumentPrediction, list[CallRecord], dict]:
    document_text = textlayer.load(document, layer)
    page_text = llm.page_texts(document_text, _LAYOUT)
    user = f"Document: {document}\n\n{page_text}"
    calls: list[CallRecord] = []
    fields: dict[str, FieldPrediction] = {}
    notes: list[str] = []

    for name in M2_FIELDS:
        spec = FIELD_SPECS[name]
        system = _M2_SYSTEM.replace("__NAME__", spec.name).replace(
            "__DESCRIPTION__", spec.description
        )
        system = f"{system}\n\n{_M2_FORMAT}"
        text, record = _call(
            backend,
            "M2",
            document,
            layer,
            system,
            user,
            llm.LlmField.model_json_schema(),
            max_tokens,
            label=name,
        )
        calls.append(record)
        raw = None if record.error else parse_llm_field(text)
        if raw is None:
            fields[name] = FieldPrediction(state=FieldState.NOT_STATED)
            notes.append(f"{name}: no structured output")
            continue
        prediction, note, _ = llm._field_prediction(name, raw, document_text, _LAYOUT)
        fields[name] = prediction
        if note:
            notes.append(f"{name}: {note}")

    text, record = _call(
        backend,
        "M2",
        document,
        layer,
        f"{_M2_INGREDIENTS_SYSTEM}\n\n{_M2_INGREDIENTS_FORMAT}",
        user,
        json.loads(json.dumps(_m2_ingredients_schema())),
        ingredients_max_tokens,
        label="ingredients",
    )
    calls.append(record)
    parsed = None if record.error else parse_llm_ingredients(text)
    if parsed is None:
        ingredients = IngredientsPrediction(state=FieldState.NOT_STATED, items=[])
        notes.append("ingredients: no structured output")
    else:
        items = [
            IngredientPrediction(
                name=item["name"],
                cas_number=item["cas_number"],
                cas_state=FieldState(item["cas_state"]),
                concentration=item["concentration"],
                evidence=llm.resolve_citation(
                    document_text,
                    llm.LlmCitation.model_validate(item["citation"])
                    if item["citation"]
                    else None,
                    _LAYOUT,
                ),
            )
            for item in parsed["ingredients"]
        ]
        ingredients = IngredientsPrediction(
            state=FieldState(parsed["ingredients_state"]), items=items
        )

    prediction = DocumentPrediction(
        document=document,
        fields=fields,
        ingredients=ingredients,
        error="; ".join(notes) or None,
    )
    return prediction, calls, {"contract_violations": {}}


def _m2_ingredients_schema() -> dict:
    from pydantic import BaseModel

    class _IngredientsOut(BaseModel):
        ingredients_state: str
        ingredients: list[dict]

    return _IngredientsOut.model_json_schema()


# ---------------------------------------------------------------------------
# M3 — contextual citation verification (depends on M1)
# ---------------------------------------------------------------------------

_M3_SYSTEM = """You verify one citation from a safety data sheet (SDS).

The extraction system reported for the field "__FIELD__":
- state: __STATE__
- value: __VALUE__
- it cites page __PAGE__ with this verbatim quote: __QUOTE__

Below are the cited page and its immediate neighbours, page by page in visual row order. The quote must occur verbatim (same spelling, punctuation and case) on the cited page. If it does, confirm it. If it does not, locate the exact verbatim string in this text that states or establishes the claim and report the correct page number and the exact string.

Return only JSON: {"page": <int>, "quote": "<exact verbatim text from the shown pages>", "found": true|false}. No markdown, no prose, no code fences."""


def _context_pages(document_text: textlayer.DocumentText, page: int, window: int = 1) -> str:
    pieces = []
    for number in range(max(1, page - window), page + window + 1):
        item = document_text.page(number)
        if item is None:
            continue
        pieces.append(f"=== PAGE {item.page_number} ===\n{item.row_text}")
    return "\n\n".join(pieces) if pieces else "(page not found)"


def _verify_span(
    backend: backends.Backend,
    document: str,
    layer: str,
    document_text: textlayer.DocumentText,
    field_name: str,
    state: str,
    value: str | None,
    span: EvidenceSpan,
) -> tuple[EvidenceSpan | None, CallRecord]:
    system = (
        _M3_SYSTEM.replace("__FIELD__", field_name)
        .replace("__STATE__", state)
        .replace("__VALUE__", value if value is not None else "null")
        .replace("__PAGE__", str(span.page))
        .replace("__QUOTE__", json.dumps(span.text, ensure_ascii=False))
    )
    user = _context_pages(document_text, span.page)
    text, record = _call(
        backend,
        "M3",
        document,
        layer,
        system,
        user,
        json_schema=None,
        max_tokens=300,
        label=field_name,
    )
    if record.error:
        return None, record
    data = extract_json_object(text)
    corrected_page = span.page
    corrected_quote = span.text
    if data is not None:
        try:
            corrected_page = int(data.get("page", span.page))
        except (TypeError, ValueError):
            corrected_page = span.page
        if isinstance(data.get("quote"), str) and data["quote"].strip():
            corrected_quote = data["quote"]
    candidate = llm.resolve_citation(
        document_text,
        llm.LlmCitation(page=max(1, corrected_page), quote=corrected_quote),
        _LAYOUT,
    )
    if candidate is not None and candidate.bbox is not None:
        return candidate, record
    # Correction did not resolve verbatim: keep the original if it still does.
    original = llm.resolve_citation(
        document_text, llm.LlmCitation(page=span.page, quote=span.text), _LAYOUT
    )
    if original is not None and original.bbox is not None:
        return original, record
    return None, record


def m3_contextual_verification(
    document: str,
    layer: str,
    backend: backends.Backend,
    base: DocumentPrediction,
    max_tokens: int = 300,
) -> tuple[DocumentPrediction, list[CallRecord], dict]:
    document_text = textlayer.load(document, layer)
    calls: list[CallRecord] = []
    fields: dict[str, FieldPrediction] = {}
    degraded = 0

    for name in PRODUCT_FIELD_NAMES:
        prediction = base.fields.get(name)
        if prediction is None or prediction.state is FieldState.NOT_STATED:
            fields[name] = prediction or FieldPrediction(state=FieldState.NOT_STATED)
            continue
        cited = prediction.cited_spans
        if not cited:
            fields[name] = prediction
            continue
        verified: list[EvidenceSpan] = []
        ok = True
        for span in cited:
            new_span, record = _verify_span(
                backend,
                document,
                layer,
                document_text,
                name,
                prediction.state.value,
                prediction.value,
                span,
            )
            calls.append(record)
            if new_span is None:
                ok = False
                break
            verified.append(new_span)
        if not ok:
            fields[name] = FieldPrediction(
                state=FieldState.NOT_STATED, rationale="M3: citation unverifiable"
            )
            degraded += 1
            continue
        fields[name] = _rebuild_claim(prediction, verified)

    result = DocumentPrediction(
        document=document, fields=fields, ingredients=base.ingredients
    )
    return result, calls, {"degraded_claims": degraded}


def _rebuild_claim(prediction: FieldPrediction, spans: list[EvidenceSpan]) -> FieldPrediction:
    """Same claim, corrected localization."""
    if prediction.derivation == "DERIVED":
        return FieldPrediction(
            state=prediction.state,
            value=prediction.value,
            derivation="DERIVED",
            rule=prediction.rule,
            premises=spans,
            confidence=prediction.confidence,
        )
    return FieldPrediction(
        state=prediction.state,
        value=prediction.value,
        evidence=spans[0] if spans else None,
        confidence=prediction.confidence,
        rationale=prediction.rationale,
    )


# ---------------------------------------------------------------------------
# M5 — basic LLM verifier (depends on M1)
# ---------------------------------------------------------------------------

_M5_SYSTEM = """You check whether the cited evidence supports one claim from a safety data sheet (SDS).

Claim for the field "__FIELD__":
- state: __STATE__
- value: __VALUE__

Cited evidence the system offers as support (page, verbatim quote):
__EVIDENCE__

Does this evidence actually state or license exactly this claim? Answer Yes only if the cited text itself supports the claimed state and value; answer No otherwise.

Answer with exactly one word: Yes or No. No markdown, no prose, no JSON, no code fences."""


def m5_basic_verifier(
    document: str,
    layer: str,
    backend: backends.Backend,
    base: DocumentPrediction,
    max_tokens: int = 200,
) -> tuple[DocumentPrediction, list[CallRecord], dict]:
    calls: list[CallRecord] = []
    fields: dict[str, FieldPrediction] = {}
    yes = 0
    no = 0

    for name in PRODUCT_FIELD_NAMES:
        prediction = base.fields.get(name)
        if prediction is None or prediction.state is FieldState.NOT_STATED:
            fields[name] = prediction or FieldPrediction(state=FieldState.NOT_STATED)
            continue
        cited = prediction.cited_spans
        if not cited:
            # A claim without evidence cannot be supported: keep it, unverified.
            fields[name] = prediction
            continue
        evidence_block = "\n".join(
            f'- page {span.page}: {json.dumps(span.text, ensure_ascii=False)}'
            for span in cited
        )
        system = (
            _M5_SYSTEM.replace("__FIELD__", name)
            .replace("__STATE__", prediction.state.value)
            .replace("__VALUE__", prediction.value if prediction.value is not None else "null")
            .replace("__EVIDENCE__", evidence_block)
        )
        text, record = _call(
            backend,
            "M5",
            document,
            layer,
            system,
            "Answer with one word: Yes or No.",
            json_schema=None,
            max_tokens=max_tokens,
            label=name,
        )
        calls.append(record)
        verdict = None if record.error else _parse_bool_verdict(text, "supported")
        if verdict is True:
            yes += 1
            fields[name] = prediction
        else:
            no += 1
            fields[name] = FieldPrediction(
                state=FieldState.NOT_STATED, rationale="M5: unsupported claim"
            )

    result = DocumentPrediction(
        document=document, fields=fields, ingredients=base.ingredients
    )
    return result, calls, {"yes": yes, "no": no}


# ---------------------------------------------------------------------------
# M4 — rules-v4 (inherited, re-scored on gold v1.3)
# ---------------------------------------------------------------------------


def m4_rules_v4(
    document: str,
    layer: str,
) -> tuple[DocumentPrediction, list[CallRecord], dict]:
    prediction = rules.extract_document(document, layer=layer, layout=rules.LAYOUT_ROWS)
    record = CallRecord(
        method="M4",
        document=document,
        layer=layer,
        backend="rules",
        n_calls=0,
        label=rules.EXTRACTOR_VERSION,
    )
    return prediction, [record], {"extractor": rules.EXTRACTOR_VERSION}


METHODS = {
    "M1": "all-fields-one-pass (whole document)",
    "M2": "individual-field (one call per field + ingredients)",
    "M3": "contextual citation verification (depends on M1)",
    "M4": "rules-v4 (inherited, re-scored on gold v1.3)",
    "M5": "basic LLM verifier (depends on M1)",
}

LLM_METHODS = ("M1", "M2", "M3", "M5")
DEPENDS_ON_M1 = ("M3", "M5")