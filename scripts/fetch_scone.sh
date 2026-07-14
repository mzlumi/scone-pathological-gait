#!/usr/bin/env bash
# Download the newest Linux SCONE package built by the scone-studio CI and
# store it as vendor/scone_amd64.deb. Needs the GitHub CLI (gh) with a token,
# because GitHub only serves Actions artifacts to authenticated users.
set -euo pipefail

repo="tgeijten/scone-studio"
root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$root/vendor"

artifact_id="$(gh api "repos/$repo/actions/artifacts?per_page=50" \
  -q '[.artifacts[] | select(.name == "deb-installer.zip" and (.expired | not))][0].id')"
if [[ -z "$artifact_id" || "$artifact_id" == "null" ]]; then
  echo "No unexpired deb-installer artifact found in $repo" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
gh api "repos/$repo/actions/artifacts/$artifact_id/zip" > "$tmp/artifact.zip"
unzip -q "$tmp/artifact.zip" -d "$tmp"
mv "$tmp"/*.deb "$root/vendor/scone_amd64.deb"
echo "artifact $artifact_id -> vendor/scone_amd64.deb"
shasum -a 256 "$root/vendor/scone_amd64.deb"
