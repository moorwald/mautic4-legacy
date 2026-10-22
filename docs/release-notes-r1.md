## Unofficial community emergency images, amd64 only

This release addresses **PHP CVE-2026-109618 and CVE-2026-109619** for legacy Mautic 4 Docker deployments. It is not an official Mautic release, renewed Mautic 4 support, ELTS or an application-dependency modernization.

Image tags (availability requires public GHCR visibility; verify anonymous pulls):
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

Public-package visibility and anonymous retrieval are checked independently after the push; source release availability alone is not an assertion that an image is anonymously pullable.
