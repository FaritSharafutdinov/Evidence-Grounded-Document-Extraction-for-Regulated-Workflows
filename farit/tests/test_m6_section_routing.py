"""M6 section routing — the hand-written field→section map must cover every field
and fall back to the whole document when nothing matches."""
from types import SimpleNamespace

import methods


def _dt(texts):
    return SimpleNamespace(
        pages=[SimpleNamespace(page_number=i + 1, row_text=t) for i, t in enumerate(texts)]
    )


def test_section_cues_cover_every_field():
    for name in methods.M2_FIELDS:
        assert methods._SECTION_CUES.get(name), f"no section cues mapped for {name}"


def test_routed_pages_selects_matching_pages_only():
    doc = _dt(["SECTION 1 Identification", "SECTION 9 Physical properties", "noise"])
    got = methods.routed_pages(doc, (r"SECTION\s*9\b",))
    assert [p.page_number for p in got] == [2]


def test_routed_pages_falls_back_to_all_when_unmatched():
    doc = _dt(["aaa", "bbb"])
    got = methods.routed_pages(doc, (r"SECTION\s*99\b",))
    assert [p.page_number for p in got] == [1, 2]


def test_flash_point_routes_to_section_9():
    assert any("9" in c for c in methods._SECTION_CUES["flash_point"])