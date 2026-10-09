import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_config as vc  # noqa: E402

GOOD = {
    "owner": "todddube", "timezone": "America/New_York", "exclude": ["todddube"], "include_forks": [],
    "featured": [
        {"repo": "C64-Projects", "spotlight": True, "title": "C64 spritemove", "why": "A demo.", "path": "spritemove"},
        {"repo": "vstat", "tagline": "Status checker"},
    ],
}


def mutated(fn):
    cfg = copy.deepcopy(GOOD)
    fn(cfg)
    return cfg


class OfflineChecks(unittest.TestCase):
    def errors(self, cfg):
        return vc.check_config(cfg)[0]

    def test_good_config_is_clean(self):
        self.assertEqual(vc.check_config(GOOD), ([], []))

    def test_repo_config_is_valid(self):
        """Guards the real file: this fails the PR that breaks key-projects.json."""
        cfg = json.loads((Path(__file__).resolve().parents[3] / "key-projects.json").read_text())
        errors, _ = vc.check_config(cfg)
        self.assertEqual(errors, [])

    def test_catches_mistakes(self):
        cases = {
            "missing repo": lambda c: c["featured"].append({"title": "x"}),
            "duplicate": lambda c: c["featured"].append({"repo": "vstat"}),
            "excluded": lambda c: c["exclude"].append("vstat"),
            "spotlight without why": lambda c: c["featured"][1].update(spotlight=True),
            "spotlight not a bool": lambda c: c["featured"][1].update(spotlight="yes"),
            "bad timezone": lambda c: c.update(timezone="Eastern"),
            "image is a url": lambda c: c["featured"][1].update(image="https://x.com/a.png"),
            "path escapes repo": lambda c: c["featured"][1].update(path="../etc"),
            "empty tagline": lambda c: c["featured"][1].update(tagline="  "),
            "no featured": lambda c: c.update(featured=[]),
            "bad owner": lambda c: c.update(owner=""),
            "weeks out of range": lambda c: c.update(activity_weeks=1),
            "exclude not a list": lambda c: c.update(exclude="vstat"),
        }
        for name, fn in cases.items():
            with self.subTest(name):
                self.assertTrue(self.errors(mutated(fn)), f"expected an error for: {name}")

    def test_warnings(self):
        _, w = vc.check_config(mutated(lambda c: c["featured"][1].update(colour="red")))
        self.assertTrue(any("unknown key" in x for x in w))
        _, w = vc.check_config(mutated(lambda c: c["featured"][0].update(why="x" * 250)))
        self.assertTrue(any("characters" in x for x in w))
        _, w = vc.check_config(mutated(lambda c: c["featured"][0].update(spotlight=False)))
        self.assertTrue(any("Spotlight section will be hidden" in x for x in w))

    def test_non_object(self):
        self.assertTrue(vc.check_config([])[0])


class OnlineChecks(unittest.TestCase):
    def fake(self, repos, files=()):
        def get(path):
            if "/contents/" in path:
                name = path.split("/contents/")[1].split("?")[0]
                return (200, {}) if name in files else (404, None)
            return repos.get(path.split("/repos/todddube/")[1], (404, None))
        return get

    def public(self, **extra):
        return (200, {"private": False, "archived": False, "fork": False, "default_branch": "main", **extra})

    def test_all_good(self):
        get = self.fake({"C64-Projects": self.public(), "vstat": self.public()}, files={"spritemove"})
        self.assertEqual(vc.check_online(GOOD, get), ([], []))

    def test_problems(self):
        get = self.fake({"C64-Projects": self.public(archived=True), "vstat": (404, None)})
        errors, _ = vc.check_online(GOOD, get)
        self.assertTrue(any("archived" in e for e in errors))
        self.assertTrue(any("no public repo" in e for e in errors))
        self.assertTrue(any("'path' 'spritemove' doesn't exist" in e for e in errors))
        errors, _ = vc.check_online(GOOD, self.fake({"C64-Projects": self.public(private=True, fork=True), "vstat": self.public()}, files={"spritemove"}))
        self.assertTrue(any("private" in e for e in errors) and any("fork" in e for e in errors))

    def test_api_trouble_is_a_warning_not_an_error(self):
        errors, warnings = vc.check_online(GOOD, lambda p: (403, None))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2)


if __name__ == "__main__":
    unittest.main()
