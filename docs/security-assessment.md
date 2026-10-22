# Scoped security assessment: PHP emergency images for Mautic 4

Date: 22 October 2026. Scoped amd64 Apache/FPM emergency-release assessment. No production change. First publication is authorized and follows the reviewed manual path; actual registry visibility is recorded separately in status.md.

## 1. Scope decision

Sven explicitly clarified the purpose: close **CVE-2026-109618 and CVE-2026-109619** for existing Mautic 4 community users. Mautic 4 remains unsupported and is NOT to be developed further by this project. There is no mandate to upgrade its application libraries, revive product support or provide ELTS.

The release criterion is **verified mitigation of these two PHP vulnerabilities without introducing an unacceptable image-layer regression or exposure**, not zero outstanding advisories in an end-of-life application.

Existing application/library findings are documented inherited risk, not an automatic demand for dependency updates or a complete application security audit. Whether a particular library could still be updated is a separate question and does not expand this scope. No dependency updates or application patches were made during this assessment.

Operators remain responsible for their application code, plugins, access control, data, backups, broader security exposure and migration to a supported version. This does not excuse defects introduced by our own container/runtime packaging.

## 2. Evidence and risk delta

- Downloaded the public [Mautic 4.4.13 release](https://github.com/mautic/mautic/releases/tag/4.4.13) and verified SHA-256 against the previously recorded build pin: `3d7446d29f279d17df370fd338583777f2c5f581ea1302458d7744ccac069b6a`.
- Compared every **23,118 payload file** from that archive with `/usr/src/mautic` in BOTH local images. Names and bytes match, including the bundled dependency metadata. No patched, added, removed or upgraded application/dependency files.
- All 195 bundled package versions therefore originate in the upstream public release, not in dependency resolution performed by our Docker build. The build uses the prepared release ZIP, not `composer update`.
- PHP CLI/common and Apache/FPM use pinned Sury revision `1:7.4.33-31+0~20261021.121+debian12~1.gbpe9c428`. The corresponding source/changelog contains the upstream EOL backport for both target CVEs. CLI and web SAPIs, multipart upload, controlled OOM behavior and worker recovery were independently exercised.
- Runtime/OS, extensions and startup packaging ARE changed: Debian 12/Sury instead of the old Debian 11/official-PHP base, retained extension coverage, a newer Composer CLI and bounded entrypoint corrections. Those changes remain our responsibility. PHP/OS package updates may include other existing vendor fixes; no claim is made that the image binary differs only by two source hunks.
- Four synthetic cases passed: fresh 4.4.13 and original-runtime-initialized 4.4.12, each through Apache/FPM. Existing data/code preservation was checked. This is not proof for arbitrary customer plugins or all workloads.

Reproduce the payload comparison and complete finding classification:

```sh
python3 tools/audit_installed.py
# Audit intentionally returns nonzero for the disclosed inherited findings.
# Obtain the public upstream ZIP with gh release download first, then:
python3 tools/assess_payload.py --upstream-zip .cache/upstream/4.4.13.zip
```

Evidence: `artifacts/security-assessment.json`, `artifacts/composer-audit.json`, `artifacts/composer-audit-summary.json` and the compatibility report referenced in [status](status.md). The assessment retains every advisory; it does not erase findings to make a scanner green.

## 3. Correcting the raw advisory count

The raw audit produced **114 unique advisories in 27 packages**, including four critical and seven abandoned packages.

Five matches are metadata false positives for the bundled **4.4.13** payload. Its installed metadata calls `mautic/core-lib` **`4.3.x-dev`**, while `app/release_metadata.json` and the pinned public archive identify 4.4.13. All five advisories have an affected 4.x range ending **before 4.4.13** and are explicitly listed as fixed in the 4.4.13 release notes:

| CVE | Upstream fixed issue |
|---|---|
| CVE-2022-25770 | Insufficient authentication in upgrade flow |
| CVE-2021-27917 | XSS in contact tracking/page-hit reports |
| CVE-2024-47050 | XSS in contact/company tracking |
| CVE-2024-47058 | Stored XSS when editing form HTML |
| CVE-2022-25768 | UI-upgrade access control |

The correction is deliberately limited to these five known CVEs and verified release 4.4.13. It is NOT a blanket exception for `mautic/core-lib`, nor does it apply to a user's preserved 4.4.12 installation.

After correction: **109 unique inherited advisory-version matches in 26 libraries**, still including all four critical library matches. These are not 109 demonstrated remotely exploitable Mautic vulnerabilities. Their complete per-instance reachability is outside this bounded assessment. No exploitation or compromise assessment was performed.

## 4. Bounded review of the four critical matches

### JMESPath 2.6.1: CVE-2026-54133

[Vendor advisory](https://github.com/jmespath/jmespath.php/security/advisories/GHSA-pcw8-m77r-2528): code injection requires attacker influence over the JMESPath EXPRESSION and use of `CompilerRuntime`. Attacker-controlled JSON data alone is insufficient.

The shipped `Env.php` defaults to `AstRuntime`; both actual images independently return `JmesPath\AstRuntime` with their default environment. Bounded scanning found AWS-SDK `JmesPath\Env` consumers, but no explicit `CompilerRuntime` or `JP_PHP_COMPILE` enablement in stock `app/` or `plugins/` sources. This is not a full data-flow proof.

Disposition: **inherited, conditional risk; not introduced by this image**. Do not enable the compiler for untrusted expressions. Prefer leaving `JP_PHP_COMPILE` UNSET rather than assuming a string such as `false` disables it. Plugins and operator configuration can change reachability. No library update is included.

### PhpSpreadsheet 1.23.0: CVE-2026-34084 and CVE-2026-45034

[Original advisory](https://github.com/advisories/GHSA-q4q6-r8wh-5cgh), [bypass advisory](https://github.com/advisories/GHSA-87m4-826x-3crx): unsafe reader filenames/stream wrappers can lead to SSRF and, under relevant PHP 7.x/object-gadget conditions, code execution. The second advisory describes a bypass of a later incomplete library fix; it does not make the older bundled version safe.

The bounded scan of stock `app/` and `plugins/` found PhpSpreadsheet used for exports via `Spreadsheet` and `IOFactory::createWriter`, including `ReportBundle/Model/ExcelExporter.php`, `FormBundle/Model/SubmissionModel.php` and `CoreBundle/Helper/ExportHelper.php`. No stock `IOFactory::load` call was found in that scan. This does not prove all reader paths, wrappers or other spreadsheet advisories unreachable, especially with third-party plugins. The exploit behavior of these vectors under all additional Sury backports was not tested.

Disposition: **inherited library risk; the specifically reported reader call chain was not identified in the bounded stock call-site scan**. No claim that the package is safe and no automatic upgrade to a PHP-8-only library branch. Operators must assess spreadsheet-reading plugins/features and untrusted file/path inputs.

### Twig 3.8.0: CVE-2026-46633

[Vendor advisory](https://symfony.com/cve-2026-46633): compiling a crafted `{% use %}` template name can inject PHP; the advisory explicitly includes a sandbox bypass. A sandbox must not be advertised as a sufficient mitigation.

Twig is configured and referenced in the shipped Mautic code. Template/compiler files and version are unchanged by our image. This review does not establish which operator/plugin workflows could pass attacker-controlled Twig source to compilation.

Disposition: **inherited risk with unresolved per-installation reachability**. Restrict who can supply templates, themes and plugins, but do not claim that this alone fixes the issue. No Twig upgrade or Mautic template-engine development is included.

### Important tool/library distinction

The bundled application contains `composer/composer` **2.2.12** and its own advisory matches. The separately packaged **Composer CLI 2.10.3** does not replace that embedded library or clear its findings. The same distinction applies to a patched PHP runtime versus unchanged application dependencies.

## 5. Release decisions under the agreed scope

| Finding/category | Decision |
|---|---|
| Either target PHP CVE not demonstrably patched in CLI or web SAPI | **Block release** |
| New exposed endpoint, credential leak, data loss, unsafe fallback or image-induced regression | **Block release until fixed or explicitly bounded and reviewed** |
| Unexpected difference from pinned application/dependency payload | **Block and investigate** |
| Inherited library advisory in byte-identical Mautic 4.4.13 payload | Disclose as residual legacy risk; **not automatically a release blocker or update mandate** |
| Known metadata false positive | Explain and retain raw evidence; do not misrepresent as a newly fixed vulnerability |
| User's older application volume or custom plugin | Operator's own risk assessment; no automatic app update, plugin fix or support promise |
| ARM64 without a tested patched build | Do not publish/claim ARM64 support; this need not block an accurately labelled amd64-only release |
| Full application audit, feature development or migration to newer Mautic | Outside project scope |

The completed first-publication checks, with evidence in status.md, cover: a scoped review of our image/runtime changes and PHP-fix evidence, the bounded compatibility smoke checks appropriate to the claim, corresponding-source/license handling, accurate warnings/source references and explicit manual release approval through the configured publication path. A full green audit of unsupported Mautic 4 is NOT required by this scope and is not promised.

The assessment identifies no changed application payload and no newly enabled critical-library attack path in its bounded checks. This is not a statement that the new OS/runtime or arbitrary deployment configuration has zero vulnerabilities. The completed bounded image-layer review stays focused on what we introduce; evidence and limits are recorded in status.md.

## 6. Suggested public scope notice

> Unofficial emergency community images for end-of-life Mautic 4. These images address PHP CVE-2026-109618 and CVE-2026-109619. They do not update Mautic's application dependencies, restore support, provide ELTS or resolve other known Mautic/plugin vulnerabilities. Existing application volumes are not automatically upgraded. Operators remain responsible for the security and maintenance of their installation and should migrate to a supported version.

This is a technical scope statement, not a claim of legal immunity or a replacement for responsible release engineering.
