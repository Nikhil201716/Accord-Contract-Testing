"""The provider's own GraphQL tests: the queries resolve, filtering works, a
missing book is null, and the schema exposes the Book type. Like the REST suite,
it asserts behaviour and core fields, not every field of every type."""

from conftest import gql


def test_book_by_id(client):
    r = gql(client, "{ book(id: 1) { id title author year } }")
    assert r.get("errors") is None
    b = r["data"]["book"]
    assert b["id"] == 1
    assert b["title"] == "The Left Hand of Darkness"
    assert b["author"] == "Ursula K. Le Guin"
    assert b["year"] == 1969


def test_missing_book_is_null(client):
    r = gql(client, "{ book(id: 999) { id } }")
    assert r["data"]["book"] is None


def test_books_filter_by_tag(client):
    r = gql(client, '{ books(tag: "classic") { id title } }')
    ids = {b["id"] for b in r["data"]["books"]}
    assert ids == {1, 3, 5}


def test_books_list_all(client):
    r = gql(client, "{ books { id } }")
    assert len(r["data"]["books"]) == 5


def test_schema_exposes_book_type(client):
    # introspection: the Book type and its title field must exist
    q = '{ __type(name: "Book") { name fields { name } } }'
    r = gql(client, q)
    t = r["data"]["__type"]
    assert t["name"] == "Book"
    names = {f["name"] for f in t["fields"]}
    assert {"id", "title", "author"} <= names
