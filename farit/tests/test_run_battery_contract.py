"""The runner's citation-contract gate (guards the 2026-10-26 hub failure mode)."""
from sdsbench.ontology import FieldState
from sdsbench.schema import DocumentPrediction, EvidenceSpan, FieldPrediction

import run_battery


def _doc(**fields):
    return DocumentPrediction(document="sds_01.pdf", fields=fields)


def test_zero_when_no_citation_anywhere():
    preds = {
        "sds_01.pdf": _doc(
            product_name=FieldPrediction(state=FieldState.PRESENT, value="X"),
            supplier_name=FieldPrediction(state=FieldState.PRESENT, value="Y"),
        )
    }
    assert run_battery.evidence_bearing_count(preds) == 0


def test_counts_evidence_and_premises():
    span = EvidenceSpan(page=1, text="X")
    preds = {
        "sds_01.pdf": _doc(
            product_name=FieldPrediction(state=FieldState.PRESENT, value="X", evidence=span),
            supplier_name=FieldPrediction(state=FieldState.PRESENT, value="Y"),
            product_cas_number=FieldPrediction(
                state=FieldState.NOT_APPLICABLE, derivation="DERIVED",
                rule="identifier_undefined_for_form", premises=[span],
            ),
        )
    }
    assert run_battery.evidence_bearing_count(preds) == 2