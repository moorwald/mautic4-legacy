# moorwald Mautic 4 legacy images

Unofficial community Apache/FPM images for Mautic 4.4.13 with a PHP 7.4 emergency mitigation. Not affiliated with or supported by the Mautic project. Addressed scope: PHP CVE-2026-109618 and CVE-2026-109619 only.

## Status
Both local builds, the four-case synthetic compatibility/SMTP suite and the bounded image review pass; exact-source/licence handoff is prepared. See [dated results and actual publication status](docs/status.md). Universal drop-in compatibility is not certified. First release: linux/amd64 only. Mautic 4 is end-of-life; these images do not restore application support, provide an ELTS contract or fix every application/dependency vulnerability.

## Intended compatibility
See [the compatibility contract](docs/compatibility.md). Existing /var/www/html volumes are authoritative and are NOT automatically upgraded to 4.4.13. The image bundles 4.4.13 for fresh installations. A PHP runtime replacement is not an application/schema upgrade.

## Development
Requirements: Docker with Buildx, Python 3 standard library, Bash. No automatic host installation.
```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash tools/build.sh
python3 tests/integration.py
python3 tools/audit_installed.py  # nonzero while known advisory/abandonment findings remain
```
Builds/tests are local and synthetic. No registry push or production deployment is part of these commands.

## Existing-stack use
After checking the actual release/public-package status, retain your database, volumes, environment and routing, and change only the existing service image to the corresponding versioned tag:
```yaml
image: ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-apache
# or the matching -fpm tag for an existing FPM deployment
```
Registry tags require the manual release and independent public-visibility check; see status above. First take a matching database/application/config/media backup and prove restore. Keep automatic migrations disabled. Existing 4.4.12 application code remains 4.4.12; upgrade that code separately through an approved Mautic procedure if needed. Custom setups are outside the tested matrix.

## Security warning
The purpose is limited to PHP CVE-2026-109618 and CVE-2026-109619, not further Mautic 4 development or dependency upgrades. The unchanged 4.4.13 payload has inherited application/library advisories, including critical findings. Read the [scoped assessment and metadata corrections](docs/security-assessment.md). Those inherited risks are disclosed, not automatically treated as a demand to modernize the unsupported application. PHP backports do not make the whole legacy application safe. Operators retain responsibility for their code, plugins, broader security and migration.

## Source and trust
Based on Debian 12 and version-pinned PHP 7.4 packages from packages.sury.org, a third-party package source. Debian and Sury repository signatures are checked by apt. The Sury keyring bootstrap is HTTPS/SHA-256 pinned. Mautic's public release ZIP is pinned by SHA-256, cross-checked with its published SHA-1; the latter is not a new signature guarantee.
See NOTICE.md, build-lock.json and the [corresponding-source/licence handoff](docs/source-handoff.md). Debian packages outside the explicit PHP pins can receive updates on a fresh build: this is a provenance-pinned recipe, not a bit-for-bit reproducible Debian snapshot.

## GitHub and GHCR
[Source repository](https://github.com/moorwald/mautic4-legacy). Pushes and pull requests only verify. The [publication process](docs/publishing.md) uses a manually started workflow and a [tracked readiness gate](docs/release-readiness.json). Image location: `ghcr.io/moorwald/mautic4-legacy`, with separate versioned Apache/FPM tags. GHCR package visibility must be set and checked independently of the public repository.

## Release boundary
The scoped release assertions and explicit manual publication approval are recorded; every publication must still pass the technical workflow checks and exact-source collection. Inherited Mautic library findings do not require a full green application audit or application updates under this scope. New image-induced vulnerabilities/regressions remain blockers. There is no ongoing support, automatic security maintenance or future release commitment. Migrate to a supported Mautic version; this emergency runtime mitigation is not a long-term maintenance plan.
