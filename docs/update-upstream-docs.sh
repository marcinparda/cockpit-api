#!/usr/bin/env bash
set -e

DOCS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Fetching Vikunja OpenAPI spec..."
curl -sf "https://raw.githubusercontent.com/go-vikunja/vikunja/main/pkg/swagger/swagger.json" \
  -o "$DOCS_DIR/vikunja.openapi.json"
echo "  -> vikunja.openapi.json ($(wc -c < "$DOCS_DIR/vikunja.openapi.json") bytes)"

echo "Fetching Actual Budget HTTP API spec (from raspberry via SSH)..."
ssh ssh.parda.me "curl -sf http://localhost:5007/api-docs/swagger.json" \
  > "$DOCS_DIR/actual-budget.openapi.json"
echo "  -> actual-budget.openapi.json ($(wc -c < "$DOCS_DIR/actual-budget.openapi.json") bytes)"

echo "Done."
