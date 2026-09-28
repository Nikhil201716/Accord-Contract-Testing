# Running Accord

**Python 3.12+** for everything measured; **Node 20+** only for the optional
Newman run of the Postman collection. No paid service, no account.

## One-click (devcontainer / Codespaces)

```bash
bash .devcontainer/run-project.sh
```

Installs the provider, runs the tests and the contract, runs the fault-injection
scoring, and runs the fuzzer — writing `reports/*.json`.

## Python: the provider, the tests, and the finding

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r provider/requirements.txt

python -m pytest testing              # 19 tests: provider (REST+GraphQL) + consumer
python scoring/verify_contract.py     # verify the consumer contract on the clean provider
python scoring/score.py               # inject 15 API changes, score 3 mechanisms -> reports/*.json
python scoring/fuzz.py                # property-based fuzz of the create endpoint
```

`scoring/score.py` copies the project into a throwaway dir, applies each change
from `scoring/catalog.py`, and runs the provider tests, the consumer contract
verification, and the schema-diff against the patched copy. `catch_matrix.json`
and `summary.json` are byte-reproducible.

## Run the provider (to explore REST + GraphQL by hand)

```bash
cd provider && python -m uvicorn app.main:app --port 8000
# REST:     http://localhost:8000/api/books
# GraphQL:  http://localhost:8000/graphql  (interactive GraphiQL in a browser)
```

## Postman / Newman (optional — needs Node)

```bash
cd provider && python -m uvicorn app.main:app --port 8000 &   # start the provider
npx --yes newman run postman/accord.postman_collection.json --env-var baseUrl=http://localhost:8000
```

## What you should see

- `19 passed` across the test suite.
- `scoring/score.py` prints a per-change matrix and a headline, and writes
  `reports/catch_matrix.json` + `summary.json` (identical on re-run).
- `scoring/fuzz.py` reports `no unhandled 5xx` and writes `reports/fuzz.json`.
