"""The change catalog: realistic API changes a provider team might ship, each
expressed as one or more exact source edits.

Each change is tagged with a class and whether it is *breaking* for a consumer.
Breaking changes should be caught by at least one mechanism; non-breaking
(additive) changes should be caught by NONE -- a mechanism that flags them is
raising a false positive, which is measured too. Every `find` must occur exactly
once in its file or the harness refuses to run.

The three mechanisms scored against each change are: the provider's own tests,
consumer-driven contract verification, and a structural schema diff.
"""

from __future__ import annotations

from dataclasses import dataclass

RE = "provider/app/rest.py"
MO = "provider/app/models.py"
GQ = "provider/app/graphql_api.py"


@dataclass(frozen=True)
class Change:
    id: str
    klass: str
    breaking: bool
    edits: tuple[tuple[str, str, str], ...]     # (file, find, replace)
    desc: str


CATALOG: list[Change] = [
    # ---- field rename (breaking) -----------------------------------------
    Change("C01", "rename", True, (
        (MO, "cover_url: str", "image: str"),
        (RE, '"cover_url": b.cover_url,', '"image": b.cover_url,'),
    ), "REST: rename cover_url -> image (a field the consumer renders)."),
    Change("C02", "rename", True, (
        (GQ, "cover_url: str", "image: str"),
        (GQ, "cover_url=b.cover_url,", "image=b.cover_url,"),
    ), "GraphQL: rename coverUrl -> image."),

    # ---- type change (breaking) ------------------------------------------
    Change("C03", "type-change", True, (
        (MO, "available: bool", "available: str"),
        (RE, '"available": b.available,', '"available": str(b.available).lower(),'),
    ), "REST: available becomes a string ('true') instead of a bool."),
    Change("C04", "type-change", True, (
        (MO, "rating: float", "rating: str"),
        (RE, '"rating": b.rating,', '"rating": str(b.rating),'),
    ), "REST: rating becomes a string instead of a float."),
    Change("C05", "type-change", True, (
        (GQ, "rating: float", "rating: str"),
        (GQ, "rating=b.rating)", "rating=str(b.rating))"),
    ), "GraphQL: rating becomes String instead of Float."),
    Change("C16", "type-change", True, (
        (GQ, "    year: int\n", "    year: str\n"),
        (GQ, "year=b.year,", "year=str(b.year),"),
    ), "GraphQL: year becomes String instead of Int."),

    # ---- field / endpoint removal (breaking) -----------------------------
    Change("C06", "remove-field", True, (
        (MO, "    year: int\n    tags: list[str]", "    tags: list[str]"),
    ), "REST: drop the year field from the book response."),
    Change("C07", "remove-endpoint", True, (
        (RE, '@r.get("/books/{book_id}", response_model=BookOut)',
             '@r.get("/books/_removed/{book_id}", response_model=BookOut)'),
    ), "REST: GET /api/books/{id} is moved/removed."),

    # ---- status code (breaking) ------------------------------------------
    Change("C08", "status-code", True, (
        (RE, "status_code=201", "status_code=200"),
    ), "REST: create returns 200 instead of 201 Created."),

    # ---- nullability widening (breaking for callers that assume non-null)-
    Change("C15", "nullability", True, (
        (GQ, "    title: str\n", "    title: str | None\n"),
    ), "GraphQL: title becomes nullable (String! -> String)."),

    # ---- additive, NON-breaking (false-positive probes) ------------------
    Change("C10", "add-field", False, (
        (MO, "    rating: float\n", '    rating: float\n    subtitle: str = ""\n'),
    ), "REST: add an optional subtitle field (additive, non-breaking)."),
    Change("C11", "add-field", False, (
        (GQ, "    rating: float\n", '    rating: float\n    subtitle: str = ""\n'),
    ), "GraphQL: add an optional subtitle field (additive, non-breaking)."),

    # ---- semantic changes: shape identical, meaning changed (breaking) ---
    Change("C12", "semantic", True, (
        (RE, '"rating": b.rating,', '"rating": b.rating * 20,'),
    ), "REST: rating silently rescaled 0-5 -> 0-100 (still a float)."),
    Change("C14", "semantic", True, (
        (RE, '"isbn": b.isbn,', '"isbn": b.isbn.replace("-", ""),'),
    ), "REST: isbn format changes (hyphens stripped; still a string)."),

    # ---- request-side validation relaxed (regression) --------------------
    Change("C09", "request-validation", True, (
        (MO, "year: int = Field(ge=1400, le=2100)", "year: int = Field(ge=1400, le=3000)"),
    ), "REST: create accepts implausible years (validation relaxed)."),
]


def by_id(cid: str) -> Change:
    for c in CATALOG:
        if c.id == cid:
            return c
    raise KeyError(cid)
