#!/usr/bin/env python3
"""Check unmodified upstream payload and separate legacy advisory matches from release metadata errors."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Explicitly fixed in the public 4.4.13 release notes; no general advisory suppression.
FIXED_IN_4413 = {
    "CVE-2022-25770", "CVE-2021-27917", "CVE-2024-47050",
    "CVE-2024-47058", "CVE-2022-25768",
}
PHP_INVENTORY = r"""
$root = '/usr/src/mautic';
$files = [];
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS));
foreach ($it as $path => $info) {
    if ($info->isDir() && !$info->isLink()) { continue; }
    $name = substr($path, strlen($root) + 1);
    $files[$name] = hash('sha256', $info->isLink() ? readlink($path) : file_get_contents($path));
}
ksort($files);
echo json_encode($files);
"""

def archive_inventory(archive):
    return {
        entry.filename: hashlib.sha256(archive.read(entry)).hexdigest()
        for entry in archive.infolist() if not entry.is_dir()
    }

def compare_inventory(expected, actual):
    differences = sorted(name for name in expected.keys() | actual.keys()
                         if expected.get(name) != actual.get(name))
    if differences:
        raise ValueError("Application payload differs from pinned release: " + ", ".join(differences[:10]))

def classify(audit, release_version):
    if release_version != "4.4.13":
        raise ValueError("This bounded assessment only covers verified release 4.4.13")
    results = []
    for package, entries in audit["advisories"].items():
        for advisory in (entries.values() if isinstance(entries, dict) else entries):
            false_positive = package == "mautic/core-lib" and advisory.get("cve") in FIXED_IN_4413
            results.append({
                "package": package,
                "advisory_id": advisory["advisoryId"],
                "cve": advisory.get("cve"),
                "severity": advisory.get("severity"),
                "link": advisory.get("link"),
                "disposition": ("release_metadata_false_positive_fixed_in_4.4.13" if false_positive
                                else "inherited_upstream_package_version_match"),
                "introduced_application_dependency_change": False,
                "exploitable_through_mautic_proven": False,
            })
    return results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-zip", type=pathlib.Path, required=True)
    args = parser.parse_args()
    lock = json.loads((ROOT / "build-lock.json").read_text())
    if hashlib.sha256(args.upstream_zip.read_bytes()).hexdigest() != lock["mautic_sha256"]:
        raise ValueError("Upstream ZIP hash does not match the independently recorded release pin")
    with zipfile.ZipFile(args.upstream_zip) as archive:
        expected = archive_inventory(archive)
        release = json.loads(archive.read("app/release_metadata.json"))
        installed_bytes = archive.read("vendor/composer/installed.json")
        installed = json.loads(installed_bytes)
    audit_summary = json.loads((ROOT / "artifacts/composer-audit-summary.json").read_text())
    if audit_summary["installed_metadata_sha256"] != hashlib.sha256(installed_bytes).hexdigest():
        raise ValueError("Advisory report does not belong to the verified upstream package metadata")
    if audit_summary["packages_audited"] != len(installed["packages"]):
        raise ValueError("Advisory report package coverage does not match the release payload")
    results = {"upstream_release": release["version"], "payload_files": len(expected),
               "upstream_zip_sha256": lock["mautic_sha256"], "images": {}}
    for variant in ("apache", "fpm"):
        image = "moorwald/mautic4-legacy:4.4.13-php74-r1-" + variant
        output = subprocess.check_output(
            ["docker", "run", "--rm", "--network", "none", image, "php", "-r", PHP_INVENTORY], text=True)
        actual = json.loads(output)
        compare_inventory(expected, actual)
        identity = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()
        runtime = subprocess.check_output(
            ["docker", "run", "--rm", "--network", "none", image, "php", "-r",
             'require "/usr/src/mautic/vendor/autoload.php"; echo get_class(\\JmesPath\\Env::createRuntime());'],
            text=True).strip()
        results["images"][variant] = {"id": identity, "payload_byte_identical": True,
                                      "default_jmespath_runtime": runtime}
    audit = json.loads((ROOT / "artifacts/composer-audit.json").read_text())
    results["findings"] = classify(audit, release["version"])
    results["declared_core_lib_version"] = next(
        p["version"] for p in installed["packages"] if p["name"] == "mautic/core-lib")
    unique = {}
    for finding in results["findings"]:
        unique[finding["advisory_id"]] = finding
    results["raw_unique_advisories"] = len(unique)
    results["metadata_false_positives"] = sum(
        f["disposition"].startswith("release_metadata_false_positive") for f in unique.values())
    residual = [f for f in unique.values() if f["disposition"] == "inherited_upstream_package_version_match"]
    results["inherited_unique_advisory_matches"] = len(residual)
    results["inherited_affected_packages"] = len({f["package"] for f in residual})
    target = ROOT / "artifacts/security-assessment.json"
    target.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({k:v for k,v in results.items() if k != "findings"}, indent=2))
    print("Detailed register: " + str(target))

if __name__ == "__main__":
    main()
