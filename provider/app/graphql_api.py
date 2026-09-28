"""The GraphQL surface, over the same store. The Book type here is the GraphQL
schema's declared shape; renaming or retyping a field edits it, and the schema
diff detects that structurally from the printed SDL -- something REST's untyped
JSON cannot offer without extra tooling.
"""

from __future__ import annotations

import strawberry

from .store import Store


@strawberry.type
class Book:
    id: int
    title: str
    author: str
    isbn: str
    year: int
    tags: list[str]
    available: bool
    cover_url: str
    rating: float


def _to_gql(b) -> Book:
    return Book(id=b.id, title=b.title, author=b.author, isbn=b.isbn, year=b.year,
                tags=list(b.tags), available=b.available, cover_url=b.cover_url,
                rating=b.rating)


def build_schema(store: Store) -> strawberry.Schema:
    @strawberry.type
    class Query:
        @strawberry.field
        def books(self, tag: str | None = None) -> list[Book]:
            return [_to_gql(b) for b in store.all(tag=tag)]

        @strawberry.field
        def book(self, id: int) -> Book | None:
            b = store.get(id)
            return _to_gql(b) if b else None

    return strawberry.Schema(query=Query)
