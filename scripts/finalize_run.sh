#!/usr/bin/env bash
# Evaluate the best solution of an optimization, analyze its gait and copy the
# run into results/<name>/ in the submission layout.
#
#   scripts/finalize_run.sh results/runs/<run id> <name> [best.par]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
[[ $# -ge 2 ]] || { echo "usage: $0 <run folder> <name> [best.par]" >&2; exit 2; }
run="$(cd "$1" && pwd)"
name="$2"
py="$root/.venv/bin/python"

if [[ $# -ge 3 ]]; then
  best="$run/$(basename "$3")"
else
  best="$("$py" -c "import sys; from scone_gait.results import best_result; print(best_result(sys.argv[1]))" "$run")"
fi
echo "best solution: $(basename "$best")"

"$root/scripts/scone.sh" evaluate "$best" | grep -E "^\S+ +(result|  )" || true
"$py" -c "import sys; from scone_gait.curate import curate_run; curate_run(sys.argv[1], sys.argv[2], sys.argv[3])" \
  "$run" "$root/results/$name" "$best"
"$root/.venv/bin/scone-gait" analyze "$root/results/$name/$(basename "$best").sto" \
  --out "$root/results/figures" --name "$name"
