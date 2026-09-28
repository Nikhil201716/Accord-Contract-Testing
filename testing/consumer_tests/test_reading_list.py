"""Consumer tests: the reading-list widget driven against the REAL provider
(in-process). These are integration tests -- they exercise the consumer and
provider together, so they catch a breaking change, but only by running both.
The lightweight *contract* (verified separately) is what lets the provider check
the same guarantees on its own, without the consumer in the loop.
"""

from consumer.client import ReadingListClient


def test_shelf_renders_every_book(client):
    shelf = ReadingListClient(client).shelf()
    assert len(shelf) == 5
    first = shelf[0]
    assert first.title
    assert first.cover_url.startswith("https://")   # the widget needs a cover
    assert isinstance(first.available, bool)


def test_detail_has_cover_and_rating(client):
    d = ReadingListClient(client).detail(1)
    assert d["cover_url"].startswith("https://")
    assert isinstance(d["rating"], float)            # the widget shows a 0-5 rating


def test_detail_via_graphql(client):
    d = ReadingListClient(client).detail_via_graphql(1)
    assert d["title"] == "The Left Hand of Darkness"
    assert isinstance(d["rating"], float)
