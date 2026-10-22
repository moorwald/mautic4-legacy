#!/usr/bin/env python3
"""Fail closed until the bounded, tracked first-release checks are reviewed."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = (
    "target_php_and_compatibility_evidence", "unchanged_upstream_payload_verified",
    "inherited_application_risks_disclosed", "image_delta_review_complete",
    "smtp_smoke_complete", "source_license_handoff_complete",
)

def missing_checks(readiness):
    if readiness.get("schema_version") != 1:
        raise ValueError("Unknown release-readiness schema")
    return [name for name in REQUIRED if readiness.get("checks", {}).get(name) is not True]

def main():
    readiness = json.loads((ROOT / "docs/release-readiness.json").read_text())
    pending = missing_checks(readiness)
    if pending:
        print("Image publication blocked; pending scoped review checks:")
        for name in pending:
            print("- " + name)
        return 1
    print("Tracked scoped release checks complete. This does not certify unsupported Mautic itself.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
