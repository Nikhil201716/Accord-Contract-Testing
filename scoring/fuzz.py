"""Property-based API fuzzing (Hypothesis).

It throws a wide space of malformed payloads at the create endpoint and asserts
one property: the server never answers with a 5xx. A well-built API rejects bad
input with 422, never crashes. This is the negative-testing layer, and finding
*nothing* is the point -- it is cheap evidence that the validation layer holds,
and a tripwire for the day it is weakened.

    python scoring/fuzz.py     (writes reports/fuzz.json)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "provider"))

from fastapi.testclient import TestClient           # noqa: E402
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st             # noqa: E402

from app.main import create_app                     # noqa: E402

MAX_EXAMPLES = 300
client = TestClient(create_app())

# deliberately mis-typed and hostile values for every field. Values are kept
# JSON- and UTF-8-serializable (no NaN/inf, no lone surrogates), because those
# cannot be sent over HTTP at all -- the target is malformed-but-sendable input.
_safe_text = st.text(st.characters(codec="utf-8"))
_value = st.one_of(
    st.none(), st.booleans(), st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    _safe_text, st.lists(_safe_text),
    st.text(alphabet="<>\"'{}$;()%&/\\"),      # injection-flavoured strings
)
_payload = st.fixed_dictionaries({}, optional={
    "title": _value, "author": _value, "isbn": _value, "year": _value, "tags": _value,
})

_found: list[str] = []


@settings(max_examples=MAX_EXAMPLES, derandomize=True, deadline=None,
          suppress_health_check=list(HealthCheck))
@given(p=_payload)
def _prop_no_5xx(p):
    r = client.post("/api/books", json=p)
    if r.status_code >= 500:
        _found.append(f"HTTP {r.status_code} on {json.dumps(p)[:160]}")
    assert r.status_code < 500


def main() -> None:
    (ROOT / "reports").mkdir(exist_ok=True)
    crashed = False
    try:
        _prop_no_5xx()
    except AssertionError:
        crashed = True

    report = {
        "endpoint": "POST /api/books",
        "max_examples": MAX_EXAMPLES,
        "generator": "malformed values for every field (null, wrong type, hostile strings)",
        "unhandled_5xx_found": bool(_found),
        "examples": _found[:5],
        "verdict": ("FOUND an unhandled 5xx -- the validation layer has a hole"
                    if _found else
                    "no unhandled 5xx: Pydantic validation rejects bad input with 4xx, "
                    "never a crash"),
    }
    (ROOT / "reports" / "fuzz.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if crashed:
        sys.exit(1)


if __name__ == "__main__":
    main()
