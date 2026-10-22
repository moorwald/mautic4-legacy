# Local prototype status: 22 October 2026

## Verdict
Both linux/amd64 images build locally and the bounded synthetic compatibility matrix passes. Public source/CI and a manual GHCR release path have been authorized and prepared; no image has been published. This is NOT a production recommendation or a complete drop-in/security certification.

Local tags:
- `moorwald/mautic4-legacy:4.4.13-php74-r1-apache`
- `moorwald/mautic4-legacy:4.4.13-php74-r1-fpm`

## Verified matrix
Static/audit/assessment/release-gate regression tests pass (see current CI results for the exact count). Build inputs match the recorded lock; local builds are not pushed registry manifests.

Evidence: ignored `artifacts/m4qa-20e6d50316/report.json`, completed 2026-10-22 10:13:48 UTC. Four cases: Apache/FPM x fresh Mautic 4.4.13 / existing Mautic 4.4.12.

- Exact patched PHP CLI/common and Apache/FPM package revision checked, not merely upstream banner 7.4.33.
- All PHP extensions loaded by the corresponding original official v4 image remain available; SQLite was retained, FPM mcrypt is separately pinned. Composer 2.10.3 is available.
- Real application installation and authenticated synthetic administrator login pass over Apache/FPM (nginx test proxy for FPM).
- Web PHP extensions, timezone/memory configuration and a mounted conf.d override pass.
- Ordinary synthetic multipart upload works. Controlled OOM exits without executing the shutdown callback; subsequent web requests succeed.
- Cron-off, cron-on and graceful stop pass; migrations remain disabled. Partial/incomplete volume and unexpected PHP package revision fail closed; configuration failures do not dump credentials.
- Existing application/configuration/original upload fingerprints match across restart and actual container replacement. Each comparison covers 23,123 immutable/original files, excluding documented caches/logs. Configuration comparison is normalized, not a promise of byte-identical local.php formatting.
- For the existing case, the ORIGINAL image's PHP CLI first installs Mautic 4.4.12 and initializes its anonymous HTTP kernel without opening a listener. A full native SQL-dump hash before/after the runtime swap matches. No new application/schema version is silently installed.
- Bounded segments/campaign rebuild/trigger commands pass on the otherwise empty fixture. This is not evidence of a populated customer campaign completing or actual mail delivery.
- No test ports published; internal Docker network only. No production data or external mail/CRM/payment/advertising traffic. Known test containers/network/volumes cleaned up.

## Why baseline initialization matters
The first exploratory existing-DB comparison found two builtin integration-settings rows added on first application HTTP-kernel initialization, plus their AUTO_INCREMENT change. The final source fixture performs this same initialization on the original runtime BEFORE taking its reference hash. The final comparison is exact, not a table exclusion or ignored difference.

## Application dependency warning
The PHP backport does NOT repair the obsolete Mautic dependency tree.

Advisory audit of the exact 195 packages shipped in the 4.4.13 ZIP found, at this check:
- 114 unique advisories in 27 packages.
- 4 critical, 40 high, 50 medium, 16 low, 4 without severity.
- 7 abandoned packages.

These are RAW package-version advisory matches, NOT proof that every issue is reachable/exploitable through Mautic and NOT a compromise finding. No exploit attempts were performed. The subsequent [scoped assessment](security-assessment.md) verified byte-identical application payloads and identified five core-version metadata false positives already fixed in 4.4.13: **109 inherited unique matches remain in 26 libraries**, including the four critical matches. The correction does not apply to preserved 4.4.12 volumes. A passing PHP/runtime test does not fix remaining application findings.

The release ZIP has installed-package metadata but no upstream root Composer lock. `tools/audit_installed.py` derives an AUDIT-ONLY lock from exact shipped metadata, disables plugins/scripts, queries public advisories and rejects an empty package set. Merely copying installed.json without package directories produced Composer's misleading “No packages - skipping audit”; that was rejected, not counted as a successful security result.

Reproduce: `python3 tools/audit_installed.py`. A nonzero result for advisories/abandonment is expected and must not be silenced. Raw public advisory JSON and a bounded summary are in ignored `artifacts/composer-audit*.json`.

## Scope and first-publication gates
Sven explicitly set a PHP-only emergency-mitigation scope, not continued Mautic 4 development or ELTS. The [assessment](security-assessment.md) separates inherited application risk from changes introduced by this project. **Zero application advisories, library modernization and a complete application audit are not release criteria.**

Required before first publication:
- Scoped review of our container/runtime changes, target-CVE provenance and bounded regression evidence. New exposure, credential leakage, data loss or an unpatched SAPI remains a blocker.
- Bounded additional workflow/SMTP smoke checks needed to support any broader compatibility claim; no application feature or dependency changes are implied.
- Corresponding-source/license delivery, explicit emergency-only/no-support/retirement policy and accurate not-official/residual-risk notices.
- GitHub public-source and GHCR publication-path approval was given on 22 October. The manual image publish job remains blocked by [release-readiness.json](release-readiness.json) until the pending scoped checks are reviewed. Ordinary pushes cannot publish images. See [publishing](publishing.md).

Not certified and not implicitly added to this project's scope:
- A full audit or repair of Mautic 4 application/library vulnerabilities. Operators retain responsibility for their installation.
- Exhaustive populated contact/segment/campaign/form/editor workflows; ordinary PHP multipart is NOT a complete Mautic asset-manager workflow test.
- Custom plugins, arbitrary PHP/server config mounts, official-php extension build helpers, read-only/rootless deployments, alternative database families/majors, load/concurrency and live customer migration.
- ARM64. A later ARM64 release needs its own patched build and architecture-specific tests; its absence does not block a correctly labelled amd64-only release.
- A blanket zero-vulnerability OS/SBOM certification. Image-layer dependency/exposure review stays relevant; no host scanner was installed automatically.

## Recovery boundary
Before any later real deployment, independently back up database AND persistent application/config/media, prove restore and preserve later writes. A runtime-only swap does not authorize an app/schema upgrade. Do not automatically fall back to publicly vulnerable PHP. Images are build/test artifacts, not backups or an incident-response guarantee.
