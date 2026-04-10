#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/2] Running backend tests"
(
  cd "$ROOT_DIR/backend"
  python3 -m pytest -q
)

echo "[2/2] Building frontend"
(
  cd "$ROOT_DIR/frontend"
  npm ci
  npm run build
)

echo "Validation passed"
