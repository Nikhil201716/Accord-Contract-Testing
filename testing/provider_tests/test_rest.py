"""The provider's own REST tests: a thorough, realistic suite of the behaviour
the provider team considers its contract -- status codes, filtering, errors, and
the core identity fields of a book. It deliberately does NOT assert every field
in every response (no team asserts cover_url or rating on each endpoint); that
gap between 'what the provider tests' and 'what a consumer depends on' is exactly
what the consumer contract measures.
"""


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_list_returns_all(client):
    r = client.get("/api/books")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_list_items_have_core_identity(client):
    for b in client.get("/api/books").json():
        assert isinstance(b["id"], int)
        assert isinstance(b["title"], str) and b["title"]
        assert isinstance(b["author"], str) and b["author"]


def test_get_one_core_fields(client):
    b = client.get("/api/books/1").json()
    assert b["id"] == 1
    assert b["title"] == "The Left Hand of Darkness"
    assert b["author"] == "Ursula K. Le Guin"
    assert b["year"] == 1969
    assert b["available"] is True


def test_get_missing_is_404(client):
    assert client.get("/api/books/999").status_code == 404


def test_filter_by_tag(client):
    r = client.get("/api/books", params={"tag": "fantasy"})
    assert r.status_code == 200
    titles = {b["title"] for b in r.json()}
    assert titles == {"A Wizard of Earthsea"}


def test_filter_by_availability(client):
    unavailable = client.get("/api/books", params={"available": "false"}).json()
    assert {b["id"] for b in unavailable} == {3}


def test_create_returns_201_and_persists(client):
    r = client.post("/api/books", json={
        "title": "New Book", "author": "A. Writer",
        "isbn": "978-0000000000", "year": 2020, "tags": ["new"]})
    assert r.status_code == 201
    new_id = r.json()["id"]
    assert client.get(f"/api/books/{new_id}").status_code == 200


def test_create_validation_is_422(client):
    r = client.post("/api/books", json={
        "title": "", "author": "x", "isbn": "short", "year": 3000})
    assert r.status_code == 422


def test_author_books(client):
    r = client.get("/api/authors/Octavia E. Butler/books")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_author_without_books_is_404(client):
    assert client.get("/api/authors/Nobody/books").status_code == 404
