import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("source_handoff", ROOT / "tools/source_handoff.py")
SOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE)

class SourceHandoffTests(unittest.TestCase):
    def test_deb822_empty_multiline_fields_are_preserved(self):
        fields = next(SOURCE.parse_deb822("Package: example\nVersion: 1:2\nChecksums-Sha256:\n " +
                                        "a"*64 + " 12 source.tar.xz\n"))
        self.assertEqual(fields["Version"], "1:2")
        self.assertEqual(SOURCE.checksum_rows(fields["Checksums-Sha256"]),
                         [("a"*64, 12, "source.tar.xz")])

    def test_paths_and_invalid_hashes_fail(self):
        for value in ["bad 1 source.tar", "a"*64 + " 1 ../outside.tar"]:
            with self.assertRaises(ValueError):
                SOURCE.checksum_rows(value)

if __name__ == "__main__":
    unittest.main()
