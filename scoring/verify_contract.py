"""Consumer-driven contract verification (a lightweight, dependency-free Pact).

It replays every interaction the consumer declared (consumer/contracts/*.json)
against the provider and checks the provider still delivers what the consumer
needs: the right status, and every declared field present with the declared
type. Unlike the provider's own tests, this encodes the CONSUMER's needs -- so it
catches a break the provider never thought to test, and it is blind to changes in
fields no consumer depends on. Both of those are the point.

    python scoring/verify_contract.py     (verifies against the clean provider)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "consumer" / "contracts"


def _type_ok(value, tname: str) -> bool:
    if value is None:
        return False
    if tname == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if tname == "bool":
        return isinstance(value, bool)
    if tname == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if tname == "str":
        return isinstance(value, str)
    return True


def _check_fields(elem, fields, desc, violations, rules=()) -> None:
    if elem is None:
        violations.append(f"{desc}: null where an object was expected")
        return
    for f, t in fields.items():
        if f not in elem:
            violations.append(f"{desc}: missing field '{f}'")
        elif not _type_ok(elem[f], t):
            violations.append(f"{desc}: field '{f}' is not {t}")
    # value matchers (a real contract asserts more than types: a rating is 0-5,
    # not merely 'a float' -- which is what catches a silent semantic rescale)
    for rule in rules:
        f = rule["field"]
        v = elem.get(f)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if "min" in rule and v < rule["min"]:
                violations.append(f"{desc}: field '{f}'={v} below min {rule['min']}")
            if "max" in rule and v > rule["max"]:
                violations.append(f"{desc}: field '{f}'={v} above max {rule['max']}")


def verify(client, contract: dict) -> list[str]:
    """Return a list of (deduplicated) contract violations; empty means satisfied."""
    violations: list[str] = []
    for it in contract["interactions"]:
        desc = it["description"]
        resp = it["response"]
        if it["kind"] == "rest":
            req = it["request"]
            r = client.get(req["path"]) if req["method"] == "GET" else \
                client.request(req["method"], req["path"])
            if r.status_code != resp["status"]:
                violations.append(f"{desc}: status {r.status_code} != {resp['status']}")
                continue
            body = r.json()
            elems = body if resp.get("shape") == "array" else [body]
            for el in elems:
                _check_fields(el, resp["fields"], desc, violations, resp.get("value_rules", ()))
        else:  # graphql
            env = client.post("/graphql", json={"query": it["request"]["query"]}).json()
            if env.get("errors"):
                violations.append(f"{desc}: graphql errors {env['errors']}")
                continue
            data = (env.get("data") or {}).get(resp["data_path"])
            elems = data if resp.get("shape") == "array" else [data]
            if elems is None:
                violations.append(f"{desc}: null result")
                continue
            for el in elems:
                _check_fields(el, resp["fields"], desc, violations, resp.get("value_rules", ()))
    # dedup while preserving order (a renamed field hits every array element)
    return list(dict.fromkeys(violations))


def load_contracts() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CONTRACTS.glob("*.json"))]


def verify_all(client) -> list[str]:
    out = []
    for c in load_contracts():
        out += verify(client, c)
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "provider"))
    from fastapi.testclient import TestClient
    from app.main import create_app

    v = verify_all(TestClient(create_app()))
    if v:
        print("CONTRACT VIOLATIONS:")
        for x in v:
            print("  -", x)
        sys.exit(1)
    print("contract satisfied: the provider delivers everything the consumer needs")
