"""Metrics for presence-gated temporal event grounding."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Interval:
    start: float
    end: float

    def is_valid(self) -> bool:
        return (
            math.isfinite(self.start)
            and math.isfinite(self.end)
            and self.end > self.start
        )


INTERVAL_PATTERN = re.compile(
    r"(?:from\s+)?(-?\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?\s+"
    r"(?:to|-)\s+(-?\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?",
    re.IGNORECASE,
)


def parse_interval(value: object) -> Interval | None:
    if isinstance(value, Interval):
        return value if value.is_valid() else None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        interval = Interval(float(value[0]), float(value[1]))
        return interval if interval.is_valid() else None
    if isinstance(value, dict):
        intervals = value.get("intervals")
        if isinstance(intervals, list) and intervals:
            return parse_interval(intervals[0])
        value = value.get("raw")
    if not isinstance(value, str):
        return None
    match = INTERVAL_PATTERN.search(value)
    if match is None:
        return None
    start, end = float(match.group(1)), float(match.group(2))
    if end < start:
        start, end = end, start
    interval = Interval(start, end)
    return interval if interval.is_valid() else None


def presence_value(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        value = value.get("present")
        return value if isinstance(value, bool) else None
    return None


def gated_interval(timestamp: object, presence: object) -> Interval | None:
    """Return a timestamp only when the preceding presence decision is Yes."""
    return parse_interval(timestamp) if presence_value(presence) is True else None


def interval_iou(left: Interval | None, right: Interval) -> float:
    if left is None:
        return 0.0
    intersection = max(
        0.0, min(left.end, right.end) - max(left.start, right.start)
    )
    union = (left.end - left.start) + (right.end - right.start) - intersection
    return intersection / union if union > 0 else 0.0


def absolute_error(
    prediction: Interval | None, target: Interval, boundary: str
) -> float:
    if prediction is None:
        return math.nan
    if boundary == "onset":
        return abs(prediction.start - target.start)
    if boundary == "offset":
        return abs(prediction.end - target.end)
    raise ValueError(f"unknown boundary: {boundary}")


def evaluate_event(
    target: Interval, timestamp: object, presence: object
) -> dict[str, object]:
    prediction = gated_interval(timestamp, presence)
    return {
        "present": presence_value(presence),
        "detected": prediction is not None,
        "pred_start": None if prediction is None else prediction.start,
        "pred_end": None if prediction is None else prediction.end,
        "temporal_iou": interval_iou(prediction, target),
        "onset_error": absolute_error(prediction, target, "onset"),
        "offset_error": absolute_error(prediction, target, "offset"),
    }


def mean_valid(values: Iterable[float]) -> float:
    valid = [float(value) for value in values if not math.isnan(float(value))]
    return sum(valid) / len(valid) if valid else math.nan
