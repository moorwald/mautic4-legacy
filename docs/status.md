# Emergency image release status: 22 October 2026

## Verdict
Both linux/amd64 images were pushed by successful manual workflow [39785595624](https://github.com/moorwald/mautic4-legacy/actions/runs/39785595624), using source commit `35a1b154a3b705754c827037a101a9064d66c32a`. All scoped checks were repeated successfully, including four SMTP cases and cleanup. The [public GitHub Release](https://github.com/moorwald/mautic4-legacy/releases/tag/v4.4.13-php74-r1) includes the complete source/licence handoff and both pushed manifests. **Public availability verified on 2026-10-22 at 14:38:26 UTC:** both manifests and Docker pulls succeed without credentials, the pulled image IDs match the tested release/source manifest, and exact PHP CLI/common plus Apache/FPM package revisions match the patched build lock. Sven completed the organization/package visibility change. The earlier HTTP 401 is resolved. This is NOT a production recommendation or complete drop-in/security certification.

Uploaded tags:
- `ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-apache`
- `ghcr.io/moorwald/mautic4-legacy:4.4.13-php74-r1-fpm`

Publication evidence:
- Ordinary verification on the exact release commit: [39784684318](https://github.com/moorwald/mautic4-legacy/actions/runs/39784684318), success.
- Manual release report `m4qa-7fe9e62e74/report.json`, completed 2026-10-22 13:21:50 UTC, all four cases/SMTP and cleanup successful.
- Pushed manifest config IDs match BOTH the tested image review and corresponding-source manifest: Apache `sha256:69287377d29f0b1068cdb05dba54823568d808511867ffe80ebc867e2a819834`; FPM `sha256:dbe1795d69dba62662a1ac98f365f6210403cbb1c4e670dec1c65a4d5b4f604f`. These are config IDs, not registry manifest digests.
- Public source bundle: 751,697,920 bytes, SHA-256 `0de137e52e106eda37198546d19fcb19e05fc82d785bce662c1f2be48860ee3a`. Public source-manifest/SHA256SUMS downloads were verified anonymously against the publication evidence.
- Public access evidence: `artifacts/public-availability.json`, also attached to the GitHub Release. Anonymous HTTP manifest bodies match their registry SHA-256 digest headers. Actual Docker pulls use an isolated temporary config with an explicit empty ghcr.io auth entry and no credential store/helper. Containers run only disposable offline revision checks; no production service or data is touched. No agent privileges were extended.
- Apache manifest digest: `sha256:ea89ebf356cd9941a20844deb3c1ee72383f157f0f1adac0515884879c9f8987`.
- FPM manifest digest: `sha256:7da372e93e6ba82fd3ab5623c5cb4355abc11ea3e34791cc5ee2e2ddbf77530e`.
- Both downloaded images pass check-runtime. Independently queried php7.4-cli, php7.4-common and the respective web SAPI package all equal `1:7.4.33-31+0~20261021.121+debian12~1.gbpe9c428`. The public registry lists exactly the two versioned r1 tags; no latest tag or ARM64 variant.

## Verified matrix
26 static/audit/assessment/release/source regression tests pass. Build inputs match the recorded lock; only the exact images tested by the manual job were pushed. The local preparation evidence below is supplemented by the actual publication evidence above.

Evidence: ignored `artifacts/m4qa-4762527a15/report.json`, completed 2026-10-22 13:07:25 UTC. Built/tested preparation runtime source: `2c9f119`; final CI repeated all tests on publication commit `35a1b15`. Four cases: Apache/FPM x fresh Mautic 4.4.13 / existing Mautic 4.4.12.

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
