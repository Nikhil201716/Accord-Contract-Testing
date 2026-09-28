# Accord — REST + GraphQL, and which API test catches which breaking change

**Across 13 realistic breaking API changes, no single testing mechanism catches
them all: the provider's own tests catch 5, consumer-driven contracts catch 7,
and a structural schema-diff catches 10 — and 2 slip past all three. Each
mechanism owns a different class of break. Contracts catch 5 changes the
provider's own tests miss (including a semantic one no schema-diff can see);
schema-diff catches 4 that no consumer declared; and a silent format change and a
relaxed input validation escape everything. API safety is layered, or it is
luck.**

Accord is a book-catalog API exposed over **both REST and GraphQL** (FastAPI +
Strawberry, SQLite-free in-memory store), plus a **reading-list consumer** with a
Pact-style **contract**. A harness injects a catalog of 15 API changes (13
breaking, 2 additive) one at a time and scores three mechanisms against each.

| Mechanism | Breaking changes caught (of 13) | What it uniquely owns |
|---|---|---|
| Provider's own tests | 5 | changes that break what the provider *chose to assert* |
| Consumer-driven contract | 7 | what the *consumer* depends on — incl. breaks the provider never tested, and (with value matchers) a semantic rescale |
| Schema-diff (structural) | **10** | structural/type breaks with **no consumer needed** — even in fields nobody uses |
| **Caught by at least one** | **11** | |
| **Slip past all three** | **2** | a silent format change; relaxed input validation |
| False positives on 2 additive changes | **0** | schema-diff correctly ignores additive changes |

Every number is read from [`reports/`](reports/), written by a real run and
**byte-reproducible** (verified by re-running and diffing).

## The point: the mechanisms are complementary, not ranked

- **Contracts catch what provider tests miss.** A rename of `cover_url` or a
  retype of `rating` — fields the provider treats as presentation extras and does
  not assert — sails past the provider's own suite. The consumer *renders* those
  fields, so its contract fails. That gap between "what the provider tests" and
  "what the consumer depends on" is exactly what consumer-driven contracts exist
  to close, and here it is 5 of 13 changes.
- **Schema-diff catches what contracts can't see.** Dropping `year`, changing a
  status code, widening a field to nullable — none of these touch a field the
  consumer declared, so the contract is (correctly) silent. A structural diff of
  the OpenAPI/GraphQL schema catches all of them with no consumer in the loop.
- **A value matcher catches what structure can't.** Rescaling `rating` from 0–5
  to 0–100 keeps the type `float`, so schema-diff and a type-only check are blind.
  The contract's `rating ∈ [0,5]` matcher catches it — the one change the
  contract catches that schema-diff cannot.
- **Two breaks escape everything.** A silent ISBN format change (hyphens
  stripped, still a string, no consumer declared it) and a relaxed request
  validation (`year` bound widened) slip past all three — genuine coverage gaps
  that need a value/regex contract matcher or a data-quality test.

## REST vs GraphQL, concretely

The same catalog break is easier to catch on the GraphQL side because the schema
is typed and introspectable: renaming or retyping a field is a structural SDL
diff. REST's untyped JSON needs the schema-diff to *derive* the shape from live
responses. Both are scored; the notebook walks the difference.

## What runs, and what is honest about it

- [`provider/`](provider/) — the FastAPI app: REST + a Strawberry GraphQL schema
  over one store. Python only.
- [`consumer/`](consumer/) — the reading-list client SDK and its Pact-style
  contract ([`contracts/reading-list.json`](consumer/contracts/reading-list.json)).
- [`testing/`](testing/) — the provider's own tests and the consumer integration
  tests (19 tests).
- [`scoring/`](scoring/) — the contract verifier, the schema-diff, the
  fault-injection harness, and a Hypothesis fuzzer.
- [`postman/`](postman/) — a Postman collection run with Newman in CI.

The catch *rates* are illustrative of each mechanism's reach, not an estimate of
any team's escape rate — the 15 changes are curated to span classes cleanly. What
is robust is the *structure*: each mechanism owns a class, and semantic breaks
escape structural and type checks. A property-based **fuzz** of the create
endpoint found **0 unhandled 5xx** across 300 malformed payloads — validation
holds, which is the point of running it.

## Reproduce it

See [RUN.md](RUN.md). In short:

```bash
pip install -r provider/requirements.txt
python -m pytest testing            # 19 tests (provider + consumer)
python scoring/verify_contract.py   # contract satisfied on the clean provider
python scoring/score.py             # the finding -> reports/*.json (byte-reproducible)
python scoring/fuzz.py              # 0 unhandled 5xx
```

## The notebook

[`docs/Accord-Notebook.pdf`](docs/) is a ~60-page write-up: the REST + GraphQL
provider, the consumer and its contract, all three mechanisms, the full catch
matrix by change class, and a chapter tracing three changes — one only the
contract catches, one only schema-diff catches, one nothing catches — through
every mechanism.
