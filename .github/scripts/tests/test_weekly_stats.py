import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import update_projects as up  # noqa: E402

ET, UTC = ZoneInfo("America/New_York"), timezone.utc
NOW = datetime(2026, 10, 9, 20, 0, tzinfo=UTC)  # Friday 4pm Eastern; the week is Mon Oct 5 to Sun Oct 11


def rec(iso, repo="a", claude=False, lang="Swift"):
    return dict(when=datetime.fromisoformat(iso).replace(tzinfo=UTC), repo=repo, title=repo.upper(), language=lang, claude=claude)


RECS = [
    rec("2026-10-05T14:00:00", "a", True), rec("2026-10-05T15:00:00", "a"), rec("2026-10-06T14:00:00", "b", True),
    rec("2026-10-08T14:00:00", "a"), rec("2026-10-09T13:00:00", "c", True, "Assembly"),
    rec("2026-10-06T02:00:00", "a"),                      # 10pm Monday in New York, so still Monday
    rec("2026-09-29T14:00:00", "a"), rec("2026-10-04T23:30:00", "b", True),  # last week; 7:30pm Sunday ET
]


class WeeklyStats(unittest.TestCase):
    def setUp(self):
        self.week, self.history = up.weekly_stats(RECS, NOW, ET, {}, 12)

    def test_week_boundaries_and_score(self):
        w = self.week
        self.assertEqual((w["label"], w["start"], w["end"]), ("WK 41", "2026-10-05", "2026-10-11"))
        self.assertEqual(w["score"], 6)
        self.assertEqual(w["days"], [3, 1, 0, 1, 1, 0, 0])  # the 02:00Z commit lands on Monday, not Tuesday
        self.assertEqual(w["today_index"], 4)

    def test_stats(self):
        w = self.week
        self.assertEqual((w["projects"], w["active_days"], w["claude_commits"], w["claude_pct"]), (3, 4, 3, 50))
        self.assertEqual(w["top_project"], {"title": "A", "commits": 4})
        self.assertEqual(w["languages"], ["Assembly", "Swift"])
        self.assertEqual(w["streak"], 2)  # Thursday and Friday

    def test_last_week_and_hi_score(self):
        self.assertEqual((self.week["last_week"]["label"], self.week["last_week"]["score"]), ("WK 40", 2))
        self.assertEqual(self.week["hi_score"]["start"], "2026-10-05")
        self.assertEqual(len(self.week["trend"]), 12)
        self.assertEqual(self.week["trend"][-1], {"start": "2026-10-05", "score": 6})

    def test_streak_rules(self):
        wed_thu = [rec("2026-10-07T14:00:00"), rec("2026-10-08T14:00:00")]
        self.assertEqual(up.weekly_stats(wed_thu, NOW, ET, {})[0]["streak"], 2)       # today empty: count from yesterday
        saturday = datetime(2026, 10, 10, 20, 0, tzinfo=UTC)
        self.assertEqual(up.weekly_stats(wed_thu, saturday, ET, {})[0]["streak"], 0)  # Friday empty: streak broken
        week_of_days = [rec(f"2026-10-0{d}T14:00:00") for d in (3, 4, 5, 6, 7, 8, 9)]
        self.assertEqual(up.weekly_stats(week_of_days, NOW, ET, {})[0]["streak"], 7)  # crosses Sunday to Monday

    def test_empty_week(self):
        w, _ = up.weekly_stats([], NOW, ET, {})
        self.assertEqual(w["score"], 0)
        self.assertIsNone(w["claude_pct"])
        self.assertIsNone(w["hi_score"])
        self.assertIsNone(w["top_project"])

    def test_history_keeps_old_records_and_ties_go_to_earliest(self):
        entry = {"commits": 60, "projects": 5, "active_days": 6, "claude_commits": 10, "top_project": None}
        w, h = up.weekly_stats(RECS, NOW, ET, {"2026-03-02": entry, "2026-03-09": dict(entry)})
        self.assertEqual(w["hi_score"], {"score": 60, "start": "2026-03-02", "label": "WK 10"})
        self.assertIn("2026-03-02", h)
        self.assertEqual(list(h), sorted(h))

    def test_only_fully_covered_weeks_are_written(self):
        since_day = (NOW - timedelta(weeks=12)).astimezone(ET).date()
        written = [k for k in self.history if k >= "2026-07"]
        self.assertEqual(len(written), 12)
        self.assertTrue(all(datetime.fromisoformat(k).date() > since_day for k in written))

    def test_idempotent(self):
        self.assertEqual(up.weekly_stats(RECS, NOW, ET, self.history), (self.week, self.history))

    def test_new_record_replaces_old(self):
        low = {"2026-03-02": {"commits": 3, "projects": 1, "active_days": 1, "claude_commits": 0, "top_project": None}}
        self.assertEqual(up.weekly_stats(RECS, NOW, ET, low)[0]["hi_score"]["start"], "2026-10-05")

    def test_claude_trailer_detection(self):
        for msg in ("fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>", "x\n\n🤖 Generated with [Claude Code](https://claude.com)"):
            self.assertTrue(up.CLAUDE_RE.search(msg), msg)
        for msg in ("plain commit", "Co-authored-by: Someone Else", "talks about Claude in the subject"):
            self.assertFalse(up.CLAUDE_RE.search(msg), msg)


if __name__ == "__main__":
    unittest.main()
