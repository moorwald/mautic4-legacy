import hashlib
import importlib.util
import io
import pathlib
import socket
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

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

    def test_cached_metadata_is_refetched_when_signed_expected_hash_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "Sources.xz"
            path.write_bytes(b"old")
            with patch.object(SOURCE.urllib.request, "urlopen", return_value=io.BytesIO(b"new")):
                SOURCE.download("https://example.invalid/source", path, hashlib.sha256(b"new").hexdigest(), 3)
            self.assertEqual(path.read_bytes(), b"new")

    def test_only_transient_dns_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "source"
            transient = urllib.error.URLError(socket.gaierror(socket.EAI_AGAIN, "synthetic DNS failure"))
            with patch.object(SOURCE.urllib.request, "urlopen", side_effect=[transient, io.BytesIO(b"new")]) as fetch, patch.object(SOURCE.time, "sleep"):
                SOURCE.download("https://example.invalid/source", path, hashlib.sha256(b"new").hexdigest(), 3)
                self.assertEqual(fetch.call_count, 2)
            with patch.object(SOURCE.urllib.request, "urlopen", side_effect=urllib.error.HTTPError("url", 404, "missing", {}, None)) as fetch:
                with self.assertRaises(urllib.error.HTTPError):
                    SOURCE.download("https://example.invalid/source", path)
                self.assertEqual(fetch.call_count, 1)

    def test_paths_and_invalid_hashes_fail(self):
        for value in ["bad 1 source.tar", "a"*64 + " 1 ../outside.tar"]:
            with self.assertRaises(ValueError):
                SOURCE.checksum_rows(value)

if __name__ == "__main__":
    unittest.main()
