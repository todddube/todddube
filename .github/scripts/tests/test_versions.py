import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release  # noqa: E402


class Bump(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(release.bump("1.4.2", "major"), "2.0.0")
        self.assertEqual(release.bump("1.4.2", "minor"), "1.5.0")
        self.assertEqual(release.bump("1.4.2", "patch"), "1.4.3")

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            release.bump("1.0.0", "huge")

    def test_add_release_prepends(self):
        data, v = release.add_release({"current": "1.0.0", "releases": [{"version": "1.0.0"}]}, "minor", " New thing. ", "2026-12-01")
        self.assertEqual(v, "1.1.0")
        self.assertEqual(data["current"], "1.1.0")
        self.assertEqual(data["releases"][0], {"version": "1.1.0", "date": "2026-12-01", "notes": "New thing."})


class RepoFile(unittest.TestCase):
    """Guards the real versions.json the site renders."""
    def test_consistent(self):
        data = json.loads((Path(__file__).resolve().parents[3] / "versions.json").read_text())
        rels = data["releases"]
        self.assertTrue(rels)
        self.assertEqual(data["current"], rels[0]["version"])
        keys = [tuple(map(int, r["version"].split("."))) for r in rels]
        self.assertEqual(keys, sorted(keys, reverse=True), "newest first")
        self.assertEqual(len(set(keys)), len(keys), "no duplicate versions")
        for r in rels:
            self.assertRegex(r["version"], r"^\d+\.\d+\.\d+$")
            self.assertRegex(r["date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(r["notes"].strip())
            self.assertLessEqual(len(r["notes"]), 300, "keep notes to a line or two")


if __name__ == "__main__":
    unittest.main()
