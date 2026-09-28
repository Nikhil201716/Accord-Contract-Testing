"""Schema diff -- a structural API linter.

It derives a descriptor of the provider (REST paths + the shape of a book +
probe status codes; the GraphQL type map) and compares it against a baseline
descriptor taken from the known-good provider. It reports *breaking* differences
only -- a removed path, a removed or retyped field, a changed status -- and
ignores additive ones (a new field is not a break). No consumer is needed: this
is what an OpenAPI/GraphQL diff tool does in CI. Its blind spot is semantics: a
field whose meaning changed but whose name and type did not looks identical.
"""

from __future__ import annotations

from graphql import build_schema as gql_build
from strawberry.printer import print_schema


def _typename(v) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "dict"
    return "null"


def _graphql_types(schema) -> dict:
    sdl = print_schema(schema)
    gs = gql_build(sdl)
    out = {}
    for name, t in gs.type_map.items():
        if name.startswith("__") or not hasattr(t, "fields"):
            continue
        out[name] = {fname: str(f.type) for fname, f in t.fields.items()}
    return out


def descriptor(client, schema) -> dict:
    """A comparable snapshot of the provider's public surface."""
    app = client.app
    paths = sorted(app.openapi().get("paths", {}).keys())

    book = client.get("/api/books/1")
    book_fields = {k: _typename(v) for k, v in book.json().items()} \
        if book.status_code == 200 else {}

    probes = {
        "GET /api/books/1": client.get("/api/books/1").status_code,
        "GET /api/books/999": client.get("/api/books/999").status_code,
        "POST /api/books": client.post("/api/books", json={
            "title": "x", "author": "y", "isbn": "978-0000000000",
            "year": 2000, "tags": []}).status_code,
    }
    return {
        "rest": {"paths": paths, "book_fields": book_fields, "probes": probes},
        "graphql": _graphql_types(schema),
    }


def diff(base: dict, cur: dict) -> list[str]:
    """Breaking changes from `base` to `cur`. Additive changes are not breaking."""
    breaks: list[str] = []

    # REST paths removed
    for p in base["rest"]["paths"]:
        if p not in cur["rest"]["paths"]:
            breaks.append(f"REST path removed: {p}")

    # REST book fields removed or retyped
    bf, cf = base["rest"]["book_fields"], cur["rest"]["book_fields"]
    for f, t in bf.items():
        if f not in cf:
            breaks.append(f"REST field removed: book.{f}")
        elif cf[f] != t:
            breaks.append(f"REST field retyped: book.{f} {t} -> {cf[f]}")

    # REST probe status codes changed
    for probe, code in base["rest"]["probes"].items():
        if cur["rest"]["probes"].get(probe) != code:
            breaks.append(f"REST status changed: {probe} {code} -> {cur['rest']['probes'].get(probe)}")

    # GraphQL fields removed or retyped
    for tname, fields in base["graphql"].items():
        cur_fields = cur["graphql"].get(tname)
        if cur_fields is None:
            breaks.append(f"GraphQL type removed: {tname}")
            continue
        for f, t in fields.items():
            if f not in cur_fields:
                breaks.append(f"GraphQL field removed: {tname}.{f}")
            elif cur_fields[f] != t:
                breaks.append(f"GraphQL field retyped: {tname}.{f} {t} -> {cur_fields[f]}")

    return breaks
