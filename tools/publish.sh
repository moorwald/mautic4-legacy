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
# Check both revisions before uploading either member of the pair.
for variant in apache fpm; do
    local_image="moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    actual="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$local_image")"
    test "$actual" = "$REVISION"
done
for variant in apache fpm; do
    local_image="moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    image_id="$(docker image inspect --format '{{.Id}}' "$local_image")"
    remote="ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}"
    docker tag "$image_id" "$remote"
    docker push "$remote"
    docker manifest inspect "$remote" > "artifacts/published-${variant}-manifest.json"
done
echo "Images pushed. GHCR visibility and anonymous pulls still require independent verification."
