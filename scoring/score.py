"""Scoring harness -- measures which API-testing mechanism catches which change.

For the clean provider and for every change in the catalog, it stages a throwaway
copy of the project, applies the change's edits, and runs three mechanisms:

    provider_tests  -- the provider's own pytest suite
    contract        -- consumer-driven contract verification (probe.py)
    schema_diff     -- a structural schema diff vs the clean baseline (probe.py)

recording whether each flagged the change. Breaking changes should be caught by
at least one mechanism; non-breaking (additive) ones by none (else a false
positive). The catch matrix is deterministic, so reports/*.json are reproducible.

    python scoring/score.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import CATALOG  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
COPY = ["provider", "testing", "consumer", "scoring", "pytest.ini"]
PY = sys.executable


def _stage(dst: Path) -> None:
    for item in COPY:
        src = ROOT / item
        if src.is_dir():
            shutil.copytree(src, dst / item)
        else:
            shutil.copy2(src, dst / item)


def _apply(dst: Path, change) -> None:
    for rel, find, replace in change.edits:
        target = dst / rel
        text = target.read_text(encoding="utf-8")
        n = text.count(find)
        if n != 1:
            raise RuntimeError(f"{change.id}: marker {find!r} occurs {n}x in {rel} (need 1)")
        target.write_text(text.replace(find, replace), encoding="utf-8")


def _pytest_caught(cwd: Path) -> bool:
    p = subprocess.run([PY, "-m", "pytest", "testing/provider_tests", "-x", "--no-header", "-q"],
                       cwd=cwd, capture_output=True, text=True)
    if p.returncode not in (0, 1):
        raise RuntimeError(f"pytest exited {p.returncode}:\n{p.stdout[-1500:]}")
    return p.returncode == 1


def _probe(cwd: Path, *args: str) -> bool:
    p = subprocess.run([PY, "scoring/probe.py", *args], cwd=cwd, capture_output=True, text=True)
    if p.returncode not in (0, 1):
        raise RuntimeError(f"probe {args} exited {p.returncode}:\n{p.stdout}\n{p.stderr[-1500:]}")
    return p.returncode == 1


def _mechanisms(cwd: Path, baseline: str) -> dict:
    return {
        "provider_tests": _pytest_caught(cwd),
        "contract": _probe(cwd, "contract"),
        "schema_diff": _probe(cwd, "schemadiff", baseline),
    }


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    baseline = str((REPORTS / "_baseline.json").resolve())

    print("clean baseline ...")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _stage(d)
        # snapshot the clean schema descriptor
        subprocess.run([PY, "scoring/probe.py", "descriptor", baseline], cwd=d, check=True)
        clean = _mechanisms(d, baseline)
        if any(clean.values()):
            raise RuntimeError(f"clean provider is flagged by {clean} -- fix before scoring")
        print("  clean: all mechanisms green")

    matrix = {}
    for ch in CATALOG:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            _stage(d)
            _apply(d, ch)
            caught = _mechanisms(d, baseline)
        matrix[ch.id] = {"klass": ch.klass, "breaking": ch.breaking,
                         "desc": ch.desc, "caught": caught}
        marks = " ".join(f"{k}={'Y' if v else '.'}" for k, v in caught.items())
        tag = ""
        if ch.breaking and not any(caught.values()):
            tag = "MISSED (breaking)"
        if (not ch.breaking) and any(caught.values()):
            tag = "FALSE POSITIVE"
        print(f"  {ch.id} {ch.klass:18s} {'BREAK' if ch.breaking else 'ok   '} {marks}  {tag}")

    mechs = ["provider_tests", "contract", "schema_diff"]
    breaking = [c for c, b in matrix.items() if b["breaking"]]
    additive = [c for c, b in matrix.items() if not b["breaking"]]

    def caught_by(cid, mech):
        return matrix[cid]["caught"][mech]

    per_mech = {mch: sum(1 for c in breaking if caught_by(c, mch)) for mch in mechs}
    caught_any = [c for c in breaking if any(matrix[c]["caught"].values())]
    missed = [c for c in breaking if not any(matrix[c]["caught"].values())]
    false_pos = [c for c in additive if any(matrix[c]["caught"].values())]

    # who catches what the others miss (the value of each mechanism)
    contract_only_vs_provider = [c for c in breaking
                                 if caught_by(c, "contract") and not caught_by(c, "provider_tests")]
    schema_catches_contract_blind = [c for c in breaking
                                     if caught_by(c, "schema_diff") and not caught_by(c, "contract")]
    contract_catches_schema_blind = [c for c in breaking
                                     if caught_by(c, "contract") and not caught_by(c, "schema_diff")]

    classes = sorted({b["klass"] for b in matrix.values()})
    per_class = {}
    for k in classes:
        ids = [c for c in matrix if matrix[c]["klass"] == k]
        per_class[k] = {"changes": len(ids),
                        **{mch: sum(1 for c in ids if caught_by(c, mch)) for mch in mechs}}

    summary = {
        "total_changes": len(CATALOG),
        "breaking_changes": len(breaking),
        "additive_changes": len(additive),
        "mechanisms": mechs,
        "caught_per_mechanism_of_breaking": per_mech,
        "breaking_caught_by_any": len(caught_any),
        "breaking_missed_by_all": len(missed),
        "missed_breaking": [{"id": c, "klass": matrix[c]["klass"], "desc": matrix[c]["desc"]}
                            for c in missed],
        "false_positives": [{"id": c, "klass": matrix[c]["klass"]} for c in false_pos],
        "contract_catches_provider_tests_miss": contract_only_vs_provider,
        "schema_diff_catches_contract_blind": schema_catches_contract_blind,
        "contract_catches_schema_diff_blind": contract_catches_schema_blind,
        "per_class": per_class,
        "headline": (
            f"Of {len(breaking)} breaking changes, provider tests catch "
            f"{per_mech['provider_tests']}, consumer contracts catch {per_mech['contract']}, "
            f"schema diff catches {per_mech['schema_diff']}; {len(missed)} slip past all "
            f"three. Contracts catch {len(contract_only_vs_provider)} that the provider's "
            f"own tests miss. No mechanism flagged any of the {len(additive)} additive "
            f"changes ({len(false_pos)} false positives)."),
    }

    (REPORTS / "catch_matrix.json").write_text(
        json.dumps({"changes": matrix}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (REPORTS / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("\n" + summary["headline"])
    print("wrote reports/catch_matrix.json, summary.json")


if __name__ == "__main__":
    main()
