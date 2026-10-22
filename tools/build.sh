#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
python3 -m unittest discover -s tests -p 'test_*.py' -v
for variant in apache fpm; do
    docker buildx build --platform linux/amd64 --load --target "$variant" \
        --build-arg "SOURCE_REVISION=$(git rev-parse HEAD)" \
        --tag "moorwald/mautic4-legacy:4.4.13-php74-r1-${variant}" \
        --metadata-file "artifacts/build-${variant}.json" .
done
