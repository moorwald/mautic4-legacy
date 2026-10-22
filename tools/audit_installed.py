#!/usr/bin/env python3
"""Audit exact public bundled versions without running Mautic or resolving/updating dependencies."""
import argparse
import collections
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "moorwald/mautic4-legacy:4.4.13-php74-r1-apache"

def derived_lock(installed):
    packages = installed["packages"]
    if not packages:
        raise ValueError("Empty package set is not a successful audit")
    return {
        "_readme": [
            "Audit-only derived package list, not an upstream installation lock.",
            "Exact versions taken from the public release vendor/composer/installed.json.",
        ],
        "content-hash": "00000000000000000000000000000000",
        "packages": [{k: v for k, v in package.items() if k not in ("install-path", "dev_requirement")}
                     for package in packages],
        "packages-dev": [], "aliases": [], "minimum-stability": "dev",
        "stability-flags": {}, "prefer-stable": True, "prefer-lowest": False,
        "platform": {}, "platform-dev": {}, "plugin-api-version": "2.2.0",
    }

def summarize(audit, package_count):
    unique = {}
    for items in audit["advisories"].values():
        for item in (items.values() if isinstance(items, dict) else items):
            unique[item["advisoryId"]] = item
    return {
        "packages_audited": package_count,
        "affected_packages": len(audit["advisories"]),
        "unique_advisories": len(unique),
        "severity": dict(collections.Counter(item.get("severity") or "unknown" for item in unique.values())),
        "abandoned_packages": len(audit.get("abandoned", {})),
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args()
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", args.image, "php", "-r",
         'readfile("/usr/src/mautic/vendor/composer/installed.json");'],
        capture_output=True, text=True, check=True,
    )
    installed = json.loads(result.stdout)
    lock = derived_lock(installed)
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mautic4-advisory-audit-") as work:
        path = pathlib.Path(work)
        (path / "composer.json").write_text(json.dumps({
            "name": "moorwald/mautic4-installed-package-audit", "version": "0.1.0",
            "license": "GPL-3.0-or-later", "require": {},
        }))
        (path / "composer.lock").write_text(json.dumps(lock))
        env = os.environ.copy()
        # No existing Composer credentials/configuration are needed for public advisories.
        for key in ("COMPOSER", "COMPOSER_AUTH", "COMPOSER_VENDOR_DIR"):
            env.pop(key, None)
        env["COMPOSER_HOME"] = str(path / "home")
        audit = subprocess.run(
            ["composer", "--no-plugins", "--no-scripts", "audit", "--locked",
             "--no-dev", "--format=json", "--no-interaction"],
            cwd=path, env=env, capture_output=True, text=True, timeout=120,
        )
        if not audit.stdout.strip():
            raise RuntimeError("Composer returned no audit data; refusing a false-green empty audit")
        data = json.loads(audit.stdout)
        summary = summarize(data, len(lock["packages"]))
        summary["installed_metadata_sha256"] = hashlib.sha256(result.stdout.encode()).hexdigest()
        summary["composer_exit_code"] = audit.returncode
        (artifacts / "composer-audit.json").write_text(json.dumps(data, indent=2) + "\n")
        (artifacts / "composer-audit-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        if audit.returncode not in (0, 1, 2, 3):
            raise RuntimeError("Composer audit failed for reasons other than known advisory/abandonment findings")
        return 1 if summary["unique_advisories"] or summary["abandoned_packages"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
