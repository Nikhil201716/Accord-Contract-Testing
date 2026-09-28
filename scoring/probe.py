"""Run one measurement mechanism against the provider in the CURRENT directory.

The scoring harness stages a (possibly patched) copy of the project into a temp
dir and runs this script there, so `create_app` is imported from the patched
copy. Modes:

    probe.py contract              -> exit 1 if the consumer contract is violated
    probe.py descriptor <out.json> -> write the provider's schema descriptor
    probe.py schemadiff <base.json>-> exit 1 if there is a breaking schema diff

Exit 0 means "this mechanism did not flag the change"; exit 1 means it did.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "provider"))
sys.path.insert(0, str(ROOT / "scoring"))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import create_app            # noqa: E402


def main() -> int:
    mode = sys.argv[1]

    if mode == "contract":
        import verify_contract
        v = verify_contract.verify_all(TestClient(create_app()))
        print(json.dumps({"violations": v}))
        return 1 if v else 0

    if mode == "descriptor":
        import schema_diff
        app = create_app()
        d = schema_diff.descriptor(TestClient(app), app.state.schema)
        Path(sys.argv[2]).write_text(json.dumps(d), encoding="utf-8")
        return 0

    if mode == "schemadiff":
        import schema_diff
        base = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        app = create_app()
        cur = schema_diff.descriptor(TestClient(app), app.state.schema)
        breaks = schema_diff.diff(base, cur)
        print(json.dumps({"breaks": breaks}))
        return 1 if breaks else 0

    print(f"unknown mode {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
