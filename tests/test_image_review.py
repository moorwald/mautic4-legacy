import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("review_image", ROOT / "tools/review_image.py")
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)

class ImageReviewTests(unittest.TestCase):
    def config(self):
        return {"Architecture": "amd64", "Os": "linux", "Config": {
            "ExposedPorts": {"80/tcp": {}}, "Env": ["MAUTIC_DB_USER=root"],
            "Labels": {"org.opencontainers.image.source": REVIEW.EXPECTED_SOURCE},
            "Entrypoint": ["/entrypoint.sh"], "WorkingDir": "/var/www/html",
            "Volumes": {"/var/www/html": {}},
        }}

    def test_expected_contract_and_no_baked_credentials(self):
        REVIEW.check_config(self.config(), "apache")
        bad = self.config()
        bad["Config"]["Env"].append("MAUTIC_DB_PASSWORD=synthetic-only")
        with self.assertRaises(ValueError):
            REVIEW.check_config(bad, "apache")

    def test_unexpected_architecture_and_ports_fail(self):
        for field, value in [("Architecture", "arm64"), ("Os", "windows")]:
            bad = self.config()
            bad[field] = value
            with self.assertRaises(ValueError):
                REVIEW.check_config(bad, "apache")
        bad = self.config()
        bad["Config"]["ExposedPorts"]["22/tcp"] = {}
        with self.assertRaises(ValueError):
            REVIEW.check_config(bad, "apache")

if __name__ == "__main__":
    unittest.main()
