#!/usr/bin/env python3
"""Bounded image-layer review; inherited application advisories remain separately disclosed."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_ENV = {"MAUTIC_DB_PASSWORD", "MAUTIC_ADMIN_PASSWORD", "GITHUB_TOKEN", "GH_TOKEN", "GHCR_TOKEN"}
EXPECTED_SOURCE = "https://github.com/moorwald/mautic4-legacy"

def check_config(config, variant):
    if config["Architecture"] != "amd64" or config["Os"] != "linux":
        raise ValueError("Unexpected architecture")
    cfg = config["Config"]
    if set(cfg.get("ExposedPorts", {})) != {("80/tcp" if variant == "apache" else "9000/tcp")}:
        raise ValueError("Unexpected exposed image ports")
    names = {entry.split("=", 1)[0] for entry in cfg.get("Env", [])}
    if names & FORBIDDEN_ENV:
        raise ValueError("Credential variable baked into image configuration; values withheld")
    if cfg["Labels"].get("org.opencontainers.image.source") != EXPECTED_SOURCE:
        raise ValueError("Image source attribution missing")
    if cfg["Entrypoint"] != ["/entrypoint.sh"] or cfg["WorkingDir"] != "/var/www/html":
        raise ValueError("Unexpected container entrypoint/workdir")
    if "/var/www/html" not in cfg.get("Volumes", {}):
        raise ValueError("Legacy persistent data volume contract missing")

def main():
    report = {"scope": "container/runtime changes only; not an application security clearance", "images": {}}
    for variant in ("apache", "fpm"):
        image = "moorwald/mautic4-legacy:4.4.13-php74-r1-" + variant
        config = json.loads(subprocess.check_output(["docker", "image", "inspect", "--format", "{{json .}}", image], text=True))
        check_config(config, variant)
        subprocess.run(["docker", "run", "--rm", "--network", "none", image, "check-runtime"], check=True)
        subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "33:33",
                        "--entrypoint", "/bin/sh", image, "-ec",
                        "test ! -w /entrypoint.sh; test ! -w /makeconfig.php; test ! -w /makedb.php; "
                        "test ! -S /var/run/docker.sock; test ! -e /qa; test ! -e /workspace; "
                        "test ! -e /tmp/qa-runtime.php; test ! -e /tmp/smtp-smoke.php"], check=True)
        php = json.loads(subprocess.check_output(
            ["docker", "run", "--rm", "--network", "none", image, "php", "-r",
             "echo json_encode(['allow_url_include'=>ini_get('allow_url_include'),'ffi_enable'=>ini_get('ffi.enable')]);"],
            text=True))
        if php["allow_url_include"] not in ("", "0"):
            raise ValueError("Remote PHP include unexpectedly enabled")
        report["images"][variant] = {"id": config["Id"], "architecture": "amd64",
            "expected_port_only": True, "no_baked_credential_variables": True,
            "helpers_not_writable_by_web_uid": True, "no_test_endpoints_or_docker_socket": True,
            "php": php}
    (ROOT / "artifacts/image-review.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
