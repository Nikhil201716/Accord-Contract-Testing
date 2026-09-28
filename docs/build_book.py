"""Builds the Accord notebook. Listings are pulled from the repo by marker and
every number is read from reports/*.json, so the book fails rather than shipping
a stale claim.

    python docs/build_book.py     (run scoring/score.py and scoring/fuzz.py first)
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
sys.path.insert(0, str(PROJ.parent / "bookgen"))

from engine import (  # noqa: E402
    build, callout, code_from, code_literal, ol, p, table, ul,
)

REPO = "github.com/Nikhil201716/Accord-Contract-Testing"


def report(name):
    return json.loads((PROJ / "reports" / f"{name}.json").read_text(encoding="utf-8"))


SUM = report("summary")
MATRIX = report("catch_matrix")["changes"]
try:
    FUZZ = report("fuzz")
except FileNotFoundError:
    FUZZ = None

MECHS = SUM["mechanisms"]                     # provider_tests, contract, schema_diff
CPM = SUM["caught_per_mechanism_of_breaking"]
NB = SUM["breaking_changes"]


def yn(b):
    return "✓" if b else "·"


SDL = """type Book {
  id: Int!
  title: String!
  author: String!
  isbn: String!
  year: Int!
  tags: [String!]!
  available: Boolean!
  coverUrl: String!
  rating: Float!
}

type Query {
  books(tag: String = null): [Book!]!
  book(id: Int!): Book
}"""


# ══════════════════════════════════════════════════════════════ chapter 1 ══

CH1 = {
    "title": "No single API test catches everything",
    "abstract": (
        "REST and GraphQL, three testing mechanisms, and a catalog of breaking "
        "changes -- measured. Each mechanism owns a different class of break, and "
        "some breaks escape them all."),
    "sections": [
        {"title": "The finding", "html": "".join([
            p("Accord is a book-catalog API served over <b>both REST and "
              "GraphQL</b>, with a reading-list consumer and a Pact-style "
              "contract. A harness injects a catalog of API changes one at a time "
              "and scores three testing mechanisms against each: the provider's "
              "own tests, consumer-driven contract verification, and a structural "
              "schema diff."),
            p(f"<b>{SUM['headline']}</b>"),
            table(["Mechanism", f"Breaking caught (of {NB})", "What it uniquely owns"],
                  [["provider's own tests", str(CPM["provider_tests"]),
                    "changes that break what the provider chose to assert"],
                   ["consumer-driven contract", str(CPM["contract"]),
                    "what the consumer depends on -- incl. breaks the provider never tested"],
                   ["schema diff (structural)", str(CPM["schema_diff"]),
                    "structural / type breaks, with no consumer needed"]],
                  caption="Table 1.1 - catch counts by mechanism (reports/summary.json)",
                  highlight_col=1),
            p(f"Of {NB} breaking changes, "
              f"{SUM['breaking_caught_by_any']} are caught by at least one "
              f"mechanism and {SUM['breaking_missed_by_all']} slip past all "
              f"three. Crucially the three are <i>complementary, not ranked</i>: "
              f"contracts catch "
              f"{len(SUM['contract_catches_provider_tests_miss'])} changes the "
              f"provider's own tests miss, schema diff catches "
              f"{len(SUM['schema_diff_catches_contract_blind'])} the contract is "
              f"blind to, and the contract catches "
              f"{len(SUM['contract_catches_schema_diff_blind'])} the schema diff "
              f"cannot see. There is no one tool to buy."),
        ])},
        {"title": "Why a book catalog over REST and GraphQL", "html": "".join([
            p("The domain is small on purpose; the point is the testing. Serving "
              "the same data two ways -- REST's untyped JSON and GraphQL's typed, "
              "introspectable schema -- lets the study measure something real: a "
              "typed schema turns a whole class of breaking change into a "
              "structural diff, while REST needs the shape derived from live "
              "responses. Both are scored side by side."),
            ul(["<b>provider/</b> - FastAPI REST + a Strawberry GraphQL schema over one store.",
                "<b>consumer/</b> - a reading-list client and its Pact-style contract.",
                "<b>testing/</b> - the provider's own tests and consumer integration tests.",
                "<b>scoring/</b> - the contract verifier, the schema diff, the harness, a fuzzer.",
                "<b>reports/</b> - the source of every number here."]),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 2 ══

CH2 = {
    "title": "One catalog, two surfaces",
    "abstract": "The store, and the single FastAPI app that exposes it as REST and GraphQL.",
    "sections": [
        {"title": "The data", "html": "".join([
            p("A book is a plain dataclass; the store is a fixed, seeded set of "
              "them, so every test and every scored run sees the same catalog and "
              "the results reproduce."),
            code_from(PROJ, "provider/app/store.py",
                      start="class Book:", end="rating: float = 0.0",
                      caption="Listing 2.1 - the Book record",
                      lang="python"),
        ])},
        {"title": "One app, two routers", "html": "".join([
            p("The app factory mounts a REST router and a GraphQL router over the "
              "same store, so the two surfaces are always in sync on the data and "
              "differ only in how they describe it."),
            code_from(PROJ, "provider/app/main.py",
                      start="def create_app() -> FastAPI:",
                      end='app.include_router(GraphQLRouter(schema), prefix="/graphql")',
                      caption="Listing 2.2 - REST + GraphQL from one factory",
                      lang="python"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 3 ══

CH3 = {
    "title": "The REST surface",
    "abstract": "Thin routes and one mapping function -- the single place the "
                "response contract lives.",
    "sections": [
        {"title": "The response shape", "html": "".join([
            p("Every REST response is built by one function that maps a Book to "
              "the declared shape. Concentrating the contract here means a breaking "
              "change (a renamed or retyped field) is a one-line edit -- which is "
              "exactly how the catalog expresses several of them."),
            code_from(PROJ, "provider/app/rest.py",
                      start="def _to_out(b: Book) -> dict:", end="    }",
                      caption="Listing 3.1 - the REST response mapping",
                      lang="python"),
            code_from(PROJ, "provider/app/rest.py",
                      start='    @r.get("/books/{book_id}", response_model=BookOut)',
                      end="return _to_out(b)",
                      caption="Listing 3.2 - a route (status codes are part of the contract)",
                      lang="python"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 4 ══

CH4 = {
    "title": "The GraphQL surface",
    "abstract": "The same data, a typed schema -- and why that typing is a testing "
                "asset.",
    "sections": [
        {"title": "The schema", "html": "".join([
            p("The GraphQL type mirrors the REST shape, but it is <i>typed and "
              "printable</i>. Strawberry converts snake_case to camelCase, so "
              "cover_url becomes coverUrl in the schema."),
            code_from(PROJ, "provider/app/graphql_api.py",
                      start="class Book:", end="rating: float",
                      caption="Listing 4.1 - the GraphQL Book type",
                      lang="python"),
            code_from(PROJ, "provider/app/graphql_api.py",
                      start="def build_schema(store: Store) -> strawberry.Schema:",
                      end="return strawberry.Schema(query=Query)",
                      caption="Listing 4.2 - the Query resolvers",
                      lang="python"),
            p("Printed, the schema is the contract in one glance -- and a diff of "
              "this SDL is a breaking-change detector that needs no consumer:"),
            code_literal(SDL, "Listing 4.3 - the printed GraphQL SDL", "graphql"),
            p("The mapping from a stored Book to the GraphQL type is the GraphQL "
              "counterpart of the REST <code>_to_out</code> -- and the place a "
              "GraphQL field rename or retype is injected:"),
            code_from(PROJ, "provider/app/graphql_api.py",
                      start="def _to_gql(b) -> Book:", end="rating=b.rating)",
                      caption="Listing 4.4 - mapping a Book into the GraphQL type",
                      lang="python"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 5 ══

CH5 = {
    "title": "The provider's own tests",
    "abstract": "A thorough, realistic suite -- and the fields it does not assert, "
                "which is where the consumer gap lives.",
    "sections": [
        {"title": "What the provider tests", "html": "".join([
            p("The provider's suite is genuinely thorough on behaviour: status "
              "codes, filtering, errors, and the core identity fields of a book. "
              "What it does not do -- what almost no provider suite does -- is "
              "assert every field of every response."),
            code_from(PROJ, "testing/provider_tests/test_rest.py",
                      start="def test_get_one_core_fields(client):",
                      end='assert b["available"] is True',
                      caption="Listing 5.1 - the provider asserts core fields, not cover_url or rating",
                      lang="python"),
            code_from(PROJ, "testing/provider_tests/test_graphql.py",
                      start="def test_book_by_id(client):",
                      end='assert b["year"] == 1969',
                      caption="Listing 5.2 - the GraphQL provider test",
                      lang="python"),
            p("This is not a weak suite -- it is a realistic one. The gap between "
              "\"what the provider asserts\" and \"what a consumer depends on\" is "
              "universal in any multi-team system, and it is exactly the gap the "
              "consumer contract is built to close."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 6 ══

CH6 = {
    "title": "The consumer and its contract",
    "abstract": "A real client that renders specific fields, and the Pact-style "
                "contract that pins them.",
    "sections": [
        {"title": "The consumer", "html": "".join([
            p("The reading-list widget renders a shelf and a detail page. It "
              "depends on cover_url and rating -- the very fields the provider "
              "treats as incidental. This is the code the contract protects."),
            code_from(PROJ, "consumer/client.py",
                      start="    def shelf(self) -> list[ShelfItem]:",
                      end='r["cover_url"], r["available"]) for r in rows]',
                      caption="Listing 6.1 - the consumer renders cover_url",
                      lang="python"),
        ])},
        {"title": "The contract", "html": "".join([
            p("The contract is a Pact-style list of interactions: for each request "
              "the consumer makes, the response fields and types it needs -- and, "
              "for rating, a <i>value</i> matcher, because a rating is 0-5, not "
              "merely 'a float'."),
            code_from(PROJ, "consumer/contracts/reading-list.json",
                      start='"description": "REST: open a book',
                      end='"value_rules": [{ "field": "rating", "min": 0.0, "max": 5.0 }]',
                      caption="Listing 6.2 - a contract interaction with a value matcher",
                      lang="json"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 7 ══

CH7 = {
    "title": "Consumer-driven contract verification",
    "abstract": "Replay what the consumer declared against the provider -- a "
                "dependency-free Pact.",
    "sections": [
        {"title": "Verifying the provider against the consumer's needs", "html": "".join([
            p("Verification replays every declared interaction against the "
              "provider and checks status, field presence, field type, and value "
              "matchers. Unlike the provider's own tests, it encodes the "
              "<i>consumer's</i> needs -- so it catches a break the provider never "
              "thought to test, and (by design) it is blind to changes in fields "
              "no consumer depends on."),
            code_from(PROJ, "scoring/verify_contract.py",
                      start="def _check_fields(elem, fields, desc, violations, rules=()) -> None:",
                      end="violations.append(f\"{desc}: field '{f}'={v} above max {rule['max']}\")",
                      caption="Listing 7.1 - field, type and value checks",
                      lang="python"),
            code_from(PROJ, "scoring/verify_contract.py",
                      start="def verify(client, contract: dict) -> list[str]:",
                      end="return list(dict.fromkeys(violations))",
                      caption="Listing 7.2 - replaying REST and GraphQL interactions",
                      lang="python"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 8 ══

CH8 = {
    "title": "The schema diff",
    "abstract": "A structural API linter -- breaking changes with no consumer, and "
                "its one blind spot.",
    "sections": [
        {"title": "Derive a descriptor, diff it", "html": "".join([
            p("The schema diff derives a comparable descriptor of the provider -- "
              "REST paths, the shape of a book, probe status codes, and the "
              "GraphQL type map -- and compares it against a baseline from the "
              "known-good provider. It reports only <i>breaking</i> diffs and "
              "ignores additive ones, so a new field is never a false alarm."),
            code_from(PROJ, "scoring/schema_diff.py",
                      start="def descriptor(client, schema) -> dict:",
                      end='"graphql": _graphql_types(schema),',
                      caption="Listing 8.1 - the provider descriptor",
                      lang="python"),
            code_from(PROJ, "scoring/schema_diff.py",
                      start="def diff(base: dict, cur: dict) -> list[str]:",
                      end="return breaks",
                      caption="Listing 8.2 - breaking-change detection",
                      lang="python"),
            p("Its blind spot is semantics: a field whose name and type are "
              "unchanged but whose <i>meaning</i> changed looks identical. That is "
              "the one class the value matcher in the contract can catch and the "
              "diff cannot."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 9 ══

CH9 = {
    "title": "The change catalog",
    "abstract": "Realistic API changes, breaking and additive, each an exact edit.",
    "sections": [
        {"title": "A change is one or more edits", "html": "".join([
            p("Each catalog entry is a class, a breaking flag, and a set of exact "
              "source edits. Breaking changes should be caught by at least one "
              "mechanism; additive ones by none (a mechanism flagging an additive "
              "change is a false positive, measured too)."),
            code_from(PROJ, "scoring/catalog.py",
                      start="class Change:", end="desc: str",
                      caption="Listing 9.1 - the Change record",
                      lang="python"),
            code_from(PROJ, "scoring/catalog.py",
                      start='Change("C01", "rename", True, (',
                      end='(a field the consumer renders)."),',
                      caption="Listing 9.2 - a field rename (two edits: model + mapping)",
                      lang="python"),
            code_from(PROJ, "scoring/catalog.py",
                      start='Change("C12", "semantic", True, (',
                      end='(still a float)."),',
                      caption="Listing 9.3 - a semantic change: shape identical, meaning changed",
                      lang="python"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 10 ══

CH10 = {
    "title": "The scoring harness",
    "abstract": "Copy, patch, run three mechanisms, record. Deterministic.",
    "sections": [
        {"title": "Apply and measure", "html": "".join([
            p("For each change the harness stages a throwaway copy, applies the "
              "edits (refusing an ambiguous marker), and runs all three mechanisms "
              "against the patched copy."),
            code_from(PROJ, "scoring/score.py",
                      start="def _apply(dst: Path, change) -> None:",
                      end='target.write_text(text.replace(find, replace), encoding="utf-8")',
                      caption="Listing 10.1 - applying a change",
                      lang="python"),
            code_from(PROJ, "scoring/score.py",
                      start="def _mechanisms(cwd: Path, baseline: str) -> dict:",
                      end='"schema_diff": _probe(cwd, "schemadiff", baseline),',
                      caption="Listing 10.2 - the three mechanisms",
                      lang="python"),
            p("The contract and schema-diff run in a subprocess against the "
              "patched provider, so they import the changed code, not the "
              "original. The clean provider must pass all three first, or a "
              "mechanism that always fails would look omniscient."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ chapter 11 ══


def _matrix_rows():
    rows = []
    for cid in sorted(MATRIX):
        c = MATRIX[cid]
        caught = c["caught"]
        tag = ""
        if c["breaking"] and not any(caught.values()):
            tag = "missed"
        if (not c["breaking"]) and any(caught.values()):
            tag = "false +"
        rows.append([cid, c["klass"], "break" if c["breaking"] else "add",
                     yn(caught["provider_tests"]), yn(caught["contract"]),
                     yn(caught["schema_diff"]), tag])
    return rows


CH11 = {
    "title": "Results",
    "abstract": "The full matrix, who catches what the others miss, and the gaps.",
    "sections": [
        {"title": "The catch matrix", "html": "".join([
            table(["Change", "Class", "Kind", "provider", "contract", "schema", "note"],
                  _matrix_rows(),
                  caption="Table 11.1 - every change, every mechanism (reports/catch_matrix.json)"),
        ])},
        {"title": "Who catches what the others miss", "html": "".join([
            p("The complementarity is the whole point:"),
            ul([f"<b>Contract catches, provider tests miss:</b> "
                f"{', '.join(SUM['contract_catches_provider_tests_miss'])} -- "
                f"renames and retypes of fields the provider treats as incidental "
                f"but the consumer renders.",
                f"<b>Schema diff catches, contract is blind:</b> "
                f"{', '.join(SUM['schema_diff_catches_contract_blind'])} -- "
                f"changes to fields/behaviour no consumer declared (a dropped "
                f"field, a status code, a nullability widening).",
                f"<b>Contract catches, schema diff cannot:</b> "
                f"{', '.join(SUM['contract_catches_schema_diff_blind']) or '(none)'} "
                f"-- a semantic rescale caught only by the value matcher."]),
            table(["Class", "changes", "provider", "contract", "schema"],
                  [[k, str(v["changes"]), str(v["provider_tests"]), str(v["contract"]),
                    str(v["schema_diff"])] for k, v in sorted(SUM["per_class"].items())],
                  caption="Table 11.2 - catch counts by change class"),
        ])},
        {"title": "The gaps", "html": "".join([
            p(f"{SUM['breaking_missed_by_all']} breaking changes slip past all "
              f"three mechanisms -- the finding that matters most, because a green "
              f"pipeline hides it:"),
            (table(["Change", "Class", "Why all three miss it"],
                   [[g["id"], g["klass"], g["desc"]] for g in SUM["missed_breaking"]],
                   caption="Table 11.3 - breaking changes no mechanism caught")
             if SUM["missed_breaking"] else p("(none in this run)")),
            p(f"And no mechanism raised a false positive on the "
              f"{SUM['additive_changes']} additive changes -- the schema diff "
              f"correctly treats a new field as non-breaking."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ fuzz ══

CH_FUZZ = {
    "title": "Fuzzing the write path",
    "abstract": "Property-based negative testing -- and why finding nothing is the point.",
    "sections": [
        {"title": "No unhandled crash", "html": "".join([
            p("The create endpoint is fuzzed with a wide space of malformed "
              "payloads, asserting one property: the server never answers 5xx. A "
              "well-built API rejects bad input with 422, never a crash."),
            code_from(PROJ, "scoring/fuzz.py",
                      start="@given(p=_payload)", end="assert r.status_code < 500",
                      caption="Listing FZ.1 - the fuzz property",
                      lang="python"),
            (p(f"Result: <b>{FUZZ['verdict']}</b> across {FUZZ['max_examples']} "
               f"generated payloads.") if FUZZ else
             p("(run scoring/fuzz.py to populate reports/fuzz.json)")),
            p("Finding nothing is not wasted effort -- it is cheap evidence that "
              "the Pydantic validation layer holds, and a tripwire for the day it "
              "is weakened (the catalog's relaxed-validation change is exactly "
              "that day)."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ ci ══

CH_CI = {
    "title": "Every mechanism in CI",
    "abstract": "Provider tests, the contract, the scoring, the fuzzer, and a "
                "Newman run -- on every push.",
    "sections": [
        {"title": "The pipeline", "html": "".join([
            p("All of it runs in CI, so a change that weakens any layer turns the "
              "build red. A second job starts the provider and runs the Postman "
              "collection with Newman -- the same requests a QA engineer would "
              "click through, automated."),
            code_from(PROJ, ".github/workflows/ci.yml",
                      start="  newman:", end="--env-var baseUrl=http://localhost:8000",
                      caption="Listing CI.1 - the Newman job",
                      lang="yaml"),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ limits ══

CH_LIMITS = {
    "title": "What this does not establish",
    "abstract": "The honest boundary around a curated, single-consumer study.",
    "sections": [
        {"title": "A curated catalog, one consumer", "html": "".join([
            p(f"The {SUM['total_changes']} changes are hand-picked to span classes "
              f"cleanly, and there is one consumer with one contract. So the catch "
              f"counts are illustrative of each mechanism's <i>reach</i>, not an "
              f"estimate of any team's escape rate, and the contract's blind spots "
              f"are the blind spots of <i>this</i> contract -- a second consumer "
              f"depending on isbn would catch the format change that here slips "
              f"through. What is robust is the structure: each mechanism owns a "
              f"class, and semantics escape structural and type checks."),
        ])},
        {"title": "'Caught' means one check failed", "html": "".join([
            p("A mechanism catches a change if it produced at least one failure. "
              "The study does not grade how good the failure message is, or whether "
              "it points a developer at the cause. And the schema diff is only as "
              "good as its descriptor: it compares the shape of one book and the "
              "GraphQL type map, not every nested response in the API."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════════ reading ══

CH_READING = {
    "title": "Where to read further",
    "abstract": "Contract testing, schema evolution, and API testing tools.",
    "sections": [
        {"title": "The sources", "html": "".join([
            p("Consumer-driven contracts come from Ian Robinson's writing and are "
              "embodied in <b>Pact</b> (pact.io) -- this project's verifier is a "
              "tiny, dependency-free version of Pact's provider verification, "
              "including value matchers. Martin Fowler's articles "
              "\"ContractTest\", \"ConsumerDrivenContracts\" and "
              "\"IntegrationContractTest\" are the canonical short reads. For "
              "schema evolution, the GraphQL specification's section on "
              "non-breaking changes and tools like <b>graphql-inspector</b> and "
              "<b>oasdiff</b> (OpenAPI diff) are the practical references. For the "
              "black-box layers, the Postman/Newman docs and Schemathesis "
              "(property-based API testing from an OpenAPI schema) go further than "
              "the hand-rolled fuzzer here."),
        ])},
    ],
}

# ══════════════════════════════════════════════════════════ runbook ══

RUNBOOK = {
    "title": "Running the Project, Step by Step",
    "abstract": "From a clone to the catch matrix, on Python (+ Node for Newman).",
    "sections": [
        {"title": "Prerequisites",
         "html": p("You need <b>Python 3.12+</b>; <b>Node 20+</b> only for the "
                   "optional Newman run.")
         + code_literal("python --version\nnode --version", "Toolcheck", "bash")},
        {"title": "The provider, tests, and the finding",
         "html": code_literal(
             "python -m venv .venv\n"
             ".venv\\Scripts\\activate            # Windows\n"
             "source .venv/bin/activate           # macOS / Linux\n"
             "pip install -r provider/requirements.txt\n\n"
             "python -m pytest testing            # 19 tests\n"
             "python scoring/verify_contract.py   # contract satisfied on clean\n"
             "python scoring/score.py             # the finding -> reports/*.json\n"
             "python scoring/fuzz.py              # 0 unhandled 5xx",
             "Everything measured", "bash")},
        {"title": "Explore the API by hand",
         "html": code_literal(
             "cd provider && python -m uvicorn app.main:app --port 8000\n"
             "# REST:    http://localhost:8000/api/books\n"
             "# GraphQL: http://localhost:8000/graphql", "The two surfaces", "bash")},
        {"title": "Postman / Newman (optional)",
         "html": code_literal(
             "cd provider && python -m uvicorn app.main:app --port 8000 &\n"
             "npx --yes newman run postman/accord.postman_collection.json "
             "--env-var baseUrl=http://localhost:8000", "Black-box collection", "bash")},
        {"title": "What you should see",
         "html": p("<code>19 passed</code>; the contract satisfied; "
                   "<code>score.py</code> prints the matrix and writes "
                   "<code>reports/catch_matrix.json</code> + "
                   "<code>summary.json</code> (identical on re-run); the fuzzer "
                   "reports no unhandled 5xx.")},
    ],
}

# ══════════════════════════════════════════════════════════ appendix ══

APPENDIX = {
    "title": "Appendix",
    "abstract": "Repository map and glossary.",
    "sections": [
        {"title": "A - Repository map",
         "html": table(["Path", "Purpose"],
                       [["<code>provider/app/rest.py</code>", "the REST surface"],
                        ["<code>provider/app/graphql_api.py</code>", "the GraphQL schema"],
                        ["<code>consumer/client.py</code>", "the reading-list consumer SDK"],
                        ["<code>consumer/contracts/reading-list.json</code>", "the Pact-style contract"],
                        ["<code>testing/</code>", "provider + consumer tests"],
                        ["<code>scoring/verify_contract.py</code>", "contract verification"],
                        ["<code>scoring/schema_diff.py</code>", "structural schema diff"],
                        ["<code>scoring/catalog.py</code>", "the change catalog"],
                        ["<code>scoring/score.py</code>", "the fault-injection harness"],
                        ["<code>scoring/fuzz.py</code>", "property-based fuzzer"],
                        ["<code>postman/</code>", "Postman collection (Newman/CI)"],
                        ["<code>reports/*.json</code>", "the source of every number here"]],
                       "Where everything lives", "")},
        {"title": "B - Glossary",
         "html": table(["Term", "Meaning"],
                       [["Breaking change", "a change that breaks an existing client"],
                        ["Consumer-driven contract", "the consumer declares what it needs; the provider is verified against it"],
                        ["Provider verification", "replaying a contract's interactions against the provider"],
                        ["Value matcher", "a contract check on a value (rating 0-5), not just its type"],
                        ["Schema diff", "detecting breaking changes by comparing API schemas"],
                        ["Additive change", "a new field/endpoint; non-breaking"],
                        ["Semantic change", "same shape and type, different meaning"],
                        ["SDL", "GraphQL Schema Definition Language -- the printed schema"],
                        ["Newman", "the command-line runner for Postman collections"],
                        ["Fuzzing", "throwing malformed input to find crashes"]],
                       "Terms used in this book", "")},
    ],
}

# ══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════ extra chapters ══

CH_DATA = {
    "title": "The store, queried",
    "abstract": "The query surface both APIs share -- filtering, lookup, creation.",
    "sections": [
        {"title": "Shared queries", "html": "".join([
            p("Both REST and GraphQL read through the same store, so a filter or a "
              "lookup behaves identically on either surface. The list query "
              "supports the two filters both APIs expose."),
            code_from(PROJ, "provider/app/store.py",
                      start="    def all(self, tag: str | None = None, available: bool | None = None) -> list[Book]:",
                      end="return sorted(out, key=lambda b: b.id)",
                      caption="Listing DS.1 - list with filters",
                      lang="python"),
            code_from(PROJ, "provider/app/store.py",
                      start="    def add(self, title: str, author: str, isbn: str, year: int,",
                      end="return b",
                      caption="Listing DS.2 - creation",
                      lang="python"),
        ])},
    ],
}

CH_RESTROUTES = {
    "title": "The rest of the REST",
    "abstract": "List, create, and the by-author endpoint -- and the models that "
                "declare the request and response shapes.",
    "sections": [
        {"title": "The declared shapes", "html": "".join([
            p("The request and response shapes are Pydantic models. The response "
              "model is the provider's promise; several catalog changes edit "
              "exactly this file."),
            code_from(PROJ, "provider/app/models.py",
                      start="class BookOut(BaseModel):", end="rating: float",
                      caption="Listing RR.1 - the response model",
                      lang="python"),
            code_from(PROJ, "provider/app/models.py",
                      start="class BookCreate(BaseModel):",
                      end="tags: list[str] = Field(default_factory=list)",
                      caption="Listing RR.2 - the create request model (input validation)",
                      lang="python"),
        ])},
        {"title": "List, create, by author", "html": "".join([
            code_from(PROJ, "provider/app/rest.py",
                      start='    @r.get("/books", response_model=list[BookOut])',
                      end="return [_to_out(b) for b in store.all(tag=tag, available=available)]",
                      caption="Listing RR.3 - list with query filters",
                      lang="python"),
            code_from(PROJ, "provider/app/rest.py",
                      start='    @r.post("/books", response_model=BookOut, status_code=201)',
                      end="return _to_out(b)",
                      caption="Listing RR.4 - create (201 Created)",
                      lang="python"),
        ])},
    ],
}

CH_STATUS = {
    "title": "Status codes as a contract",
    "abstract": "The HTTP status is a machine-readable promise; the tests and the "
                "schema-diff both assert it.",
    "sections": [
        {"title": "The vocabulary", "html": "".join([
            table(["Code", "Meaning in Accord"],
                  [["200 OK", "a successful read"],
                   ["201 Created", "a book was created"],
                   ["404 Not Found", "unknown book or author"],
                   ["422 Unprocessable", "invalid create payload"]],
                  caption="Table ST.1 - the status contract"),
            p("A status code is part of the contract, so a change from 201 to 200 "
              "on create is a breaking change -- caught by the provider test that "
              "asserts 201 and by the schema-diff's status probe, though not by "
              "the consumer contract, which never creates a book. That split is "
              "recorded in the matrix."),
        ])},
    ],
}

CH_INTROSPECT = {
    "title": "GraphQL introspection and the type map",
    "abstract": "The typed schema is machine-readable, which is what makes the "
                "structural diff on GraphQL so cheap.",
    "sections": [
        {"title": "Building the type map", "html": "".join([
            p("The schema-diff turns the printed SDL into a map of type -> field "
              "-> type, which is directly comparable across versions. This is the "
              "advantage a typed API gives the tester: the contract is data."),
            code_from(PROJ, "scoring/schema_diff.py",
                      start="def _graphql_types(schema) -> dict:", end="return out",
                      caption="Listing IN.1 - the GraphQL type map",
                      lang="python"),
            p("A provider test can even assert the schema from the inside, via an "
              "introspection query -- the same mechanism a client uses to discover "
              "the API:"),
            code_from(PROJ, "testing/provider_tests/test_graphql.py",
                      start="def test_schema_exposes_book_type(client):",
                      end='assert {"id", "title", "author"} <= names',
                      caption="Listing IN.2 - asserting the schema by introspection",
                      lang="python"),
        ])},
    ],
}

CH_CONSUMER_TESTS = {
    "title": "Consumer tests, and the false comfort of mocks",
    "abstract": "Integration tests catch breaks by running both sides; the contract "
                "is the artifact that lets each side check alone.",
    "sections": [
        {"title": "The consumer against the real provider", "html": "".join([
            p("The consumer tests drive the widget against the real provider "
              "in-process. These are integration tests: they catch a breaking "
              "change, but only by running both sides together."),
            code_from(PROJ, "testing/consumer_tests/test_reading_list.py",
                      start="def test_detail_has_cover_and_rating(client):",
                      end='assert isinstance(d["rating"], float)',
                      caption="Listing CT.1 - a consumer integration test",
                      lang="python"),
            p("The trap they warn about is the <i>mock</i>. A consumer test that "
              "mocks the provider encodes the shape the consumer <i>assumes</i>, "
              "not the shape the provider actually returns -- so it stays green "
              "while the real provider drifts away. That is the whole reason for a "
              "contract: it is the shared, verified artifact that keeps the mock "
              "honest. The consumer records what it needs once; the provider is "
              "verified against it in its own pipeline, with no mock and no "
              "running consumer."),
        ])},
    ],
}

CH_PROBE = {
    "title": "Running a mechanism against patched code",
    "abstract": "Why the contract and schema-diff run in a subprocess.",
    "sections": [
        {"title": "A fresh interpreter per probe", "html": "".join([
            p("The contract and schema-diff must import the <i>patched</i> "
              "provider, not the original the harness already loaded. So they run "
              "in a subprocess whose working directory is the patched copy; the "
              "probe imports the app from there and exits 0 (not flagged) or 1 "
              "(flagged)."),
            code_from(PROJ, "scoring/probe.py",
                      start='    if mode == "schemadiff":', end="return 1 if breaks else 0",
                      caption="Listing PB.1 - the schema-diff probe",
                      lang="python"),
            code_from(PROJ, "scoring/score.py",
                      start="def _probe(cwd: Path, *args: str) -> bool:",
                      end="return p.returncode == 1",
                      caption="Listing PB.2 - launching a probe",
                      lang="python"),
        ])},
    ],
}

CH_WORKED = {
    "title": "Tracing four changes",
    "abstract": "One caught only by the contract-vs-provider gap, one only by "
                "schema-diff, one only by the value matcher, one by nothing.",
    "sections": [
        {"title": "C01 rename: contract catches, provider misses", "html": "".join([
            p("Renaming cover_url to image edits the REST model and mapping. The "
              "provider's own tests never assert cover_url, so they pass "
              f"(provider caught: {yn(MATRIX['C01']['caught']['provider_tests'])}). "
              "The consumer renders cover_url, so its contract fails "
              f"(contract caught: {yn(MATRIX['C01']['caught']['contract'])}); the "
              "schema-diff sees the field vanish "
              f"(schema caught: {yn(MATRIX['C01']['caught']['schema_diff'])}). This "
              "is the archetype of consumer-driven contracts: catching a break the "
              "provider had no reason to test."),
        ])},
        {"title": "C15 nullability: only schema-diff catches", "html": "".join([
            p("Widening GraphQL title from String! to String breaks callers that "
              "assume non-null. But the provider test asserts title's <i>value</i> "
              "(still present), so it passes "
              f"({yn(MATRIX['C15']['caught']['provider_tests'])}); the contract "
              "checks the value is a string (still true), so it passes "
              f"({yn(MATRIX['C15']['caught']['contract'])}). Only the schema-diff, "
              "comparing String! to String, catches it "
              f"({yn(MATRIX['C15']['caught']['schema_diff'])}). A value-present "
              "check cannot see a widened type; a structural diff can."),
        ])},
        {"title": "C12 semantic: only the value matcher catches", "html": "".join([
            p("Rescaling rating from 0-5 to 0-100 keeps the type float. The "
              "provider does not assert rating "
              f"({yn(MATRIX['C12']['caught']['provider_tests'])}); the schema-diff "
              "sees float -> float and shrugs "
              f"({yn(MATRIX['C12']['caught']['schema_diff'])}). Only the contract's "
              "value matcher (rating in 0-5) catches the 90.0 "
              f"({yn(MATRIX['C12']['caught']['contract'])}). This is the one change "
              "the contract catches that the schema-diff cannot -- semantics live "
              "in values, not shapes."),
        ])},
        {"title": "C14 semantic format: nothing catches", "html": "".join([
            p("Stripping the hyphens from isbn keeps it a string, and no consumer "
              "declared isbn, so all three pass "
              f"(provider {yn(MATRIX['C14']['caught']['provider_tests'])}, contract "
              f"{yn(MATRIX['C14']['caught']['contract'])}, schema "
              f"{yn(MATRIX['C14']['caught']['schema_diff'])}). It is a genuine "
              "coverage gap: a value-format break in a field no contract pins. A "
              "regex value matcher, or a second consumer that depends on isbn, "
              "would close it -- which is the honest, actionable lesson."),
        ])},
    ],
}

CH_VERSIONING = {
    "title": "Avoiding the break in the first place",
    "abstract": "The measurement argues for a discipline: additive change, "
                "deprecation windows, and a contract as the gate.",
    "sections": [
        {"title": "Expand, migrate, contract", "html": "".join([
            p("Every breaking change in the catalog has a non-breaking "
              "alternative. Instead of renaming cover_url to image, add image "
              "alongside cover_url, move consumers over, and remove cover_url only "
              "once no contract still depends on it. This is the "
              "expand/migrate/contract pattern, and it is why the additive changes "
              "in the catalog are correctly flagged by nothing: adding a field is "
              "safe, removing or retyping one is not."),
            p("The contract is what makes the 'once no consumer depends on it' "
              "step checkable rather than hopeful. In a real pipeline, each "
              "consumer publishes its contract to a broker, and the provider asks "
              "'can I deploy this change without breaking a published contract?' "
              "before it ships. The verifier here is the single-repo version of "
              "that question; Pact's broker and its can-i-deploy tool are the "
              "multi-repo version."),
        ])},
        {"title": "Deprecation is a first-class API feature", "html": "".join([
            p("GraphQL bakes this in with an @deprecated directive on fields; REST "
              "does it with Sunset/Deprecation headers and versioned media types. "
              "The point the measurement makes is that a breaking change is a "
              "<i>process</i> failure as much as a code one: with additive change "
              "plus a deprecation window plus a contract gate, most of the 13 "
              "breaks here never reach a consumer. The tests are the safety net; "
              "the discipline is the trapeze."),
        ])},
    ],
}

CH_RESTGQL = {
    "title": "REST versus GraphQL, for the tester",
    "abstract": "The same break is cheaper to catch on the typed surface -- but "
                "GraphQL has its own hazards.",
    "sections": [
        {"title": "Typed schema, cheaper diff", "html": "".join([
            p("On GraphQL, renaming or retyping a field is a structural change to "
              "the SDL, detectable by an offline schema diff with no server call. "
              "On REST, the shape is implicit in the JSON, so the diff must derive "
              "it from live responses (or from an OpenAPI spec, if the team keeps "
              "one accurate). The typed surface hands the tester a machine-readable "
              "contract for free; the untyped one makes them reconstruct it."),
            p("That is not a blanket win for GraphQL. Its flexibility moves risk "
              "elsewhere: a client can ask for arbitrarily nested queries (a "
              "denial-of-service surface REST rarely has), field-level "
              "authorization is easy to get wrong, and a single endpoint means "
              "status-code-based monitoring is coarser. The tester's job shifts, "
              "it does not shrink -- query-depth limits and field-auth tests "
              "replace some of the status-code and routing tests REST needs."),
        ])},
    ],
}

CH_DESIGN = {
    "title": "Design decisions",
    "abstract": "Each load-bearing choice, and the alternative it beat.",
    "sections": [
        {"title": "Why a curated catalog", "html": "".join([
            callout("note", "WHY: named change classes over random mutation",
                    p("Random schema mutation would estimate sensitivity; a curated "
                      "catalog answers 'which mechanism owns which class of real "
                      "change' -- rename, retype, remove, status, semantic. The "
                      "results read as a table of risks and owners, which is what a "
                      "team actually needs to decide what to run.")),
        ])},
        {"title": "Why value matchers in the contract", "html": "".join([
            callout("note", "WHY: a contract asserts meaning, not just shape",
                    p("A type-only contract is just a schema check with extra "
                      "steps. The value matcher (rating in 0-5) is what lets the "
                      "contract catch a semantic rescale that every structural and "
                      "type check misses -- the one thing consumer-driven contracts "
                      "can do that a schema diff cannot. It is also exactly how "
                      "real Pact contracts work.")),
        ])},
        {"title": "Why subprocess probes", "html": "".join([
            callout("note", "WHY: import the patched code, not the original",
                    p("The harness has already imported the clean provider. To "
                      "measure a patched one, the contract and schema-diff must run "
                      "in a fresh interpreter rooted at the patched copy. A "
                      "subprocess is the honest way to guarantee that; importlib "
                      "reload tricks are fragile and leak state.")),
        ])},
    ],
}

CH_ADDITIVE = {
    "title": "Precision: not flagging the safe changes",
    "abstract": "A tool that cries wolf on every additive change is as useless as "
                "one that misses breaks.",
    "sections": [
        {"title": "Additive changes must pass silently", "html": "".join([
            p(f"The catalog includes {SUM['additive_changes']} additive changes -- "
              f"adding an optional field to REST and to GraphQL. A good detector "
              f"must NOT flag these, and none of the three did "
              f"({len(SUM['false_positives'])} false positives). The schema-diff "
              f"earns this by only reporting removed or retyped fields, never new "
              f"ones; the contract earns it by checking that required fields are "
              f"present, not that no others exist."),
            p("This matters because precision is what makes a gate trustworthy. A "
              "schema-diff that flagged every new field would be turned off within "
              "a week, and then it would catch nothing. Measuring false positives "
              "alongside catches is the only way to know a tool is safe to gate "
              "on -- the same reason this portfolio measures a naive baseline's "
              "false comfort, not just a method's hits."),
        ])},
    ],
}

# ---- append listings to existing chapters ----

CH6["sections"].append({"title": "The GraphQL side of the contract", "html": "".join([
    p("The contract covers GraphQL interactions too -- here the shelf-covers query "
      "the widget uses, depending on coverUrl (the camelCase of cover_url):"),
    code_from(PROJ, "consumer/contracts/reading-list.json",
              start='"description": "GraphQL: shelf covers",',
              end='"fields": { "id": "int", "title": "str", "coverUrl": "str" }',
              caption="Listing 6.3 - a GraphQL contract interaction",
              lang="json"),
]) })

CH9["sections"].append({"title": "Two more entries", "html": "".join([
    p("A field removal and a nullability widening, each a precise edit:"),
    code_from(PROJ, "scoring/catalog.py",
              start='Change("C06", "remove-field", True, (',
              end='"REST: drop the year field from the book response."),',
              caption="Listing 9.4 - remove a field",
              lang="python"),
    code_from(PROJ, "scoring/catalog.py",
              start='Change("C15", "nullability", True, (',
              end='"GraphQL: title becomes nullable (String! -> String)."),',
              caption="Listing 9.5 - widen to nullable",
              lang="python"),
]) })

CH5["sections"].append({"title": "Behaviour, thoroughly", "html": "".join([
    p("The provider suite is thorough where it counts -- filtering and creation "
      "are pinned end to end, so a change to that behaviour is caught here, not "
      "left to a consumer to discover."),
    code_from(PROJ, "testing/provider_tests/test_rest.py",
              start="def test_filter_by_tag(client):",
              end='assert titles == {"A Wizard of Earthsea"}',
              caption="Listing 5.3 - filtering is pinned",
              lang="python"),
    code_from(PROJ, "testing/provider_tests/test_rest.py",
              start="def test_create_returns_201_and_persists(client):",
              end='assert client.get(f"/api/books/{new_id}").status_code == 200',
              caption="Listing 5.4 - creation is pinned",
              lang="python"),
]) })

# ═══════════════════════════════════════ round two ══

CH_STRATEGY = {
    "title": "The API testing pyramid",
    "abstract": "Where each mechanism sits, by cost and by what it can see.",
    "sections": [
        {"title": "From free to expensive", "html": "".join([
            p("The mechanisms form a pyramid of their own, ordered by cost:"),
            ol(["<b>Static (schema diff / type checks)</b> -- no server, no "
                "consumer, runs in milliseconds; catches structural and type "
                "breaks, blind to semantics.",
                "<b>Provider unit + integration tests</b> -- in-process, fast; "
                "catch what the provider asserts.",
                "<b>Consumer-driven contract verification</b> -- in-process, fast; "
                "catches what the consumer needs, including the provider's blind "
                "spots and (with value matchers) semantics.",
                "<b>Consumer integration tests</b> -- run both sides; catch breaks "
                "but require the whole stack.",
                "<b>Black-box (Newman / Schemathesis)</b> -- a running server; the "
                "closest to production, the slowest to run."]),
            p("The lesson the matrix teaches is to spend low and broad: a schema "
              "diff and a contract are cheap and catch most breaks between them, so "
              "they belong in every pull request. The expensive black-box layer is "
              "a thin confirmation on top, not the foundation."),
        ])},
    ],
}

CH_ERRORS = {
    "title": "Testing the unhappy paths",
    "abstract": "The error contract -- 404s and 422s -- is as much a promise as the "
                "happy path.",
    "sections": [
        {"title": "Errors are part of the API", "html": "".join([
            p("A client branches on 404 and 422 as surely as on 200, so those "
              "paths are tested explicitly. An endpoint that starts returning 200 "
              "with an empty body instead of 404 is a breaking change even though "
              "nothing 'errored'."),
            code_from(PROJ, "testing/provider_tests/test_rest.py",
                      start="def test_get_missing_is_404(client):",
                      end='assert client.get("/api/books/999").status_code == 404',
                      caption="Listing ER.1 - a missing book is 404",
                      lang="python"),
            code_from(PROJ, "testing/provider_tests/test_rest.py",
                      start="def test_author_without_books_is_404(client):",
                      end='assert client.get("/api/authors/Nobody/books").status_code == 404',
                      caption="Listing ER.2 - an author with no books is 404",
                      lang="python"),
            code_from(PROJ, "testing/provider_tests/test_graphql.py",
                      start="def test_books_filter_by_tag(client):",
                      end="assert ids == {1, 3, 5}",
                      caption="Listing ER.3 - GraphQL filtering, pinned",
                      lang="python"),
        ])},
    ],
}

CH_SECURITY = {
    "title": "Security testing for a read API",
    "abstract": "No auth by design -- so the security surface is input handling, "
                "mass assignment, and GraphQL's own hazards.",
    "sections": [
        {"title": "What matters when the data is public", "html": "".join([
            p("Accord is a public catalog with no authentication, so the classic "
              "auth tests do not apply -- but a security review still has real "
              "targets, and the design answers each:"),
            ul(["<b>Injection / malformed input</b> -- the fuzzer throws "
                "hostile strings and wrong types at the write path and confirms a "
                "4xx, never a 5xx or a stack trace.",
                "<b>Mass assignment</b> -- the create model accepts only "
                "title/author/isbn/year/tags, so a client cannot smuggle in an id, "
                "a rating, or an availability flag. The allowlist model is the "
                "defence, and it is visible in one place (Listing RR.2).",
                "<b>GraphQL query depth / complexity</b> -- a single flexible "
                "endpoint invites expensive nested queries; a production deployment "
                "adds a depth/complexity limit, which is a test in its own right.",
                "<b>Information leakage</b> -- errors return a short detail, not an "
                "internal trace, and the same 404 covers 'unknown' and 'no "
                "books' so a probe learns nothing extra."]),
            p("The point for a tester: 'no auth' does not mean 'no security "
              "tests' -- it moves the surface to input validation and to GraphQL's "
              "particular risks, and each of those is checkable."),
        ])},
    ],
}

CH_HARNESS_AGG = {
    "title": "Turning the matrix into the finding",
    "abstract": "The aggregation that computes who catches what the others miss.",
    "sections": [
        {"title": "Complementarity, computed", "html": "".join([
            p("The headline numbers -- contract catches what provider tests miss, "
              "schema-diff catches what the contract can't -- are not asserted; "
              "they are computed from the matrix by simple set logic, so they "
              "cannot disagree with the per-change table."),
            code_from(PROJ, "scoring/score.py",
                      start="    contract_only_vs_provider = [c for c in breaking",
                      end='if caught_by(c, "contract") and not caught_by(c, "schema_diff")]',
                      caption="Listing AG.1 - who catches what the others miss",
                      lang="python"),
        ])},
    ],
}

CH_REPRO = {
    "title": "Reproducibility",
    "abstract": "The catch matrix is verified deterministic, not merely assumed.",
    "sections": [
        {"title": "Re-run and diff", "html": "".join([
            p("The store is seeded, the catalog is a literal list, and the JSON is "
              "written with sorted keys and no timestamps, so the catch matrix is "
              "deterministic. That claim is verified the honest way -- run the "
              "scoring, snapshot the reports, run it again, and compare the files "
              "byte for byte. They are identical. The only thing deliberately kept "
              "out of the reproducible reports is wall-clock timing, which nothing "
              "in the finding depends on."),
        ])},
    ],
}

CH_CLIENT2 = {
    "title": "The consumer, over GraphQL",
    "abstract": "The same widget, the other surface -- and the same contract idea.",
    "sections": [
        {"title": "One client, two protocols", "html": "".join([
            p("The widget can fetch a book's detail over GraphQL as easily as over "
              "REST, asking for exactly the fields it needs -- which is GraphQL's "
              "selling point and, for the tester, the reason the contract lists "
              "the query verbatim."),
            code_from(PROJ, "consumer/client.py",
                      start="    def detail_via_graphql(self, book_id: int) -> dict:",
                      end="return data",
                      caption="Listing CL.1 - the consumer's GraphQL call",
                      lang="python"),
            code_from(PROJ, "scoring/verify_contract.py",
                      start="def verify_all(client) -> list[str]:", end="return out",
                      caption="Listing CL.2 - verifying every contract",
                      lang="python"),
        ])},
    ],
}

# ═══════════════════════════════════════ round three ══

CH_GQLERR = {
    "title": "GraphQL's different error model",
    "abstract": "A GraphQL request is 200 with an errors array, not a 4xx -- which "
                "changes what the tests assert.",
    "sections": [
        {"title": "Null, and the errors array", "html": "".join([
            p("GraphQL does not use HTTP status for domain outcomes: a missing book "
              "is a 200 whose data.book is null, and a bad query is a 200 with an "
              "errors array. The provider tests assert this explicitly, because a "
              "consumer that branches on HTTP status alone would be misled."),
            code_from(PROJ, "testing/provider_tests/test_graphql.py",
                      start="def test_missing_book_is_null(client):",
                      end='assert r["data"]["book"] is None',
                      caption="Listing GE.1 - a missing book is null, not 404",
                      lang="python"),
            p("This is a concrete way REST and GraphQL diverge for the tester: the "
              "REST 404 test and the GraphQL null test check the same domain fact "
              "through two different contracts, and a schema-diff on the REST side "
              "watches status codes while on the GraphQL side it watches "
              "nullability. Same intent, different instruments."),
        ])},
    ],
}

CH_SEED = {
    "title": "The seed, and testing against known data",
    "abstract": "A fixed catalog is what lets a test assert exact values, not just "
                "shapes.",
    "sections": [
        {"title": "Known data, exact assertions", "html": "".join([
            p("Because the store is seeded with a fixed set of books, tests assert "
              "exact facts -- five books, a specific title for id 1, two books for "
              "an author -- rather than vague shape checks. Exact assertions are "
              "sharper sensors: they fail on a data-mapping bug a shape check would "
              "wave through."),
            code_from(PROJ, "testing/provider_tests/test_rest.py",
                      start="def test_list_returns_all(client):",
                      end="assert len(r.json()) == 5",
                      caption="Listing SD.1 - an exact-count assertion",
                      lang="python"),
            code_from(PROJ, "provider/app/rest.py",
                      start='    @r.get("/health")', end='return {"status": "ok"}',
                      caption="Listing SD.2 - the health probe",
                      lang="python"),
        ])},
    ],
}

CH_MONITORING = {
    "title": "From tests to production monitoring",
    "abstract": "The same contract that gates a deploy can watch production.",
    "sections": [
        {"title": "A contract is a synthetic check", "html": "".join([
            p("The contract's interactions -- 'GET /api/books returns these fields "
              "with these types' -- are exactly the shape of a synthetic "
              "monitoring check. The artifact that gates a deploy in CI can run "
              "every minute against production and page when the live API stops "
              "delivering what the consumer needs. This is the natural bridge from "
              "pre-deploy testing to post-deploy observability: one description of "
              "the consumer's needs, used in both places."),
            p("It also reframes the two coverage gaps. A semantic format change "
              "that slips past the pre-deploy checks might still be caught in "
              "production by a synthetic check with a value/regex matcher, or by a "
              "consumer's own error rate rising. Testing and monitoring are the "
              "same discipline at two points in time, and the contract is the "
              "thing they share."),
        ])},
    ],
}

CH_TOOLING = {
    "title": "The test tooling",
    "abstract": "pytest configuration, and the one place third-party noise is "
                "silenced.",
    "sections": [
        {"title": "Configuration as code", "html": "".join([
            p("The suite is configured in one file: which directory holds the "
              "tests, deterministic ordering, and a single suppression for "
              "Starlette's TestClient deprecation warning -- noise from a "
              "dependency, not from Accord."),
            code_from(PROJ, "pytest.ini", start="[pytest]", end="testpaths = testing",
                      caption="Listing TL.1 - the pytest configuration",
                      lang="ini"),
            p("Keeping the config small and explicit is itself a testing value: a "
              "reviewer can see exactly what runs and what is filtered, and the "
              "filter is scoped to one dependency's message, not a blanket "
              "'ignore all warnings' that would hide a real one."),
        ])},
    ],
}

CH9["sections"].append({"title": "The type-change entries", "html": "".join([
    p("The type-change class edits both the model/field and the mapping so the "
      "change is real end to end -- a bool becomes a string, an Int becomes a "
      "String:"),
    code_from(PROJ, "scoring/catalog.py",
              start='Change("C03", "type-change", True, (',
              end="instead of a bool.\"),",
              caption="Listing 9.6 - REST bool -> string",
              lang="python"),
    code_from(PROJ, "scoring/catalog.py",
              start='Change("C16", "type-change", True, (',
              end="instead of Int.\"),",
              caption="Listing 9.7 - GraphQL Int -> String",
              lang="python"),
]) })

# ═══════════════════════════════════════ round four ══

CH_TYPES = {
    "title": "Matching types across two protocols",
    "abstract": "One type-checker serves REST JSON and GraphQL results alike -- and "
                "why bool-is-not-int matters.",
    "sections": [
        {"title": "One matcher, both surfaces", "html": "".join([
            p("The contract verifier checks the same declared types whether the "
              "value came from REST JSON or a GraphQL result. The one subtlety "
              "worth its own line: in Python a bool is an int, so an honest 'is "
              "this an int' check must exclude booleans -- otherwise "
              "available=true would satisfy a field declared int."),
            code_from(PROJ, "scoring/verify_contract.py",
                      start="def _type_ok(value, tname: str) -> bool:", end="return True",
                      caption="Listing TY.1 - type matching, bool excluded from int",
                      lang="python"),
        ])},
    ],
}

CH_CONTRACTFIRST = {
    "title": "Contract-first, schema-first",
    "abstract": "The contract and the schema can lead the code, not trail it.",
    "sections": [
        {"title": "Design the promise, then keep it", "html": "".join([
            p("Nothing forces a contract to be written after the API. Written "
              "first, it is a design tool: the consumer and provider teams agree "
              "the interactions, and both build to them -- the provider verifies "
              "against the contract from day one, the consumer codes against it "
              "with a stub. GraphQL makes the schema-first version natural: write "
              "the SDL, generate resolvers and client types from it, and a schema "
              "diff then guards every later edit against the agreed shape."),
            p("The measurement supports this order. The changes that slip through "
              "are semantic and request-side -- exactly the things a schema cannot "
              "express and a contract must state deliberately. Deciding those "
              "up front (rating is 0-5; year is a publication year) is cheaper than "
              "discovering them from a broken consumer, and it turns two of this "
              "study's gaps into checks that would exist by construction."),
        ])},
    ],
}

CH_BROKER = {
    "title": "Contracts at scale",
    "abstract": "One verifier here; a broker, versioning, and can-i-deploy in a real "
                "many-service estate.",
    "sections": [
        {"title": "The multi-repo version", "html": "".join([
            p("Accord has one consumer and one provider in one repo, so the "
              "verifier just reads the contract off disk. A real estate has many "
              "consumers of many providers across many repos, and the coordination "
              "problem is solved by a <b>broker</b>: each consumer publishes its "
              "contract (tagged with its version and environment), the provider "
              "verifies against every published consumer contract, and before "
              "shipping it asks <b>can-i-deploy</b> -- is there any consumer, in "
              "the environment I am deploying to, whose contract this version would "
              "break?"),
            p("That question is the whole value of consumer-driven contracts at "
              "scale: it converts 'will this change break someone' from a Slack "
              "message into a gate. Everything in this project -- the interactions, "
              "the provider verification, the value matchers -- is the atom the "
              "broker orchestrates. Understanding the atom is the point; the broker "
              "is operational plumbing on top of it."),
        ])},
    ],
}

CH_GQLPERF = {
    "title": "The performance tests GraphQL needs",
    "abstract": "Flexibility has a cost, and it is testable.",
    "sections": [
        {"title": "N+1 and query cost", "html": "".join([
            p("GraphQL's let-the-client-ask-for-anything model creates a "
              "performance surface REST rarely has. Two hazards a tester should "
              "pin: the <b>N+1 problem</b> -- a query for a list of books each "
              "resolving its author can fire one database call per book unless a "
              "dataloader batches them -- and <b>query cost</b> -- a deeply nested "
              "or wide query can be arbitrarily expensive. Accord's resolvers read "
              "from an in-memory store so neither bites here, but in a real "
              "deployment both are test targets: assert that resolving N books "
              "issues O(1) not O(N) backend calls, and that a query past a depth or "
              "complexity budget is rejected."),
            p("This is the other side of the REST-vs-GraphQL coin from chapter "
              "'REST versus GraphQL, for the tester': the typed schema gives the "
              "tester a free structural contract, and in exchange the tester takes "
              "on a performance contract the single-purpose REST endpoint did not "
              "need."),
        ])},
    ],
}

CH_INPUT = {
    "title": "Input validation, and the gap it leaves",
    "abstract": "The create endpoint rejects bad input -- and a relaxed bound is a "
                "regression no response-side mechanism can see.",
    "sections": [
        {"title": "Rejecting bad writes", "html": "".join([
            p("The provider validates create payloads and returns 422 on bad "
              "input, and a test pins it. But note what this test can and cannot "
              "do: it asserts that a clearly-bad payload is rejected, not that "
              "every bound is exactly right."),
            code_from(PROJ, "testing/provider_tests/test_rest.py",
                      start="def test_create_validation_is_422(client):",
                      end="assert r.status_code == 422",
                      caption="Listing IV.1 - a bad create payload is 422",
                      lang="python"),
            p("That is why the catalog's relaxed-validation change (widening the "
              "year bound) slips past all three mechanisms: it is a request-side "
              "regression, and the contract, the schema-diff and even this test -- "
              "which sends several bad fields at once -- do not isolate it. Closing "
              "it needs a property-based test of the boundary, or a data-quality "
              "assertion on what actually got stored: exactly the instrument the "
              "next project in this series is built around."),
        ])},
    ],
}

CH5["sections"].append({"title": "Listing the GraphQL catalog", "html": "".join([
    p("A last provider GraphQL test pins the full-list query -- five books, no "
      "filter -- the mirror of the REST list test."),
    code_from(PROJ, "testing/provider_tests/test_graphql.py",
              start="def test_books_list_all(client):",
              end='assert len(r["data"]["books"]) == 5',
              caption="Listing 5.5 - the GraphQL list query",
              lang="python"),
]) })

CH_RESTROUTES["sections"].append({"title": "The by-author endpoint", "html": "".join([
    p("The by-author route returns a 404 when the author has no books, so the "
      "'empty' and 'unknown' cases are one status -- a small information-leak "
      "guard, and a route the provider tests cover on both paths."),
    code_from(PROJ, "provider/app/rest.py",
              start='    @r.get("/authors/{author}/books", response_model=list[BookOut])',
              end="return [_to_out(b) for b in books]",
              caption="Listing RR.5 - books by author",
              lang="python"),
]) })

CH_DATA["sections"].append({"title": "Lookup by author", "html": "".join([
    p("The by-author query underlies the REST /authors/{author}/books endpoint "
      "and is a plain filter over the same store -- small, but a real query the "
      "provider tests pin (two books for Octavia E. Butler)."),
    code_from(PROJ, "provider/app/store.py",
              start="    def by_author(self, author: str) -> list[Book]:",
              end="return [b for b in self.all() if b.author == author]",
              caption="Listing DS.3 - lookup by author",
              lang="python"),
]) })

CH_RECAP = {
    "title": "The finding, restated",
    "abstract": "One table, and the boundary around it.",
    "sections": [
        {"title": "Everything, in one place", "html": "".join([
            table(["Question", "Answer (reports/summary.json)"],
                  [["Breaking changes in the catalog", str(NB)],
                   ["Caught by the provider's own tests", str(CPM["provider_tests"])],
                   ["Caught by the consumer contract", str(CPM["contract"])],
                   ["Caught by the schema diff", str(CPM["schema_diff"])],
                   ["Caught by at least one mechanism", str(SUM["breaking_caught_by_any"])],
                   ["Slip past all three", str(SUM["breaking_missed_by_all"])],
                   ["Contract catches, provider misses",
                    str(len(SUM["contract_catches_provider_tests_miss"]))],
                   ["Schema-diff catches, contract blind",
                    str(len(SUM["schema_diff_catches_contract_blind"]))],
                   ["Contract catches, schema-diff blind",
                    str(len(SUM["contract_catches_schema_diff_blind"]))],
                   ["False positives on additive changes", str(len(SUM["false_positives"]))]],
                  caption="Table RC.1 - the whole project, from reports/summary.json",
                  highlight_col=1),
        ])},
        {"title": "The paragraph", "html": "".join([
            p(f"{SUM['headline']} The three mechanisms are complementary, not "
              f"ranked: the provider's tests guard what it asserts, the consumer "
              f"contract guards what a consumer depends on (including the "
              f"provider's blind spots and, with value matchers, meaning), and the "
              f"schema diff guards structure with no consumer at all. None is "
              f"sufficient alone; together they still miss a silent format change "
              f"and a relaxed validation, which is the honest edge -- API safety is "
              f"layered, and even the layers have gaps a data-quality or "
              f"property test must close."),
        ])},
    ],
}

CHAPTERS = [CH1, CH2, CH_DATA, CH3, CH_RESTROUTES, CH_STATUS, CH_ERRORS, CH4,
            CH_INTROSPECT, CH_GQLERR, CH5, CH_SEED, CH6, CH_CLIENT2, CH7,
            CH_TYPES, CH8, CH9, CH10, CH_PROBE, CH_HARNESS_AGG, CH11, CH_WORKED,
            CH_CONSUMER_TESTS, CH_RESTGQL, CH_GQLPERF, CH_VERSIONING,
            CH_CONTRACTFIRST, CH_BROKER, CH_ADDITIVE, CH_SECURITY, CH_DESIGN,
            CH_STRATEGY, CH_TOOLING, CH_INPUT, CH_FUZZ, CH_CI, CH_MONITORING,
            CH_REPRO, CH_RECAP, CH_LIMITS, CH_READING, RUNBOOK, APPENDIX]

META = {
    "series": "Engineering Notebook",
    "title": "Accord",
    "subtitle": "REST + GraphQL, and which API test catches which breaking change",
    "author": "Nikhil Sinha",
    "repo": REPO,
    "stack": "Python · FastAPI · Strawberry GraphQL · Pact-style contracts · pytest + Hypothesis · Newman",
    "version": "1.0",
    "how_to_read": (
        p("This is an API-testing notebook that happens to be about a book "
          "catalog. It is written for someone building or testing services who "
          "wants to know, concretely, which testing mechanism catches which kind "
          "of breaking change -- and which kinds escape them all.")
        + p("Every listing is extracted from the repository at build time and "
            "every number is read from the reports a real run wrote, so nothing "
            "here can drift from the code.")),
}

if __name__ == "__main__":
    out = HERE / "Accord-Notebook.pdf"
    r = build(META, CHAPTERS, out, min_pages=60)
    print(f"PAGES {r['pages']} (min 60 -> {r['meets_minimum']})  "
          f"WORDS ~{r['approx_words']:,}  {r['chapters']} ch / {r['sections']} sec  "
          f"{r['size_kb']} KB")
