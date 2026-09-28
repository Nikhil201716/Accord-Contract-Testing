"""Pydantic models for the REST surface. The response model is the provider's
declared shape -- what it promises to return -- and several catalog changes edit
exactly this to simulate a breaking API change (a renamed or retyped field)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    year: int
    tags: list[str]
    available: bool
    cover_url: str
    rating: float


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)
    isbn: str = Field(min_length=10, max_length=20)
    year: int = Field(ge=1400, le=2100)
    tags: list[str] = Field(default_factory=list)
