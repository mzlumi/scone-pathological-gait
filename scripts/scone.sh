#!/usr/bin/env bash
# Run sconecmd inside the Docker image.
#
#   scripts/scone.sh optimize scone/HealthyGait.scone CmaOptimizer.max_generations=50
#   scripts/scone.sh evaluate results/runs/<run>/<best>.par
#
# The repository is mounted at /work and SCONE's results folder is mapped to
# results/runs, so every optimization lands in results/runs/<run id>/.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
image="${SCONE_IMAGE:-scone-headless:latest}"
mkdir -p "$root/results/runs"

usage() {
  echo "usage: $0 {optimize <file.scone>|evaluate <file.par>} [key=value ...]" >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
mode="$1"
target="$2"
shift 2

case "$mode" in
  optimize) flag="-o" ;;
  evaluate) flag="-e" ;;
  *) usage ;;
esac

# Paths are passed to the container relative to the repository root.
abs="$(cd "$(dirname "$target")" && pwd)/$(basename "$target")"
rel="${abs#"$root"/}"
if [[ "$rel" == "$abs" ]]; then
  echo "$target must live inside $root" >&2
  exit 2
fi

run() {
  docker run --rm \
    -v "$root:/work" \
    -v "$root/results/runs:/root/SCONE/results" \
    "$image" "$flag" "/work/$rel" "$@"
}

if [[ "$mode" == "evaluate" ]]; then
  # SCONE appends ".sto" to the -r path, giving <name>.par.sto like SCONE Studio.
  # The objective breakdown printed by sconecmd is kept in <name>.par.txt.
  run -r "/work/$rel" "$@" 2>&1 | tee "$abs.txt"
else
  run -s "$@"
fi
