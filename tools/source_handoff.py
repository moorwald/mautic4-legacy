#!/usr/bin/env python3
"""Collect exact image package sources, signed index evidence and redistribution notices."""
import argparse
import base64
import concurrent.futures
import hashlib
import json
import lzma
import pathlib
import re
import shutil
import socket
import subprocess
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORIES = [
    ("debian", "https://deb.debian.org/debian/", "bookworm", "debian-archive-keyring.gpg"),
    ("updates", "https://deb.debian.org/debian/", "bookworm-updates", "debian-archive-keyring.gpg"),
    ("security", "https://security.debian.org/debian-security/", "bookworm-security", "debian-archive-keyring.gpg"),
    ("sury", "https://packages.sury.org/php/", "bookworm", "deb.sury.org-php.gpg"),
]
PUBLIC_KEYS = ("debian-archive-keyring.gpg", "deb.sury.org-php.gpg")
DPKG_FORMAT = r"${binary:Package}\t${source:Package}\t${source:Version}\t${Version}\n"
LICENCES_PHP = r"""
$result = [];
$paths = array_merge(glob('/usr/share/doc/*/copyright'), glob('/usr/share/common-licenses/*'));
foreach ($paths as $path) {
    if (is_file($path)) { $result[substr($path, 1)] = base64_encode(file_get_contents($path)); }
}
// Phar's constructor requires a recognised suffix for this extensionless executable.
copy('/usr/local/bin/composer', '/tmp/composer.phar');
$phar = new Phar('/tmp/composer.phar');
foreach (new RecursiveIteratorIterator($phar) as $path => $file) {
    if (preg_match('~/(LICENSE[^/]*|COPYING[^/]*)$~i', $path)) {
        $result['composer-phar/'.substr($path, strlen('phar:///tmp/composer.phar/'))] =
            base64_encode(file_get_contents($path));
    }
}
echo json_encode($result);
"""

def parse_deb822(text):
    for paragraph in text.strip().split("\n\n"):
        fields = {}
        key = None
        for line in paragraph.splitlines():
            if line.startswith((" ", "\t")) and key:
                fields[key] += "\n" + line[1:]
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.lstrip()
        if fields:
            yield fields

def checksum_rows(value):
    rows = []
    for line in value.splitlines():
        if not line.strip():
            continue
        digest, size, name = line.split()
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid source checksum")
        if pathlib.PurePosixPath(name).name != name or name in (".", ".."):
            raise ValueError("Unsafe source filename")
        rows.append((digest, int(size), name))
    return rows

def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def download(url, path, expected=None, size=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and expected is not None and digest_file(path) == expected:
        return
    temporary = path.with_name(path.name + ".partial")
    # Hundreds of independent downloads exposed transient EAI_AGAIN on WSL DNS.
    # Retry that specific resolver failure, never checksum failures or HTTP errors.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response, temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
            break
        except urllib.error.URLError as error:
            if not (isinstance(error.reason, socket.gaierror) and
                    error.reason.errno == socket.EAI_AGAIN and attempt < 2):
                raise
            print("Temporary DNS failure; retrying public source: " + path.name, flush=True)
            time.sleep(2 ** attempt)
    if expected is not None and digest_file(temporary) != expected:
        raise ValueError("Downloaded source hash mismatch: " + path.name)
    if size is not None and temporary.stat().st_size != size:
        raise ValueError("Downloaded source size mismatch: " + path.name)
    temporary.replace(path)

def docker_output(image, *command):
    return subprocess.check_output(["docker", "run", "--rm", "--network", "none", image, *command], text=True)

def inventory(images):
    packages = {}
    for variant, image in images.items():
        output = docker_output(image, "dpkg-query", "-W", "-f=" + DPKG_FORMAT)
        for line in output.splitlines():
            name, source, source_version, binary_version = line.split("\t")
            row = packages.setdefault((name, binary_version), {
                "binary": name, "binary_version": binary_version,
                "source": source, "source_version": source_version, "variants": [],
            })
            row["variants"].append(variant)
    return sorted(packages.values(), key=lambda row: row["binary"])

def source_indexes(keys, destination):
    result = {}
    evidence = []
    for label, base, suite, key in REPOSITORIES:
        directory = destination / label
        directory.mkdir(parents=True, exist_ok=True)
        signed = directory / "InRelease"
        download(base + "dists/" + suite + "/InRelease", signed)
        verified = subprocess.run(["gpgv", "--keyring", str(keys / key), str(signed)],
                                  capture_output=True, text=True)
        if verified.returncode:
            raise RuntimeError("Source index signature failed for " + label)
        (directory / "signature-verification.txt").write_text(verified.stderr)
        clear = signed.read_text().split("\n\n", 1)[1].split("\n-----BEGIN PGP SIGNATURE-----", 1)[0]
        clear = "\n".join(line[2:] if line.startswith("- ") else line for line in clear.splitlines())
        release = next(parse_deb822(clear))
        expected_line = next(line.split() for line in release["SHA256"].splitlines()
                             if line.strip().endswith(" main/source/Sources.xz"))
        expected, size, _ = expected_line
        compressed = directory / "Sources.xz"
        download(base + "dists/" + suite + "/main/source/Sources.xz",
                 compressed, expected, int(size))
        for fields in parse_deb822(lzma.decompress(compressed.read_bytes()).decode()):
            if "Package" in fields and "Version" in fields:
                result[(fields["Package"], fields["Version"])] = (label, base, fields)
        evidence.append({"repository": label, "base": base, "suite": suite,
                         "inrelease_sha256": digest_file(signed), "sources_sha256": expected,
                         "signature_verified": True})
        print("Verified signed source index: " + label, flush=True)
    return result, evidence

def add_external(name, url, directory, expected=None):
    path = directory / name
    download(url, path, expected)
    return {"name": name, "url": url, "sha256": digest_file(path), "bytes": path.stat().st_size}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "artifacts/source-handoff")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tree = output / "source-bundle"
    tree.mkdir(exist_ok=True)
    keys = tree / "repository-evidence/keyrings"
    keys.mkdir(parents=True, exist_ok=True)
    images = {variant: "moorwald/mautic4-legacy:4.4.13-php74-r1-" + variant
              for variant in ("apache", "fpm")}
    for key in PUBLIC_KEYS:
        encoded = docker_output(images["apache"], "php", "-r",
                                f'echo base64_encode(file_get_contents("/usr/share/keyrings/{key}"));')
        (keys / key).write_bytes(base64.b64decode(encoded))
    packages = inventory(images)
    indexes, evidence = source_indexes(keys, tree / "repository-evidence")
    needed = sorted({(row["source"], row["source_version"]) for row in packages})
    missing = [item for item in needed if item not in indexes]
    if missing:
        raise ValueError("Exact source versions unavailable: " + repr(missing))
    files = []
    sources = []
    for package, version in needed:
        label, base, fields = indexes[(package, version)]
        directory = fields["Directory"]
        if directory.startswith("/") or ".." in pathlib.PurePosixPath(directory).parts:
            raise ValueError("Unsafe signed source directory")
        rows = checksum_rows(fields["Checksums-Sha256"])
        source_files = []
        for digest, size, name in rows:
            url = base + urllib.parse.quote(directory + "/" + name, safe="/+~")
            target = tree / "debian-sources" / package / version / name
            files.append((url, target, digest, size))
            source_files.append({"name": name, "url": url, "sha256": digest, "bytes": size})
        sources.append({"package": package, "version": version, "repository": label, "files": source_files})
    print("Collecting %d exact source packages (%d files)." % (len(needed), len(files)), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(download, url, target, digest, size) for url, target, digest, size in files]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    lock = json.loads((ROOT / "build-lock.json").read_text())
    external = tree / "application-sources"
    external.mkdir(exist_ok=True)
    extras = [add_external("mautic-4.4.13-distribution.zip",
              "https://github.com/mautic/mautic/releases/download/4.4.13/4.4.13.zip",
              external, lock["mautic_sha256"])]
    upstream = json.loads((ROOT / "source-lock.json").read_text())
    for component in upstream["archives"]:
        extras.append(add_external(component["name"], component["url"], external, component["sha256"]))
    for variant, image in images.items():
        licences = json.loads(docker_output(image, "php", "-r", LICENCES_PHP))
        for name, encoded in licences.items():
            target = tree / "licences" / variant / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(encoded))
    local_source = tree / "moorwald-source.tar"
    subprocess.run(["git", "archive", "--format=tar", "--prefix=mautic4-legacy/", "HEAD",
                    "-o", str(local_source)], cwd=ROOT, check=True)
    for name in ("LICENSE", "NOTICE.md", "docs/source-handoff.md"):
        target = tree / "project-notices" / pathlib.Path(name).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    manifest = {
        "schema_version": 1, "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "images": {variant: {"reference": image, "id": subprocess.check_output(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True).strip()}
            for variant, image in images.items()},
        "binary_packages": packages, "source_packages": sources,
        "signed_indexes": evidence, "additional_source_archives": extras,
        "application_payload": "Unchanged public Mautic 4.4.13 distribution",
    }
    manifest_path = tree / "source-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    checksums = []
    for path in sorted(tree.rglob("*")):
        if path.is_file():
            checksums.append(digest_file(path) + "  " + str(path.relative_to(tree)))
    (tree / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
    bundle = output / "source-bundle.tar"
    with tarfile.open(bundle, "w") as archive:
        archive.add(tree, arcname="source-bundle")
    if bundle.stat().st_size >= 2_000_000_000:
        raise ValueError("Source bundle exceeds the single GitHub-release asset limit")
    shutil.copyfile(manifest_path, output / "source-manifest.json")
    (output / "SHA256SUMS").write_text(
        digest_file(bundle) + "  source-bundle.tar\n" +
        digest_file(output / "source-manifest.json") + "  source-manifest.json\n")
    print(json.dumps({"binary_packages": len(packages), "source_packages": len(sources),
                      "source_files": len(files), "bundle_bytes": bundle.stat().st_size,
                      "bundle_sha256": digest_file(bundle), "output": str(output)}, indent=2))

if __name__ == "__main__":
    main()
