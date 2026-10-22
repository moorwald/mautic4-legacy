# Emergency image release preparation: 22 October 2026

## Verdict
The scoped release checks are complete: linux/amd64 Apache/FPM compatibility including isolated SMTP, container/runtime review and exact-source/licence handoff. Sven authorized the first manual publication and public GHCR visibility. At this preparation snapshot no image has been pushed; the manual workflow must repeat the checks on its exact commit. Public package visibility and anonymous retrieval remain separate post-push checks. This is NOT a production recommendation or a complete drop-in/security certification.

Local tags:
- `moorwald/mautic4-legacy:4.4.13-php74-r1-apache`
- `moorwald/mautic4-legacy:4.4.13-php74-r1-fpm`

## Verified matrix
Static/audit/assessment/release-gate regression tests pass (see current CI results for the exact count). Build inputs match the recorded lock; local builds are not pushed registry manifests.

Evidence: ignored `artifacts/m4qa-4762527a15/report.json`, completed 2026-10-22 13:07:25 UTC. Built/tested runtime source: `2c9f119`; final CI repeats all tests on the actual publication commit. Four cases: Apache/FPM x fresh Mautic 4.4.13 / existing Mautic 4.4.12.

- Exact patched PHP CLI/common and Apache/FPM package revision checked, not merely upstream banner 7.4.33.
- All PHP extensions loaded by the corresponding original official v4 image remain available; SQLite was retained, FPM mcrypt is separately pinned. Composer 2.10.3 is available.
- Real application installation and authenticated synthetic administrator login pass over Apache/FPM (nginx test proxy for FPM).
- Web PHP extensions, timezone/memory configuration and a mounted conf.d override pass. Actual Apache/FPM requests run as www-data UID 33. Generated defaults disable error/startup-error display and PHP banners; errors log to stderr.
- Ordinary synthetic multipart upload works. Controlled OOM exits without executing the shutdown callback; subsequent web requests succeed.
- Cron-off, cron-on and graceful stop pass; migrations remain disabled. Partial/incomplete volume and unexpected PHP package revision fail closed; configuration failures do not dump credentials.
- Existing application/configuration/original upload fingerprints match across restart and actual container replacement. Each comparison covers 23,123 immutable/original files, excluding documented caches/logs. Configuration comparison is normalized, not a promise of byte-identical local.php formatting.
- For the existing case, the ORIGINAL image's PHP CLI first installs Mautic 4.4.12 and initializes its anonymous HTTP kernel without opening a listener. A full native SQL-dump hash before/after the runtime swap matches. No new application/schema version is silently installed.
- Bounded segments/campaign rebuild/trigger commands pass on the otherwise empty fixture. The actual Mautic mail helper also sends one synthetic message per case to an isolated SMTP receiver, which checks recipient/subject and records only a message hash. All four cases were received exactly once. This does not certify populated customer campaigns, external SMTP/TLS/authentication providers or deliverability.
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

Completed first-release review:
- Container/runtime delta: signed/pinned PHP packages and unchanged app payload, expected ports/volume/entrypoint, no baked credential variables, root-owned helpers not writable by web UID, no packaged test endpoints/socket, remote PHP includes disabled, FFI restricted to preload. No new exposed endpoint or inherited critical-library execution mode was enabled in the bounded review. Root bootstrap remains necessary for the legacy contract; web workers run as UID 33. Evidence: `artifacts/image-review.json` and the four-case matrix. This is not a zero-vulnerability OS scanner result.
- PHP source handoff independently checks Debian/Sury source-index signatures and file hashes. The exact PHP packaging archive contains active `0164-Avoid-state-corruption-via-bailout.patch` in its series, names both CVEs and has SHA-256 `f299907678a90feef3d69d8686f666a45430fa2d556dc28f59f0ad52b7e1b382`.
- SMTP: true Mautic sample-mail helper to an internal synthetic sink, all four cases exactly once. No external delivery claim.
- Sources/licences: all 236 binary package/version combinations resolve to 152 exact source packages, 487 checked source files. Local bundle approximately 717 MiB, with repository evidence, upstream source/build trees, installed copyright/licence texts and own committed recipes. Final CI regenerates from its actual images. Sven confirmed Docker-Mautic uses Mautic's licence. See [source handoff](source-handoff.md) and NOTICE.md.
- No ongoing maintenance/support commitment or automatic releases. This is the single scoped emergency revision; migrate to a supported Mautic release. Existing tags must not be silently overwritten.
- [release-readiness.json](release-readiness.json) records the reviewed assertions. Ordinary pushes still cannot publish. The manually selected publication repeats verification, collects exact sources, pushes the tested IDs and attaches the handoff to a GitHub Release. See [publishing](publishing.md).

Not certified and not implicitly added to this project's scope:
- A full audit or repair of Mautic 4 application/library vulnerabilities. Operators retain responsibility for their installation.
- Exhaustive populated contact/segment/campaign/form/editor workflows; ordinary PHP multipart is NOT a complete Mautic asset-manager workflow test.
- Custom plugins, arbitrary PHP/server config mounts, official-php extension build helpers, read-only/rootless deployments, alternative database families/majors, load/concurrency and live customer migration.
- ARM64. A later ARM64 release needs its own patched build and architecture-specific tests; its absence does not block a correctly labelled amd64-only release.
- A blanket zero-vulnerability OS/SBOM certification. Image-layer dependency/exposure review stays relevant; no host scanner was installed automatically.

## Recovery boundary
Before any later real deployment, independently back up database AND persistent application/config/media, prove restore and preserve later writes. A runtime-only swap does not authorize an app/schema upgrade. Do not automatically fall back to publicly vulnerable PHP. Images are build/test artifacts, not backups or an incident-response guarantee.
