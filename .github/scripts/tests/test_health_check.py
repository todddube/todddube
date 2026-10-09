import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import health_check as hc  # noqa: E402

NOW = datetime(2026, 10, 9, 15, 0, tzinfo=timezone.utc)


def project(name, **extra):
    return {"name": name, "url": f"https://github.com/todddube/{name}", "image": None, "release": None, "homepage": None, **extra}


def data(hours_old=6, featured=(), others=()):
    return {"generated_at": (NOW - timedelta(hours=hours_old)).isoformat(), "featured": list(featured), "others": list(others)}


def status_map(table):
    return lambda url, method="HEAD": table.get(url, 200)


class Check(unittest.TestCase):
    def run_check(self, d, table=None):
        return hc.check(d, status_map(table or {}), NOW, sleep=lambda s: None)

    def test_healthy(self):
        self.assertEqual(self.run_check(data(featured=[project("a")], others=[project("b")])), ([], []))

    def test_stale_data_is_an_error(self):
        errors, _ = self.run_check(data(hours_old=60))
        self.assertTrue(errors and "60 hours old" in errors[0])
        self.assertEqual(self.run_check(data(hours_old=47))[0], [])

    def test_broken_repo_link_and_screenshot_are_errors(self):
        p = project("a", image="https://raw.githubusercontent.com/todddube/a/main/shot.png")
        errors, _ = self.run_check(data(featured=[p]), {p["image"]: 404, p["url"]: 404})
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("screenshot returned 404" in e for e in errors))

    def test_release_and_homepage_only_warn(self):
        p = project("a", release={"url": "https://github.com/todddube/a/releases/tag/v1"}, homepage="https://example.com")
        errors, warnings = self.run_check(data(featured=[p]), {"https://github.com/todddube/a/releases/tag/v1": 404, "https://example.com": 500})
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2)

    def test_each_url_is_checked_once(self):
        calls = []
        def fn(url, method="HEAD"):
            calls.append(url)
            return 200
        shared = project("a", url="https://github.com/todddube/shared")
        hc.check(data(featured=[shared, dict(shared, name="b")]), fn, NOW, sleep=lambda s: None)
        self.assertEqual(calls.count("https://github.com/todddube/shared"), 1)


class Probe(unittest.TestCase):
    def test_falls_back_to_get_when_head_is_rejected(self):
        fn = lambda url, method="HEAD": 405 if method == "HEAD" else 200  # noqa: E731
        self.assertEqual(hc.probe("u", fn, lambda s: None), 200)

    def test_retries_once_on_network_error(self):
        seq = iter([0, 0, 200, 200])
        self.assertEqual(hc.probe("u", lambda url, method="HEAD": next(seq), lambda s: None), 200)

    def test_a_real_404_is_not_retried(self):
        calls = []
        def fn(url, method="HEAD"):
            calls.append(method)
            return 404
        self.assertEqual(hc.probe("u", fn, lambda s: None), 404)
        self.assertEqual(calls, ["HEAD", "GET"])


if __name__ == "__main__":
    unittest.main()
