"""The REST surface. Thin routes over the store that map a Book to the declared
BookOut shape. The mapping (`_to_out`) is the single place the response contract
lives, so a catalog change that renames or retypes a field edits one function.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .models import BookCreate, BookOut
from .store import Book, Store


def _to_out(b: Book) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "isbn": b.isbn,
        "year": b.year,
        "tags": b.tags,
        "available": b.available,
        "cover_url": b.cover_url,
        "rating": b.rating,
    }


def build_rest_router(store: Store) -> APIRouter:
    r = APIRouter(prefix="/api")

    @r.get("/health")
    def health():
        return {"status": "ok"}

    @r.get("/books", response_model=list[BookOut])
    def list_books(tag: str | None = Query(default=None),
                   available: bool | None = Query(default=None)):
        return [_to_out(b) for b in store.all(tag=tag, available=available)]

    @r.get("/books/{book_id}", response_model=BookOut)
    def get_book(book_id: int):
        b = store.get(book_id)
        if b is None:
            raise HTTPException(status_code=404, detail="book not found")
        return _to_out(b)

    @r.post("/books", response_model=BookOut, status_code=201)
    def create_book(body: BookCreate):
        b = store.add(body.title, body.author, body.isbn, body.year, body.tags)
        return _to_out(b)

    @r.get("/authors/{author}/books", response_model=list[BookOut])
    def books_by_author(author: str):
        books = store.by_author(author)
        if not books:
            raise HTTPException(status_code=404, detail="author has no books")
        return [_to_out(b) for b in books]

    return r
