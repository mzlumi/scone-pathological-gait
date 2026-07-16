#!/usr/bin/env bash
# Build docs/report/report.pdf from docs/report/report.md (needs pandoc and xelatex).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root/docs/report"
pandoc report.md \
  --pdf-engine=xelatex \
  --resource-path=.:../.. \
  -V mainfont="Helvetica Neue" \
  -V linkcolor=blue \
  -o report.pdf
echo "wrote docs/report/report.pdf"
