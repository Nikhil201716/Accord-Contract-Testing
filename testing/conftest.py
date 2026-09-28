"""Shared fixtures. The provider is put on the path relative to this file, so
the same tests run unchanged against the real provider and against a patched
copy (the scoring harness copies provider/ + testing/ into a temp dir)."""

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "provider"))
sys.path.insert(0, str(_ROOT))                       # for `import consumer.client`

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def gql(client, query: str) -> dict:
    """Run a GraphQL query and return the JSON envelope ({data, errors})."""
    return client.post("/graphql", json={"query": query}).json()
