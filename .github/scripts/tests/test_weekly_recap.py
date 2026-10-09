import sys
import unittest
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import weekly_recap as wr  # noqa: E402

ET = ZoneInfo("America/New_York")


def week(commits, projects=1, days=1, claude=0, top=None):
    return {"commits": commits, "projects": projects, "active_days": days, "claude_commits": claude,
            "top_project": {"title": top, "commits": commits} if top else None}


WEEKLY = {"weeks": {
    "2026-09-14": week(2, top="C64 spritemove"),
    "2026-09-21": week(4, claude=4, top="C64 spritemove"),
    "2026-09-28": week(6, 2, 2, 4, "C64 spritemove"),
    "2026-10-05": week(9, 2, 2, 8, "MacBridge"),
    "2026-10-12": week(0, 0, 0),
}}
PROJECTS = [
    {"title": "wthrr", "created_at": "2026-01-01T00:00:00Z", "release": {"tag": "v1.1", "date": "2026-10-07T15:00:00Z"}},
    {"title": "MacBridge", "created_at": "2026-10-06T14:00:00Z", "release": None},
    {"title": "old", "created_at": "2025-01-01T00:00:00Z", "release": {"tag": "v0.1", "date": "2025-02-01T00:00:00Z"}},
]


class Recap(unittest.TestCase):
    def test_new_record_week(self):
        title, body = wr.build_recap(WEEKLY, PROJECTS, date(2026, 10, 12), ET)
        self.assertEqual(title, "Weekly recap: WK 41 (Oct 5 to Oct 11)")
        self.assertIn("**9** commits (▲ 3 vs WK 40)", body)
        self.assertIn("89% (8 of 9 commits)", body)
        self.assertIn("MacBridge (9 commits)", body)
        self.assertIn("New HI-SCORE", body)
        self.assertIn("**Released:** wthrr v1.1", body)
        self.assertIn("**New repos:** MacBridge", body)
        self.assertNotIn("old", body.split("Released")[1].split("\n")[0])

    def test_not_a_record_points_to_the_best_week(self):
        weekly = {"weeks": {**WEEKLY["weeks"], "2026-09-07": week(12, 3, 4, 2, "Vibe Stats")}}
        _, body = wr.build_recap(weekly, PROJECTS, date(2026, 10, 12), ET)  # WK 41: 9 commits, but WK 37 had 12
        self.assertIn("**9** commits", body)
        self.assertNotIn("New HI-SCORE", body)
        self.assertIn("Best week on record: **12 commits** (WK 37, week of Sep 7)", body)

    def test_record_only_counts_weeks_up_to_the_recap_week(self):
        # Recapping WK 36 (the week of Aug 31 is absent): later, bigger weeks must not leak backwards.
        weekly = {"weeks": {"2026-08-31": week(3, top="x"), "2026-09-07": week(12, top="y")}}
        _, body = wr.build_recap(weekly, [], date(2026, 9, 7), ET)
        self.assertIn("New HI-SCORE", body)
        self.assertNotIn("12 commits", body)

    def test_quiet_week(self):
        _, body = wr.build_recap(WEEKLY, PROJECTS, date(2026, 10, 19), ET)
        self.assertIn("A quiet week: no commits.", body)
        self.assertIn("(▼ 9 vs WK 41)", body)
        self.assertNotIn("| With Claude |", body)
        self.assertNotIn("| Top project |", body)
        self.assertIn("Best week on record: **9 commits** (WK 41", body)

    def test_trend_is_twelve_weeks_oldest_first(self):
        _, body = wr.build_recap(WEEKLY, PROJECTS, date(2026, 10, 12), ET)
        line = [l for l in body.splitlines() if l.startswith("**Last 12 weeks")][0]
        self.assertTrue(line.endswith("(0 0 0 0 0 0 0 0 2 4 6 9)"), line)  # 12 values, this week last

    def test_missing_week_raises(self):
        with self.assertRaises(LookupError):
            wr.build_recap(WEEKLY, PROJECTS, date(2026, 11, 2), ET)

    def test_spark(self):
        self.assertEqual(wr.spark([0, 0]), "▁▁")
        self.assertEqual(wr.spark([0, 8]), "▁█")
        self.assertEqual(len(wr.spark([1, 2, 3])), 3)


if __name__ == "__main__":
    unittest.main()
