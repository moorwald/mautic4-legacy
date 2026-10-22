# Mautic 4 community image contract

## Scope
Sven authorized a public moorwald/mautic4-legacy GitHub repository and repository-driven GHCR publication on 22 October 2026. Source pushes and read-only CI are allowed. Sven explicitly authorized completing the remaining checks, publishing both amd64 images and making the GHCR package public. Image publication remains manual and blocked until the tracked scoped release checks pass; public visibility may require the owner's authenticated GitHub UI. No production access/deployment or automatic image publication on push.

The explicit user scope is a community emergency mitigation for PHP CVE-2026-109618 and CVE-2026-109619, not renewed Mautic 4 support, ELTS, application development or dependency modernization. Preserve the application payload. Record inherited library risks; do not turn them into an update mandate or a blanket zero-advisory release gate. Our introduced runtime/image regressions and an unproven target-CVE fix DO block release. See docs/security-assessment.md. Further application/plugin security and migration remain the operator's responsibility.

## Before changes
Read README.md, docs/compatibility.md, docs/security-assessment.md and relevant tests/source. Observable invariant: fresh volumes contain real Mautic 4.4.13, existing application files survive replacement, and PHP CLI/web SAPIs use the exact patched package revision. A working homepage or a 7.4.33 banner alone is a false green.

## Safety
- Use only disposable local Docker resources with a unique test prefix and internal networks. No production data, credentials or mounts.
- Secrets for real deployments come from Infisical. Test fixtures are synthetic and never used for any live service.
- Preserve legacy environment variables, /var/www/html, www-data UID/GID and port 80/9000.
- No automatic application upgrade or database major migration. Existing volumes remain authoritative.
- Do not emit credentials, local.php contents or real request bodies in logs/reports.
- Keep source/package/base pins and provenance. Do not silently fall back to unpatched packages or another architecture.
- No automatic image publication on push or pull requests. Only the explicit main-branch workflow_dispatch publish job may publish, after the tracked readiness and full verification gates pass.
- Keep upstream license/notices and disclose modifications.

## Checks
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash tools/build.sh
python3 tests/integration.py

Run static/negative tests before implementing changed behavior. Keep detailed bounded evidence in ignored artifacts/; never assert production readiness from synthetic tests. Review git diff and remove disposable containers/networks/volumes only by exact known IDs.
