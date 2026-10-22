# Compatibility and acceptance contract

## Scope
Replacement candidates for the standard mautic/mautic:v4-apache and v4-fpm contract, not for Mautic 5+ images. Initial architecture linux/amd64. Custom extensions, custom Dockerfiles, arbitrary startup overrides, PHP/Apache/FPM config mounts, rootless/read-only operation and alternative database majors are NOT implicitly certified.

## Must preserve
- Application volume/workdir /var/www/html; seed /usr/src/mautic only if no application is present. Never merge new code into an existing installation.
- Apache 80, FPM 9000, www-data UID/GID 33.
- MAUTIC_DB_HOST (including host:port), MAUTIC_DB_PORT, MAUTIC_DB_NAME, MAUTIC_DB_USER, MAUTIC_DB_PASSWORD, MAUTIC_DB_TABLE_PREFIX.
- MAUTIC_RUN_CRON_JOBS=true and MAUTIC_RUN_MIGRATIONS=false defaults, explicit string true to activate legacy flags.
- PHP_INI_DATE_TIMEZONE, PHP_MEMORY_LIMIT, PHP_MAX_UPLOAD (512M Apache / 128M FPM), PHP_MAX_EXECUTION_TIME.
- MAUTIC_CONFIG_* passthrough, MAUTIC_TRUSTED_PROXIES, legacy automated-install parameters and integration cron flags.
- /usr/local/etc/php/php.ini and conf.d user configuration interface where tested. Distribution module configuration remains separately loaded. No claim that arbitrary official-php Docker build helpers/custom modules are compatible.

## Deliberate differences
- Debian 12/Sury packages rather than EOL Debian 11 and stale official PHP 7.4 binaries.
- No database password/configuration dump in startup/error logs or password argument in the database helper command.
- Existing installed application is not overwritten. A partially populated non-application volume fails closed rather than being silently merged.
- Generated PHP configuration disables public error/startup-error display and version banners, while logging errors to stderr. Explicit operator configuration mounts remain authoritative.
- No fallback to an older PHP revision. Runtime package revision is checked at build/start.
- PHP security backport disables session upload-progress bookkeeping and changes out-of-memory cleanup. It does not disable ordinary multipart uploads. Test worker recovery and application uploads separately.
- Supported default commands are apache2-foreground and php-fpm; unrelated commands bypass application bootstrap.

## Acceptance matrix
For BOTH Apache and FPM:
1. Static/negative controls for credential redaction, flags, pins, volume preservation and source provenance.
2. CLI extensions, exact package revision, PHP version and OOM regression; web SAPI checks over real HTTP/FastCGI.
3. Fresh real release install with synthetic isolated database, login/authentication and bounded application operations.
4. Repeated start preserves full application/config/upload files; existing old-image fixture survives replacement, no implicit code/schema update.
5. PHP override behavior, cron on/off and process stop, no secret values in logs, invalid config fails without dumping credentials.
6. No publicly exposed test service; no real email, payment, CRM/webhook or telemetry traffic.

Completed evidence belongs in artifacts/ and docs/status.md. Passing only some gates does not certify the matrix. The bounded image/runtime review and release checks are required. A full application audit, plugin modernization, ARM64 and live migration are outside this release scope; see docs/security-assessment.md.
