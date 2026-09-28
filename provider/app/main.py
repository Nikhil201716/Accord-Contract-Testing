"""The Accord provider: one FastAPI app exposing the same book catalog over
REST (/api/...) and GraphQL (/graphql). `create_app` is a factory so tests and
the scoring harness each get an isolated store.
"""

from __future__ import annotations

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from .graphql_api import build_schema
from .rest import build_rest_router
from .store import Store


def create_app() -> FastAPI:
    app = FastAPI(title="Accord", version="1.0")
    store = Store()
    app.state.store = store

    app.include_router(build_rest_router(store))

    schema = build_schema(store)
    app.state.schema = schema
    app.include_router(GraphQLRouter(schema), prefix="/graphql")

    return app


app = create_app()
