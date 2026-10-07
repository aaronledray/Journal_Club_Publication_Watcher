"""Offline tests for seen-state retention across long query windows."""

import unittest
from datetime import datetime, timedelta, timezone

from notify_modules.seen_tracker import prune_old_entries


class SeenTrackerTests(unittest.TestCase):
    def test_retention_covers_configured_lookup_window(self):
        now = datetime.now(timezone.utc)
        seen = {
            "seen": {
                "doi:recent": (now - timedelta(days=200)).isoformat(),
                "doi:expired": (now - timedelta(days=400)).isoformat(),
            }
        }

        prune_old_entries(seen, max_age_days=180, lookup_frequency="1 year")

        self.assertIn("doi:recent", seen["seen"])
        self.assertNotIn("doi:expired", seen["seen"])

    def test_naive_legacy_timestamps_are_treated_as_utc(self):
        recent = (datetime.now(timezone.utc) - timedelta(days=20)).replace(
            tzinfo=None
        ).isoformat()
        seen = {"seen": {"doi:legacy": recent}}

        prune_old_entries(seen, max_age_days=180)

        self.assertIn("doi:legacy", seen["seen"])


if __name__ == "__main__":
    unittest.main()
