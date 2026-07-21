#!/usr/bin/env bash
# Regenerate the comparison and convergence figures used in the report from
# the curated results in results/<name>/.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
sg=".venv/bin/scone-gait"
fig="results/figures"

sto() { echo "results/$1/$(awk '/^best:/ {print $2}' "results/$1/SOURCE.txt").sto"; }
hist() { echo "results/$1/history.txt"; }

compare() {
  local out="$1"; shift
  local files=() labels=()
  while [[ $# -gt 0 ]]; do
    [[ -d "results/$1" ]] && { files+=("$(sto "$1")"); labels+=("$2"); }
    shift 2
  done
  "$sg" compare "${files[@]}" --labels "${labels[@]}" --out "$fig/$out"
}

convergence() {
  local out="$1"; shift
  local files=() labels=()
  while [[ $# -gt 0 ]]; do
    [[ -d "results/$1" ]] && { files+=("$(hist "$1")"); labels+=("$2"); }
    shift 2
  done
  "$sg" convergence "${files[@]}" --labels "${labels[@]}" --out "$fig/$out"
}

compare weakness_comparison.png \
  healthy "Healthy" weakness_0.70 "Force x 0.7" \
  weakness_0.50_cold "Force x 0.5" weakness_0.50_warm "Force x 0.5 (warm start)"

compare hyperreflexia_comparison.png \
  healthy "Healthy" hyperreflexia_fixed0.3 "KV = 0.3 (fixed)" \
  hyperreflexia_fixed1.0 "KV = 1.0 (fixed)" hyperreflexia_free1.0 "KV ~1.0 (handout, optimized)"

compare model_comparison.png \
  healthy "Healthy" contracture_0.95 "Tendon slack x 0.95" contracture_0.90 "Tendon slack x 0.90" \
  hyperreflexia_fixed1.0 "Hyperreflexia KV = 1.0"

compare crouch_comparison.png \
  healthy "Healthy" crouch_hamstrings_0.95_warm "Hamstrings x 0.95" \
  crouch_hamstrings_iliopsoas_0.95_warm "Hamstrings and iliopsoas x 0.95"

convergence convergence.png \
  healthy "Healthy" weakness_0.50_cold "Weakness x 0.5" weakness_0.70 "Weakness x 0.7" \
  hyperreflexia_fixed1.0 "Hyperreflexia KV = 1.0" hyperreflexia_free1.0 "Hyperreflexia (handout)" \
  contracture_0.90 "Plantarflexor contracture x 0.90" \
  crouch_hamstrings_iliopsoas_0.95_warm "Hip and knee flexor contracture (warm)"

echo "figures written to $fig"
