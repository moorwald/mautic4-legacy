## Unofficial community emergency images, amd64 only

This release addresses **PHP CVE-2026-109618 and CVE-2026-109619** for legacy Mautic 4 Docker deployments. It is not an official Mautic release, renewed Mautic 4 support, ELTS or an application-dependency modernization.

Public image tags, verified pullable without login on 22 October 2026:
- `ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-apache`
- `ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-fpm`

The prepared application payload is byte-identical to public Mautic 4.4.13. Existing application volumes remain authoritative: a preserved 4.4.12 application does NOT silently upgrade to 4.4.13. The patched PHP runtime replaces the old runtime; keep automatic schema migrations disabled.

Tested: Apache/FPM, fresh 4.4.13 and existing original-runtime-initialized 4.4.12, login, configuration, ordinary multipart upload, bounded CLI commands, real Mautic sample-mail helper to an isolated SMTP sink, restart/replacement preservation, controlled OOM behavior and scoped container checks. Custom plugins, external mail delivery/TLS providers and arbitrary customer deployments are not certified.

The unchanged application libraries have known advisory matches, including critical ones. See `docs/security-assessment.md` for scope, metadata corrections and conditional reachability. Operators remain responsible for their application/plugins, access control, data, backups and migration to a supported version.

Before replacing an image, back up and prove restore of BOTH the database and persistent application/config/media. Do not infer a supported/fully secure application from this runtime mitigation.

### Provenance and sources
- PHP packages: Sury revision `1:7.4.33-31+0~20261021.121+debian12~1.gbpe9c428`, based on the upstream EOL backport.
- Base OS: Debian 12; exact installed binary/source versions and image IDs in the attached manifest.
- `source-bundle.tar`: exact Debian/Sury source archives, verified signed-index evidence, upstream Mautic source/build tree and distribution, community build source, copyright/licence texts and source references.
- `SHA256SUMS`: outer bundle/manifest hashes; a second checksum list is inside the bundle.
- `published-*-manifest.json`: actual pushed manifests. No floating latest tag or ARM64 release is supplied.

### Public retrieval verified
Both anonymous manifest access and actual Docker pulls passed at 2026-10-22 14:38:26 UTC, using an isolated credential-free Docker configuration. Downloaded IDs match the tested images and corresponding-source manifest. CLI/common and the respective web SAPI package independently match the exact patched PHP revision above.

Digest-pinned references:
- Apache: `ghcr.io/moorwald/mautic4-legacy@sha256:ea89ebf356cd9941a20844deb3c1ee72383f157f0f1adac0515884879c9f8987`
- FPM: `ghcr.io/moorwald/mautic4-legacy@sha256:7da372e93e6ba82fd3ab5623c5cb4355abc11ea3e34791cc5ee2e2ddbf77530e`

See attached `public-availability.json` for the bounded verification evidence. This post-publication check did not rebuild or overwrite either released image, source bundle or version tag.
