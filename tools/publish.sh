#!/bin/bash
# Manual workflow only. Push the exact image IDs that passed that run's tests.
set -euo pipefail
cd "$(dirname "$0")/.."
test "${GITHUB_EVENT_NAME:-}" = workflow_dispatch
test "${GITHUB_REPOSITORY:-}" = moorwald/mautic4-legacy
test "${GITHUB_REF:-}" = refs/heads/main
python3 tools/check_release.py
REVISION="$(git rev-parse HEAD)"
python3 tools/check_registry_tags.py
TAG=v4.4.13-php74-r1
test -s artifacts/source-handoff/source-bundle.tar
test -s artifacts/source-handoff/source-manifest.json
(cd artifacts/source-handoff && sha256sum -c SHA256SUMS)
# Bind corresponding sources to this commit AND the current tested image IDs.
python3 - <<'PY'
import json, subprocess
manifest = json.load(open("artifacts/source-handoff/source-manifest.json"))
assert manifest["source_revision"] == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
for variant, record in manifest["images"].items():
    current = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", record["reference"]], text=True).strip()
    assert current == record["id"], "Image changed after source collection"
PY
# Check both revisions before uploading either member of the pair.
for variant in apache fpm; do
    local_image="moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    actual="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$local_image")"
    test "$actual" = "$REVISION"
done
# Preserve corresponding source availability before distributing the image pair.
gh release create "$TAG" --repo "$GITHUB_REPOSITORY" --target "$REVISION" \
    --title "Mautic 4 PHP emergency images r1 (amd64)" --notes-file docs/release-notes-r1.md --draft \
    artifacts/source-handoff/source-bundle.tar artifacts/source-handoff/source-manifest.json artifacts/source-handoff/SHA256SUMS
for variant in apache fpm; do
    local_image="moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    image_id="$(docker image inspect --format '{{.Id}}' "$local_image")"
    remote="ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    docker tag "$image_id" "$remote"
    docker push "$remote"
    docker manifest inspect "$remote" > "artifacts/published-${variant}-manifest.json"
done
gh release upload "$TAG" --repo "$GITHUB_REPOSITORY" artifacts/published-apache-manifest.json artifacts/published-fpm-manifest.json
gh release edit "$TAG" --repo "$GITHUB_REPOSITORY" --draft=false
echo "Images and corresponding sources released. GHCR visibility and anonymous pulls still require independent verification."
