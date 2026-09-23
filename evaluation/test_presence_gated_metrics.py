#!/usr/bin/env python3

import math
import unittest

from spotsound_metrics import Interval, evaluate_event, gated_interval


class PresenceGateTests(unittest.TestCase):
    def test_yes_keeps_timestamp(self) -> None:
        self.assertEqual(
            gated_interval("from 1.0s to 3.0s", {"present": True}),
            Interval(1.0, 3.0),
        )

    def test_no_discards_timestamp(self) -> None:
        result = evaluate_event(
            Interval(1.0, 3.0),
            "from 7.0s to 9.0s",
            {"present": False},
        )
        self.assertFalse(result["detected"])
        self.assertIsNone(result["pred_start"])
        self.assertTrue(math.isnan(result["onset_error"]))
        self.assertTrue(math.isnan(result["offset_error"]))

    def test_unparseable_presence_discards_timestamp(self) -> None:
        self.assertIsNone(
            gated_interval(
                "from 1.0s to 3.0s",
                {"present": None, "raw": "possibly"},
            )
        )

    def test_invalid_timestamp_is_not_detected(self) -> None:
        self.assertIsNone(gated_interval([0.0, 0.0], {"present": True}))


if __name__ == "__main__":
    unittest.main()
