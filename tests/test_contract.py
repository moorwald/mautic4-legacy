"""Static acceptance and negative controls, no Docker or production access."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ContractTests(unittest.TestCase):
    def test_security_lock_is_exact(self):
        lock = json.loads((ROOT / "build-lock.json").read_text())
        self.assertEqual(lock["mautic_version"], "4.4.13")
        self.assertIn("20261021", lock["php_package_version"])
        self.assertIn("@sha256:", lock["debian_image"])
        self.assertEqual(lock["architecture"], "amd64")

    def test_docker_defaults_match_provenance_lock(self):
        lock = json.loads((ROOT / "build-lock.json").read_text())
        dockerfile = (ROOT / "Dockerfile").read_text()
        for key in ["debian_image", "php_package_version", "sury_keyring_url", "sury_keyring_sha256",
                    "composer_version", "composer_sha256", "mcrypt_package_version",
                    "mautic_version", "mautic_sha256"]:
            self.assertIn("ARG " + key.upper() + "=" + lock[key], dockerfile)

    def test_no_password_log_or_config_dump(self):
        entry = (ROOT / "common/docker-entrypoint.sh").read_text()
        config = (ROOT / "common/makeconfig.php").read_text()
        for text in (entry, config):
            self.assertNotRegex(text, r'echo.*(?:Database Password|\$MAUTIC_DB_PASSWORD)')
            self.assertNotIn('$rendered\\n', text)
        self.assertNotIn('php /makedb.php "$MAUTIC_DB_HOST"', entry)

    def test_existing_code_is_not_merged(self):
        entry = (ROOT / "common/docker-entrypoint.sh").read_text()
        self.assertIn('app/AppKernel.php', entry)
        self.assertIn('Refusing to merge', entry)
        self.assertNotRegex(entry, r'cp\\s+-[a-z]*u')
        self.assertNotIn('composer update', entry)

    def test_both_targets_and_no_unpatched_fallback(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("AS apache", dockerfile)
        self.assertIn("AS fpm", dockerfile)
        self.assertIn('VOLUME ["/var/www/html"]', dockerfile)
        self.assertNotIn("FROM php:7.4", dockerfile)
        self.assertIn("rm -f /var/www/html/index.html", dockerfile)
        runtime = (ROOT / "common/check-runtime").read_text()
        self.assertIn("dpkg-query", runtime)
        self.assertIn("PHP_PACKAGE_VERSION", runtime)

    def test_php_configuration_interface(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("PHPRC=/usr/local/etc/php/php.ini", dockerfile)
        self.assertIn("PHP_INI_SCAN_DIR=", dockerfile)
        self.assertIn("/usr/local/etc/php/conf.d", dockerfile)

    def test_package_install_uses_signed_source_and_exact_pins(self):
        script = (ROOT / "tools/install-runtime.sh").read_text()
        self.assertIn("signed-by=", script)
        self.assertIn('=${PHP_PACKAGE_VERSION}', script)
        self.assertNotIn("trusted=yes", script)
        self.assertNotIn("--allow-unauthenticated", script)

    def test_shell_syntax(self):
        paths = [*(ROOT / "common").glob("*.sh"), *(ROOT / "tools").glob("*.sh")]
        paths += [ROOT / "common" / name for name in ["check-runtime", "apache2-foreground", "php-fpm"]]
        for path in paths:
            subprocess.run(["bash", "-n", str(path)], check=True)

    def test_verification_action_cannot_publish(self):
        action = (ROOT / ".github/actions/verify/action.yml").read_text()
        self.assertNotIn("docker push", action)
        self.assertNotIn("docker login", action)
        self.assertNotIn("packages: write", action)

if __name__ == "__main__":
    unittest.main()
