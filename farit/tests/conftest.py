"""Make the farit inspection code importable from the tests.

`tests/` at the repo root is Maria's read-only infrastructure; the project's own
regression tests live here under `farit/tests/` and are run with
`pytest farit/tests -q`.
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "farit" / "src" / "extraction"), str(_ROOT / "farit" / "src" / "retrieval")):
    if _p not in sys.path:
        sys.path.insert(0, _p)