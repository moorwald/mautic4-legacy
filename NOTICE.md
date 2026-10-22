# Provenance and modifications

This is an unofficial moorwald compatibility prototype, not a Mautic project release.

- Mautic 4.4.13 public distribution: https://github.com/mautic/mautic/releases/tag/4.4.13
- The bundled application retains its upstream GPL license and third-party notices. LICENSE is copied from that distribution.
- Legacy entrypoint/config/database helper and cron baseline adapted/copied from mautic/docker-mautic commit 244effba9cf43ff6c848d164ae4cc4d9c3d55f52 (mautic4 branch). Original project: https://github.com/mautic/docker-mautic/tree/244effba9cf43ff6c848d164ae4cc4d9c3d55f52
- Changes dated 2026-10-22: Debian 12 / Sury package runtime, exact PHP revision checks, credential redaction, configuration error redaction, bounded database availability helper without password arguments, fail-closed incomplete-volume handling, corrected install argument quoting and process lifecycle, deterministic integration-cron initialization, production PHP error/banner defaults, and source/license handoff tooling.
- PHP source backport for CVE-2026-109618/109619: https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2
- Sury source corresponding to pinned PHP packages: https://packages.sury.org/php/pool/main/p/php7.4/php7.4_7.4.33-31+0~20261021.121+debian12~1.gbpe9c428.dsc
- Sury packaging contains patch 0164-Avoid-state-corruption-via-bailout.patch. This is a minimal upstream EOL mitigation, not renewed PHP upstream support.

Project-authored modifications and tooling are offered under GPL-3.0-or-later, subject to each included component's own license. Package copyright/license and changelog/source references remain in /usr/share/doc. Before public binary distribution, complete the corresponding-source/license delivery review; this local build does not claim that the public distribution obligations have already been satisfied.

Sury trust bootstrap uses a SHA-256-pinned HTTPS keyring package, then apt verifies signed repository metadata. Published hashes are provenance checks, not a substitute for independent review. Exact inputs are in build-lock.json. No maintenance service, endorsement or future patch guarantee is implied.
