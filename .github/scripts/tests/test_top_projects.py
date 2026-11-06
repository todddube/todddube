import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import update_projects as up  # noqa: E402


def proj(name, commits, last="2026-01-01T00:00:00+00:00"):
    return {"name": name, "commits_30d": commits, "last_commit": {"date": last}}


class PickTop(unittest.TestCase):
    def test_busiest_first_and_limited(self):
        ps = [proj("a", 2), proj("b", 9), proj("c", 5), proj("d", 7), proj("e", 1)]
        self.assertEqual([p["name"] for p in up.pick_top(ps, 3)], ["b", "d", "c"])

    def test_ties_go_to_most_recent_commit(self):
        ps = [proj("old", 4, "2026-01-01T00:00:00+00:00"), proj("new", 4, "2026-02-01T00:00:00+00:00")]
        self.assertEqual([p["name"] for p in up.pick_top(ps, 1)], ["new"])

    def test_quiet_projects_never_qualify(self):
        self.assertEqual(up.pick_top([proj("a", 0), proj("b", 0)], 4), [])

    def test_zero_count(self):
        self.assertEqual(up.pick_top([proj("a", 3)], 0), [])


if __name__ == "__main__":
    unittest.main()
