#!/usr/bin/env bash
# What Codespaces runs on attach: a stranger opening this repo sees the real
# measurement -- which API-testing mechanism catches which breaking change --
# not a README claiming it. Python only for the headline; Node only for Newman.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=============================================================="
echo " Accord - REST + GraphQL, and which API test catches what"
echo "=============================================================="

echo
echo "[1/4] provider deps"
pip install -q -r provider/requirements.txt

echo
echo "[2/4] provider + consumer tests, and the consumer contract"
python -m pytest testing
python scoring/verify_contract.py

echo
echo "[3/4] fault injection: score provider-tests vs contract vs schema-diff"
python scoring/score.py

echo
echo "[4/4] fuzz the create endpoint"
python scoring/fuzz.py

echo
echo "=============================================================="
echo " Provider tests catch changes they assert; consumer contracts"
echo " catch what the consumer needs (incl. breaks the provider never"
echo " tested); schema-diff catches structural breaks with no consumer"
echo " -- and semantic breaks slip past all three. Numbers in"
echo " reports/*.json. Postman/Newman: see RUN.md."
echo "=============================================================="
