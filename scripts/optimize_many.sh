#!/usr/bin/env bash
# Start several optimizations side by side, each limited to a share of the cores.
#
#   scripts/optimize_many.sh <threads> <generations> scenario.scone [scenario.scone ...]
#
# Each run logs to logs/<scenario name>.log and writes its results to
# results/runs/<run id>/ through scripts/scone.sh.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
[[ $# -ge 3 ]] || { echo "usage: $0 <threads> <generations> scenario.scone..." >&2; exit 2; }
threads="$1"
generations="$2"
shift 2

mkdir -p "$root/logs"
for scenario in "$@"; do
  name="$(basename "$scenario" .scone)"
  nohup "$root/scripts/scone.sh" optimize "$scenario" \
    "CmaOptimizer.max_threads=$threads" "CmaOptimizer.max_generations=$generations" \
    > "$root/logs/$name.log" 2>&1 &
  echo "started $name (pid $!)"
  sleep 2
done
