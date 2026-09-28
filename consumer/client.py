"""The reading-list widget's client -- a small SDK over the Accord API. It uses
exactly the fields declared in consumer/contracts/reading-list.json, so the
contract is not a paper promise: this is the code the contract protects. In a
real deployment it would talk to the provider over HTTP; here it takes any
callable that behaves like httpx/TestClient, so it can be pointed at an
in-process provider for testing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShelfItem:
    id: int
    title: str
    author: str
    cover_url: str
    available: bool


class ReadingListClient:
    def __init__(self, http) -> None:
        # `http` is anything with .get(path) and .post(path, json=...) -> response
        self.http = http

    def shelf(self) -> list[ShelfItem]:
        """The main view: every book, rendered as a shelf card."""
        rows = self.http.get("/api/books").json()
        return [ShelfItem(r["id"], r["title"], r["author"],
                          r["cover_url"], r["available"]) for r in rows]

    def detail(self, book_id: int) -> dict:
        """A book's detail page, which shows the rating and cover."""
        b = self.http.get(f"/api/books/{book_id}").json()
        return {"id": b["id"], "title": b["title"], "author": b["author"],
                "cover_url": b["cover_url"], "rating": b["rating"]}

    def detail_via_graphql(self, book_id: int) -> dict:
        q = "{ book(id: %d) { id title author rating } }" % book_id
        data = self.http.post("/graphql", json={"query": q}).json()["data"]["book"]
        return data
