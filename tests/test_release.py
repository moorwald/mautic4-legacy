import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_release", ROOT / "tools/check_release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)

class ReleaseTests(unittest.TestCase):
    def test_missing_and_non_boolean_checks_block(self):
        checks = {name: True for name in RELEASE.REQUIRED}
        self.assertEqual(RELEASE.missing_checks({"schema_version": 1, "checks": checks}), [])
        checks["image_delta_review_complete"] = "true"
        self.assertIn("image_delta_review_complete",
                      RELEASE.missing_checks({"schema_version": 1, "checks": checks}))
        self.assertEqual(len(RELEASE.missing_checks({"schema_version": 1})), len(RELEASE.REQUIRED))

    def test_unknown_schema_fails(self):
        with self.assertRaises(ValueError):
            RELEASE.missing_checks({"schema_version": 2})

    def test_publication_is_manual_and_uses_tested_ids(self):
        workflow = (ROOT / ".github/workflows/images.yml").read_text()
        script = (ROOT / "tools/publish.sh").read_text()
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.publish", workflow)
        self.assertIn("default: false", workflow)
        self.assertIn('docker tag "$image_id" "$remote"', script)
        self.assertNotIn("docker build", script)
        self.assertIn("check_registry_tags.py", script)
        self.assertIn("image_delta_review_complete", RELEASE.REQUIRED)

    def test_automatic_job_has_no_package_write_permission(self):
        workflow = (ROOT / ".github/workflows/images.yml").read_text()
        automatic_job = workflow.split("\n  publish:", 1)[0]
        self.assertNotIn("packages: write", automatic_job)
        self.assertIn("persist-credentials: false", automatic_job)

if __name__ == "__main__":
    unittest.main()
