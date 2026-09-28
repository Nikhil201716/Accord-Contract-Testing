"""In-memory book catalog -- the data the provider serves over both REST and
GraphQL. A plain dict-backed store with a fixed seed, so every test and every
scored run sees exactly the same catalog and the results reproduce.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    year: int                       # year of publication
    tags: list[str] = field(default_factory=list)
    available: bool = True
    cover_url: str = ""
    rating: float = 0.0


_SEED: list[Book] = [
    Book(1, "The Left Hand of Darkness", "Ursula K. Le Guin", "978-0441478125",
         1969, ["scifi", "classic"], True, "https://covers.accord.test/1.jpg", 4.5),
    Book(2, "Kindred", "Octavia E. Butler", "978-0807083697",
         1979, ["scifi", "historical"], True, "https://covers.accord.test/2.jpg", 4.6),
    Book(3, "The Dispossessed", "Ursula K. Le Guin", "978-0061054884",
         1974, ["scifi", "classic"], False, "https://covers.accord.test/3.jpg", 4.4),
    Book(4, "Parable of the Sower", "Octavia E. Butler", "978-1538732182",
         1993, ["scifi", "dystopia"], True, "https://covers.accord.test/4.jpg", 4.3),
    Book(5, "A Wizard of Earthsea", "Ursula K. Le Guin", "978-0547773742",
         1968, ["fantasy", "classic"], True, "https://covers.accord.test/5.jpg", 4.2),
]


class Store:
    def __init__(self) -> None:
        self._books: dict[int, Book] = {}
        self._next = 1
        for b in _SEED:
            self._books[b.id] = Book(**b.__dict__)
            self._next = max(self._next, b.id + 1)

    def all(self, tag: str | None = None, available: bool | None = None) -> list[Book]:
        out = list(self._books.values())
        if tag is not None:
            out = [b for b in out if tag in b.tags]
        if available is not None:
            out = [b for b in out if b.available is available]
        return sorted(out, key=lambda b: b.id)

    def get(self, book_id: int) -> Book | None:
        return self._books.get(book_id)

    def by_author(self, author: str) -> list[Book]:
        return [b for b in self.all() if b.author == author]

    def add(self, title: str, author: str, isbn: str, year: int,
            tags: list[str] | None = None) -> Book:
        b = Book(self._next, title, author, isbn, year, tags or [],
                 True, f"https://covers.accord.test/{self._next}.jpg", 0.0)
        self._books[b.id] = b
        self._next += 1
        return b
