import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_installed", ROOT / "tools/audit_installed.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

class AuditTests(unittest.TestCase):
    def test_empty_audit_is_not_a_success(self):
        with self.assertRaises(ValueError):
            AUDIT.derived_lock({"packages": []})

    def test_exact_installed_versions_not_dependency_resolution(self):
        lock = AUDIT.derived_lock({"packages": [
            {"name": "example/package", "version": "v1.2.3", "install-path": "/nonexistent"},
        ]})
        self.assertEqual(lock["packages"], [{"name": "example/package", "version": "v1.2.3"}])
        self.assertEqual(lock["packages-dev"], [])

    def test_unique_advisories_are_not_double_counted(self):
        advisory = {"advisoryId": "example-id", "severity": "high"}
        summary = AUDIT.summarize({"advisories": {"a": [advisory], "b": {"0": advisory}},
                                   "abandoned": {"old/package": None}}, 2)
        self.assertEqual(summary["unique_advisories"], 1)
        self.assertEqual(summary["affected_packages"], 2)
        self.assertEqual(summary["abandoned_packages"], 1)

if __name__ == "__main__":
    unittest.main()
