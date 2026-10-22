import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_registry_tags", ROOT / "tools/check_registry_tags.py")
REGISTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGISTRY)

class RegistryTests(unittest.TestCase):
    def test_all_pages_are_checked_for_conflicting_release_tags(self):
        pages = [
            [{"metadata": {"container": {"tags": ["unrelated"]}}}],
            [{"metadata": {"container": {"tags": ["4.4.13-php74-r1-apache"]}}}],
        ]
        self.assertEqual(REGISTRY.conflicting_tags(pages), ["4.4.13-php74-r1-apache"])
        self.assertEqual(REGISTRY.conflicting_tags([]), [])

if __name__ == "__main__":
    unittest.main()
