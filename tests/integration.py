#!/usr/bin/env python3
"""Local, synthetic, no published ports; original EOL images are NEVER started as servers."""
import datetime
import hashlib
import html
import json
import pathlib
import re
import secrets
import subprocess
import sys
import time
import urllib.parse
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "build-lock.json").read_text())
IMAGE = "moorwald/mautic4-legacy:4.4.13-php74-r1-"
REQUIRED_EXTENSIONS = {"curl", "gd", "imap", "intl", "mbstring", "mysqli", "pdo_mysql",
                       "zip", "bcmath", "sockets", "exif", "dom", "json", "session"}

class Suite:
    def __init__(self):
        self.prefix = "m4qa-" + uuid.uuid4().hex[:10]
        self.network = self.prefix + "-net"
        self.containers = []
        self.volumes = []
        # Generated credentials authorize ONLY disposable synthetic local resources.
        self.db_password = secrets.token_urlsafe(24)
        self.admin_password = secrets.token_urlsafe(24)
        self.report = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       "architecture": "amd64", "scenarios": [], "ok": False}
        self.artifacts = ROOT / "artifacts" / self.prefix
        self.artifacts.mkdir(parents=True)
        self.network_created = False

    def redacted(self, text):
        for value in (self.db_password, self.admin_password):
            text = text.replace(value, "<synthetic-credential-redacted>")
        return text

    def docker(self, *args, input=None, check=True, timeout=180):
        result = subprocess.run(["docker", *args], input=input, text=True,
                                capture_output=True, timeout=timeout)
        if check and result.returncode:
            # Never render full arguments: environment arguments can contain credentials.
            detail = self.redacted(result.stderr + "\n" + result.stdout)
            raise RuntimeError(f"Docker operation {args[0]} failed: {detail[-4000:]}")
        return result

    def start(self, name, image, *, env=None, options=(), command=()):
        self.containers.append(name)
        args = ["run", "-d", "--name", name, "--network", self.network]
        for key, value in (env or {}).items():
            args += ["-e", key + "=" + str(value)]
        return self.docker(*args, *options, image, *command).stdout.strip()

    def execute(self, container, *command, input=None, check=True, user=None):
        options = ["exec", "-i"]
        if user:
            options += ["--user", user]
        return self.docker(*options, container, *command, input=input, check=check)

    def remove_container(self, name):
        result = self.docker("rm", "-fv", name, check=False)
        if result.returncode:
            raise RuntimeError("Failed to remove a known disposable test container.")
        self.containers.remove(name)

    def http(self, container, base, path, *, data=None, options=(), check=True):
        args = ["curl", "--noproxy", "*", "--silent", "--show-error", "--max-time", "20",
                "--location", "--cookie", "/tmp/qa.cookies", "--cookie-jar", "/tmp/qa.cookies",
                "--write-out", "\n%{http_code}", *options]
        if data is not None:
            args += ["--header", "Content-Type: application/x-www-form-urlencoded", "--data-binary", "@-"]
        args += [base + path]
        result = self.execute(container, *args, input=data, check=False)
        if result.returncode:
            if check:
                raise RuntimeError("HTTP client failed: " + self.redacted(result.stderr))
            return "", 0
        body, status = result.stdout.rsplit("\n", 1)
        return body, int(status)

    def wait_ready(self, app, base):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            state = json.loads(self.docker("inspect", "--format", "{{json .State}}", app).stdout)
            if not state["Running"]:
                logs = self.docker("logs", app, check=False)
                raise RuntimeError("Application exited: " + self.redacted(logs.stdout + logs.stderr)[-5000:])
            body, status = self.http(app, base, "/s/login", check=False)
            if status == 200 and ('name="_username"' in body or '/s/logout' in body):
                # Existing authenticated sessions legitimately redirect login to dashboard.
                return body
            time.sleep(2)
        logs = self.docker("logs", app, check=False)
        raise RuntimeError("Timed out waiting for real Mautic login/dashboard: " +
                           self.redacted(logs.stdout + logs.stderr)[-5000:])

    def copy_fixture(self, app, filename, target):
        self.docker("cp", str(ROOT / "tests" / filename), app + ":" + target)

    def runtime_tests(self, variant):
        image = IMAGE + variant
        for package in ["php7.4-cli", "php7.4-common",
                        "libapache2-mod-php7.4" if variant == "apache" else "php7.4-fpm"]:
            actual = self.docker("run", "--rm", "--network", "none", image,
                                 "dpkg-query", "-W", "-f=${Version}", package).stdout
            assert actual == LOCK["php_package_version"], "Unexpected PHP distribution revision"
        result = self.docker("run", "--rm", "--network", "none", image, "php", "-r",
                             "echo json_encode(['php'=>PHP_VERSION,'ext'=>get_loaded_extensions()]);")
        runtime = json.loads(result.stdout)
        assert runtime["php"] == "7.4.33"
        assert REQUIRED_EXTENSIONS <= set(runtime["ext"])
        legacy = self.docker("run", "--rm", "--network", "none", "--entrypoint", "php",
                             LOCK["test_legacy_images"][variant], "-r", "echo json_encode(get_loaded_extensions());")
        assert set(json.loads(legacy.stdout)) <= set(runtime["ext"]), "Lost an upstream PHP extension"
        composer = self.docker("run", "--rm", "--network", "none", image, "composer", "--version", "--no-ansi")
        assert LOCK["composer_version"] in composer.stdout, "Composer compatibility tool is absent"
        oom = self.docker("run", "--rm", "--network", "none", image, "php", "-d", "memory_limit=16M",
                          "-r", 'register_shutdown_function(function(){echo "UNSAFE_SHUTDOWN_CALLBACK";});'
                          '$value=str_repeat("x",64*1024*1024);', check=False)
        assert oom.returncode != 0
        assert "UNSAFE_SHUTDOWN_CALLBACK" not in oom.stdout + oom.stderr
        partial = self.docker("run", "--rm", "--network", "none",
                              "--entrypoint", "/bin/sh", "-e", "MAUTIC_DB_HOST=unreachable",
                              "-e", "MAUTIC_DB_PASSWORD=" + self.db_password, image, "-c",
                              "printf 'fixture' > /var/www/html/incomplete.txt; exec /entrypoint.sh " +
                              ("apache2-foreground" if variant == "apache" else "php-fpm"), check=False)
        assert partial.returncode != 0 and "Refusing to merge" in partial.stderr
        assert self.db_password not in partial.stdout + partial.stderr
        config_error = self.docker("run", "--rm", "--network", "none",
                                   "-e", "MAUTIC_DB_PASSWORD=" + self.db_password,
                                   image, "php", "/makeconfig.php", check=False)
        assert config_error.returncode != 0
        assert self.db_password not in config_error.stdout + config_error.stderr
        wrong_revision = self.docker("run", "--rm", "--network", "none",
                                    "-e", "PHP_PACKAGE_VERSION=7.4-unpatched", image, "php", "-v", check=False)
        assert wrong_revision.returncode != 0, "Runtime revision negative control did not fail"
        return {"package_revision": LOCK["php_package_version"], "cli_extensions": True,
                "oom_exits_without_shutdown_callback": True, "wrong_revision_rejected": True,
                "upstream_extensions_preserved": True, "composer": LOCK["composer_version"],
                "partial_volume_rejected": True, "configuration_errors_redacted": True}

    def fingerprint(self, app):
        return json.loads(self.execute(app, "php", "/tmp/fingerprint.php").stdout)

    def start_application(self, variant, app, web, env, options):
        self.start(app, IMAGE + variant, env=env, options=options)
        if variant == "fpm":
            self.start(web, LOCK["test_nginx_image"], options=[
                "--network-alias", "web", "--volumes-from", app + ":ro", "--mount",
                "type=bind,src=" + str(ROOT / "tests/nginx.conf") + ",dst=/etc/nginx/conf.d/default.conf,readonly"])

    def database_fingerprint(self, database):
        result = self.docker("exec", "-i", "-e", "MYSQL_PWD=" + self.db_password,
                             self.prefix + "-db", "mariadb-dump", "--user=root",
                             "--skip-comments", "--skip-dump-date", "--skip-lock-tables",
                             "--skip-add-locks", "--skip-extended-insert", "--compact", database)
        # Keep SQL only in process memory for bounded mismatch diagnosis, never on disk.
        lines = result.stdout.splitlines()
        self.last_dump_lines = lines
        return hashlib.sha256(result.stdout.encode()).hexdigest()

    def initialize_existing(self, variant, volume, env):
        name = self.prefix + "-old-cli"
        self.containers.append(name)
        options = ["run", "--rm", "--name", name, "--network", self.network,
                   "--entrypoint", "/bin/bash", "--mount",
                   "type=volume,src=" + volume + ",dst=/var/www/html", "--mount",
                   "type=bind,src=" + str(ROOT / "common") + ",dst=/qa-helpers,readonly", "--mount",
                   "type=bind,src=" + str(ROOT / "tests") + ",dst=/qa-tests,readonly"]
        for key, value in env.items():
            options += ["-e", key + "=" + value]
        command = ('set -e; printf "memory_limit=512M\\ndate.timezone=UTC\\n" > /usr/local/etc/php/php.ini; '
                   'php /qa-helpers/makedb.php; php /qa-helpers/makeconfig.php; '
                   'chown www-data:www-data app/config/local.php; '
                   'sudo -Eu www-data php bin/console mautic:install --force '
                   '--admin_username="$MAUTIC_ADMIN_USERNAME" '
                   '--admin_firstname="$MAUTIC_ADMIN_FIRSTNAME" '
                   '--admin_lastname="$MAUTIC_ADMIN_LASTNAME" "$MAUTIC_URL"; '
                   'sudo -Eu www-data php bin/console mautic:cache:clear; '
                   'sudo -Eu www-data php /qa-tests/warm-http.php')
        result = self.docker(*options, LOCK["test_legacy_images"][variant], "-c", command)
        (self.artifacts / ("source-install-" + variant + ".log")).write_text(
            self.redacted(result.stdout + result.stderr))
        self.containers.remove(name)
        return self.database_fingerprint(env["MAUTIC_DB_NAME"])

    def scenario(self, variant, existing):
        label = variant + ("-existing-4.4.12" if existing else "-fresh")
        print("Testing " + label, flush=True)
        image = IMAGE + variant
        app = self.prefix + "-app"
        web = self.prefix + "-web"
        volume = self.prefix + "-" + label
        self.docker("volume", "create", volume)
        self.volumes.append(volume)
        if existing:
            # The old image only copies packaged files. No vulnerable PHP/web/entrypoint runs.
            old = LOCK["test_legacy_images"][variant]
            seed_name = self.prefix + "-seed"
            self.containers.append(seed_name)
            self.docker("run", "--rm", "--name", seed_name, "--network", "none",
                        "--entrypoint", "/bin/sh", "--mount", "type=volume,src=" + volume + ",dst=/var/www/html",
                        old, "-c", "tar -C /usr/src/mautic -cf - . | tar -C /var/www/html -xf -")
            self.containers.remove(seed_name)
        overrides = self.artifacts / (label + ".ini")
        overrides.write_text("max_input_vars=2345\n")
        base = "http://app" if variant == "apache" else "http://web"
        env = {"MAUTIC_DB_HOST": self.prefix + "-db", "MAUTIC_DB_PORT": "3306",
               "MAUTIC_DB_USER": "root", "MAUTIC_DB_PASSWORD": self.db_password,
               "MAUTIC_DB_NAME": label.replace("-", "_"), "MAUTIC_DB_TABLE_PREFIX": "qa_",
               "MAUTIC_RUN_CRON_JOBS": "false", "MAUTIC_RUN_MIGRATIONS": "false",
               "MAUTIC_URL": base, "MAUTIC_INSTALL_FORCE": "true",
               "MAUTIC_ADMIN_EMAIL": "admin@example.invalid", "MAUTIC_ADMIN_PASSWORD": self.admin_password,
               "MAUTIC_ADMIN_USERNAME": "qa", "MAUTIC_ADMIN_FIRSTNAME": "Synthetic",
               "MAUTIC_ADMIN_LASTNAME": "Fixture", "PHP_MEMORY_LIMIT": "384M",
               "PHP_INI_DATE_TIMEZONE": "Europe/London",
               "MAUTIC_CONFIG_UPDATE_STABILITY": "stable"}
        options = ["--network-alias", "app", "--mount", "type=volume,src=" + volume + ",dst=/var/www/html",
                   "--mount", "type=bind,src=" + str(overrides) + ",dst=/usr/local/etc/php/conf.d/zz-qa.ini,readonly"]
        source_database = self.initialize_existing(variant, volume, env) if existing else None
        source_lines = self.last_dump_lines if existing else []
        self.start_application(variant, app, web, env, options)
        body = self.wait_ready(app, base)
        if existing:
            target_database = self.database_fingerprint(env["MAUTIC_DB_NAME"])
            if source_database != target_database:
                import difflib
                changes = []
                for line in difflib.unified_diff(source_lines, self.last_dump_lines):
                    if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                        table = re.search(r'(?:TABLE|INTO) `([^`]+)`', line)
                        changes.append({"side": line[0], "table": table.group(1) if table else None,
                                        "sha256": hashlib.sha256(line.encode()).hexdigest()})
                (self.artifacts / "database-difference.json").write_text(json.dumps(changes, indent=2))
                raise AssertionError("Image swap changed existing database; hashed differences saved")
        self.copy_fixture(app, "runtime-probe.php", "/tmp/qa-runtime.php")
        if variant == "apache":
            self.copy_fixture(app, "apache-probe.conf", "/etc/apache2/conf-enabled/qa-probe.conf")
            self.execute(app, "apache2ctl", "-k", "graceful")
        self.copy_fixture(app, "fingerprint.php", "/tmp/fingerprint.php")
        probe, code = self.http(app, base, "/qa-runtime.php")
        assert code == 200, f"Runtime HTTP probe failed with status {code}"
        runtime = json.loads(probe)
        assert runtime["sapi"] == ("apache2handler" if variant == "apache" else "fpm-fcgi")
        assert runtime["php"] == "7.4.33"
        assert REQUIRED_EXTENSIONS <= set(runtime["extensions"]), "Missing web PHP extensions"
        assert runtime["memory_limit"] == "384M"
        assert runtime["timezone"] == "Europe/London"
        assert runtime["custom_override"] == "2345"
        assert runtime["upload_max_filesize"] == ("512M" if variant == "apache" else "128M")
        # Plain multipart upload must work despite disabled session upload-progress support.
        self.execute(app, "sh", "-c", "printf 'synthetic-upload' > /tmp/upload.txt")
        uploaded, code = self.http(app, base, "/qa-runtime.php",
                                   options=["--form", "fixture=@/tmp/upload.txt"])
        assert code == 200
        assert json.loads(uploaded)["upload_sha256"] == hashlib.sha256(b"synthetic-upload").hexdigest()
        # Fatal OOM must not execute cleanup callbacks; worker pool must recover.
        fatal, _ = self.http(app, base, "/qa-runtime.php?oom=1", check=False)
        assert "UNSAFE_SHUTDOWN_CALLBACK" not in fatal
        recovered, code = self.http(app, base, "/qa-runtime.php")
        assert code == 200 and json.loads(recovered)["php"] == "7.4.33"
        if variant == "apache":
            self.execute(app, "rm", "/etc/apache2/conf-enabled/qa-probe.conf")
            self.execute(app, "apache2ctl", "-k", "graceful")
        for sensitive in ["/app/config/local.php", "/vendor/autoload.php", "/.git/config"]:
            _, protected_status = self.http(app, base, sensitive)
            assert protected_status in (403, 404), "Sensitive application path is exposed"
        token = re.search(r'name="_csrf_token" value="([^"]+)"', body)
        action = re.search(r'<form[^>]+name="login"[^>]+action="([^"]+)"', body)
        assert token and action, "Real login form not understood"
        login_path = urllib.parse.urlsplit(html.unescape(action.group(1))).path
        payload = urllib.parse.urlencode({"_username": "qa", "_password": self.admin_password,
                                         "_csrf_token": html.unescape(token.group(1))})
        logged_in, code = self.http(app, base, login_path, data=payload)
        assert code == 200 and "/s/logout" in logged_in, "Synthetic admin authentication failed"
        # Bounded real console commands with no external integrations or mail recipients.
        commands = ["mautic:segments:update", "mautic:campaigns:rebuild", "mautic:campaigns:trigger"]
        for command in commands:
            self.execute(app, "php", "bin/console", command, "--no-interaction", user="www-data")
        self.execute(app, "sh", "-c",
                     "printf 'keep-me' > media/files/qa-preserve.txt; chown www-data:www-data media/files/qa-preserve.txt")
        before = self.fingerprint(app)
        expected_version = "4.4.12" if existing else "4.4.13"
        assert before["application_version"] == expected_version, "Implicit application replacement"
        logs = self.docker("logs", app)
        assert self.db_password not in logs.stdout + logs.stderr
        assert self.admin_password not in logs.stdout + logs.stderr
        assert "Applying any needed database migrations" not in logs.stdout + logs.stderr
        cron = self.execute(app, "pgrep", "-x", "cron", check=False)
        assert cron.returncode == 1, "Cron started despite false flag"
        self.docker("restart", app, timeout=60)
        self.wait_ready(app, base)
        after = self.fingerprint(app)
        assert before == after, "Existing application/config/upload changed on restart"
        self.docker("stop", "--time", "15", app)
        state = json.loads(self.docker("inspect", "--format", "{{json .State}}", app).stdout)
        assert not state["Running"] and state["ExitCode"] != 137, "Stop needed SIGKILL"
        if variant == "fpm":
            self.remove_container(web)
        self.remove_container(app)
        # Replace the actual container, reusing the same application volume and environment.
        self.start_application(variant, app, web, env, options)
        self.wait_ready(app, base)
        self.copy_fixture(app, "fingerprint.php", "/tmp/fingerprint.php")
        replacement = self.fingerprint(app)
        assert before == replacement, "Replacement overwrote persistent application/config/upload"
        # Runtime probe lived outside persistent app data, not in this replacement.
        if not existing:
            if variant == "fpm":
                self.remove_container(web)
            self.remove_container(app)
            self.start_application(variant, app, web, {**env, "MAUTIC_RUN_CRON_JOBS": "true"}, options)
            self.wait_ready(app, base)
            assert self.execute(app, "pgrep", "-x", "cron").returncode == 0
            self.docker("stop", "--time", "15", app)
            cron_state = json.loads(self.docker("inspect", "--format", "{{json .State}}", app).stdout)
            assert cron_state["ExitCode"] != 137, "Cron-enabled shutdown required SIGKILL"
        self.report["scenarios"].append({"name": label, "ok": True,
             "application_version": expected_version, "login": True,
             "web_sapi": runtime["sapi"], "web_extensions": True,
             "php_override": True, "multipart_upload": True, "oom_worker_recovery": True,
             "empty_installation_cli_commands": commands, "no_credentials_in_logs": True,
             "cron_disabled": True, "cron_enabled_and_stopped": not existing,
             "no_automatic_migrations": True,
             "restart_and_replacement_preserve_fingerprints": True,
             "fingerprint": before,
             "original_runtime_database_unchanged_on_swap": existing,
             "source_database_sha256": source_database})
        if variant == "fpm":
            self.remove_container(web)
        self.remove_container(app)

    def cleanup(self):
        failures = []
        for name in list(reversed(self.containers)):
            # Some --rm one-off containers may already have exited.
            if self.docker("container", "inspect", name, check=False).returncode == 0:
                if self.docker("rm", "-fv", name, check=False).returncode:
                    failures.append(name)
        for name in reversed(self.volumes):
            if self.docker("volume", "rm", name, check=False).returncode:
                failures.append(name)
        if self.network_created and self.docker("network", "rm", self.network, check=False).returncode:
            failures.append(self.network)
        self.report["cleanup_ok"] = not failures
        if failures:
            self.report["cleanup_failures"] = failures

    def run(self):
        try:
            for image in [LOCK["test_database_image"], LOCK["test_nginx_image"],
                          *LOCK["test_legacy_images"].values()]:
                self.docker("pull", "--platform", "linux/amd64", image, timeout=300)
            self.docker("network", "create", "--internal", self.network)
            self.network_created = True
            db = self.prefix + "-db"
            self.start(db, LOCK["test_database_image"],
                       env={"MARIADB_ROOT_PASSWORD": self.db_password, "MARIADB_ROOT_HOST": "%"})
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if self.execute(db, "healthcheck.sh", "--connect", "--innodb_initialized", check=False).returncode == 0:
                    break
                time.sleep(2)
            else:
                raise RuntimeError("Disposable test database did not become ready")
            self.report["runtime"] = {}
            for variant in ["apache", "fpm"]:
                self.report["runtime"][variant] = self.runtime_tests(variant)
                for existing in [False, True]:
                    self.scenario(variant, existing)
            self.report["ok"] = True
        except Exception as error:
            self.report["error"] = self.redacted(str(error))
            raise
        finally:
            self.cleanup()
            self.report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            target = self.artifacts / "report.json"
            target.write_text(json.dumps(self.report, indent=2) + "\n")
            print("Evidence: " + str(target), flush=True)

if __name__ == "__main__":
    suite = Suite()
    try:
        suite.run()
    except Exception as error:
        print(suite.redacted(str(error)), file=sys.stderr)
        sys.exit(1)
    if not suite.report["cleanup_ok"]:
        sys.exit(1)
