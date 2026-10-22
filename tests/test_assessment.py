import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("assess_payload", ROOT / "tools/assess_payload.py")
ASSESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASSESS)

class AssessmentTests(unittest.TestCase):
    def test_payload_changes_and_extra_files_fail(self):
        for actual in ({"code.php": "changed"}, {"code.php": "same", "extra.php": "new"}, {}):
            with self.assertRaises(ValueError):
                ASSESS.compare_inventory({"code.php": "same"}, actual)

    def test_metadata_exception_is_narrow_and_does_not_erase_findings(self):
        advisory = {"advisoryId": "known", "cve": "CVE-2022-25770", "severity": "medium"}
        result = ASSESS.classify({"advisories": {
            "mautic/core-lib": [advisory],
            "other/package": [{**advisory, "advisoryId": "other"}],
        }}, "4.4.13")
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]["disposition"].startswith("release_metadata_false_positive"))
        self.assertEqual(result[1]["disposition"], "inherited_upstream_package_version_match")

    def test_unknown_release_cannot_reuse_fixed_version_exception(self):
        with self.assertRaises(ValueError):
            ASSESS.classify({"advisories": {}}, "4.4.12")

if __name__ == "__main__":
    unittest.main()
