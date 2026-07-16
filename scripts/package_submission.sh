#!/usr/bin/env bash
# Build dist/SCONE_Parmida_Mazloomi.zip as the handout asks: the report as PDF,
# all SCONE setup files, and the optimization result folders without
# intermediate solutions (setup files, best solution and its evaluation).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
name="SCONE_Parmida_Mazloomi"
stage="$(mktemp -d)/$name"
trap 'rm -rf "$(dirname "$stage")"' EXIT

[[ -f "$root/docs/report/report.pdf" ]] || "$root/scripts/build_report.sh"

mkdir -p "$stage/setup" "$stage/results"
cp "$root/docs/report/report.pdf" "$stage/$name.pdf"
cp "$root"/scone/*.scone "$root"/scone/*.osim "$root"/scone/*.sto "$root"/scone/*.par "$stage/setup/"
cp -R "$root/scone/sweeps" "$stage/setup/sweeps"
for d in "$root"/results/*/; do
  [[ -f "$d/SOURCE.txt" ]] && cp -R "$d" "$stage/results/$(basename "$d")"
done

mkdir -p "$root/dist"
rm -f "$root/dist/$name.zip"
(cd "$(dirname "$stage")" && zip -qr "$root/dist/$name.zip" "$name")
echo "wrote dist/$name.zip"
unzip -l "$root/dist/$name.zip" | tail -1
