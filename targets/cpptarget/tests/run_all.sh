#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "KAVACH C++ benchmark: $ROOT"
for d in "$ROOT"/0*; do
  [[ -x "$d/run.sh" ]] || continue
  echo "============================================================"
  echo "CASE: $(basename "$d")"
  "$d/run.sh" || true
done
