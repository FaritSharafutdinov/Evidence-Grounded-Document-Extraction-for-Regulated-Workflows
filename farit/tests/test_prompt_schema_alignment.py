"""The prompt output-templates must match the JSON schema the backend enforces.

Regression for the 2026-10-26 hub incident: M1's prompt used a *flat* template
(`page`/`quote`/`premise_pages`), while the request sent `LlmOutput.model_json_schema()`
to the server. On MLX (no schema enforcement) the flat template worked; on vLLM
guided decoding enforced the schema, the two disagreed, and the model returned
values with `evidence: null` — M1/M3/M5 collapsed to ~0% joint. These tests fail
loudly if any template drifts away from the schema shape again.
"""
import json

import pytest

from sdsbench.extractors import llm

import methods


def _example_json(text: str) -> dict:
    """Extract the first balanced {...} block from a template string."""
    start = text.index("{")
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise AssertionError("no balanced JSON example in template")


PRODUCT_FIELDS = (
    "product_name",
    "supplier_name",
    "substance_or_mixture",
    "product_cas_number",
    "chemical_formula",
    "molecular_weight",
    "flash_point",
)


def test_m1_example_validates_against_schema():
    example = _example_json(methods._M1_FORMAT)
    out = llm.LlmOutput.model_validate(example)  # raises if the shape drifts
    assert example.get("ingredients_state"), "M1 template must include ingredients_state"
    assert example["ingredients"] and example["ingredients"][0].get("citation"), (
        "M1 ingredient example must carry a nested citation"
    )
    for name in PRODUCT_FIELDS:
        field = getattr(out, name)
        if field.derivation == "DIRECT":
            assert field.evidence is not None, f"{name}: DIRECT example lost its evidence"
        else:
            assert field.premises, f"{name}: DERIVED example has no premises"


def test_m1_example_uses_nested_evidence_not_flat():
    example = _example_json(methods._M1_FORMAT)
    field = example["product_name"]
    assert "evidence" in field and "premises" in field
    for flat_key in ("page", "quote", "premise_pages", "premise_quotes"):
        assert flat_key not in field, (
            f"M1 template drifted back to the flat '{flat_key}' shape — this breaks "
            "vLLM guided decoding (evidence silently lost). Keep the nested "
            "evidence/premises shape that matches LlmOutput."
        )


def test_m2_templates_use_nested_citation_shape():
    field_example = _example_json(methods._M2_FORMAT)
    field = llm.LlmField.model_validate(field_example)  # raises if the shape drifts
    assert field.evidence is not None, "M2 DIRECT example lost its evidence"
    for flat_key in ("page", "quote", "premise_pages", "premise_quotes"):
        assert flat_key not in field_example, f"M2 template drifted back to flat '{flat_key}'"

    ing = _example_json(methods._M2_INGREDIENTS_FORMAT)
    assert ing["ingredients"] and ing["ingredients"][0]["citation"]["page"] == 1