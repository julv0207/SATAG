#!/usr/bin/env python3
"""Evaluate SpotSound timestamps after an explicit Yes/No presence gate."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from spotsound_metrics import Interval, evaluate_event, mean_valid


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(
    jobs: list[dict], timestamps: dict, presences: dict
) -> list[dict]:
    rows = []
    for job in jobs:
        sample_id = job["id"]
        sample_timestamps = timestamps.get(sample_id, {})
        sample_presences = presences.get(sample_id, {})
        row = {
            key: job[key]
            for key in (
                "id",
                "model_id",
                "model_label",
                "overlap_id",
                "overlap_label",
            )
            if key in job
        }
        for suffix, event_key in (("a", "event_a"), ("b", "event_b")):
            target = Interval(
                float(job[f"start_{suffix}"]), float(job[f"end_{suffix}"])
            )
            result = evaluate_event(
                target,
                sample_timestamps.get(event_key),
                sample_presences.get(event_key),
            )
            row.update({f"{key}_{suffix}": value for key, value in result.items()})
        row["k"] = int(row["detected_a"]) + int(row["detected_b"])
        row["onset_mae"] = mean_valid(
            [row["onset_error_a"], row["onset_error_b"]]
        )
        row["offset_mae"] = mean_valid(
            [row["offset_error_a"], row["offset_error_b"]]
        )
        row["temporal_iou"] = 0.5 * (
            float(row["temporal_iou_a"]) + float(row["temporal_iou_b"])
        )
        rows.append(row)
    return rows


def summarize(rows: list[dict]) -> dict[str, object]:
    n = len(rows)
    counts = {k: sum(row["k"] == k for row in rows) for k in (0, 1, 2)}
    return {
        "n": n,
        "event_recall": mean_valid(row["k"] for row in rows),
        "k0_rate": counts[0] / n if n else math.nan,
        "k1_rate": counts[1] / n if n else math.nan,
        "k2_rate": counts[2] / n if n else math.nan,
        "temporal_iou": mean_valid(row["temporal_iou"] for row in rows),
        "onset_mae": mean_valid(row["onset_mae"] for row in rows),
        "offset_mae": mean_valid(row["offset_mae"] for row in rows),
    }


def grouped_summary(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row.get("model_label", ""), row.get("overlap_label", ""))].append(
            row
        )
    return [
        {
            "model_label": model,
            "overlap_label": overlap,
            **summarize(group),
        }
        for (model, overlap), group in sorted(groups.items())
    ]


def json_safe(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--timestamps", type=Path, required=True)
    parser.add_argument(
        "--presence-predictions",
        type=Path,
        required=True,
        help="Per-event Yes/No predictions. No or unparseable removes timestamps.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = evaluate(
        load_json(args.jobs),
        load_json(args.timestamps),
        load_json(args.presence_predictions),
    )
    payload = {
        "overall": summarize(rows),
        "by_model_overlap": grouped_summary(rows),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "samples.json").write_text(
        json.dumps(json_safe(rows), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "summary.json").write_text(
        json.dumps(json_safe(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
