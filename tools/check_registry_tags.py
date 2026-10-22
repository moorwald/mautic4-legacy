#!/usr/bin/env python3
"""Authenticated, read-only preflight: never silently overwrite a versioned GHCR release."""
import json
import subprocess

TAGS = {"4.4.13-php74-r1-apache", "4.4.13-php74-r1-fpm"}
ENDPOINT = "orgs/moorwald/packages/container/mautic4-legacy/versions?per_page=100"

def conflicting_tags(pages):
    return sorted({
        tag for page in pages for version in page
        for tag in version.get("metadata", {}).get("container", {}).get("tags", [])
        if tag in TAGS
    })

def main():
    result = subprocess.run(["gh", "api", "--paginate", "--slurp", ENDPOINT],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        if "(HTTP 404)" in result.stderr:
            print("Package not found through the repository token; first creation may proceed if org policy allows.")
            return 0
        raise RuntimeError("Package lookup failed without establishing tag absence; refusing publication.")
    conflicts = conflicting_tags(json.loads(result.stdout))
    if conflicts:
        raise RuntimeError("Refusing to overwrite existing release tags: " + ", ".join(conflicts))
    print("No existing versioned r1 tags found in the accessible package.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
