# Presence-gated SpotSound evaluation

Temporal grounding is evaluated in two stages for each conditioned event:

1. Ask whether the event is audible and record a binary `present` value.
2. Use the predicted onset/offset only when `present` is `true`.

`false` and unparseable presence responses discard any timestamp response. Their
onset and offset errors are not included in MAE. A `0.0–0.0` interval is also
invalid and excluded.

```bash
python evaluation/evaluate_spotsound.py \
  --jobs evaluation_jobs.json \
  --timestamps spotsound_timestamps.json \
  --presence-predictions spotsound_presence.json \
  --output-dir evaluation_results
```

The three JSON inputs are keyed by sample ID. Timestamp and presence records use
`event_a` and `event_b` keys. A presence entry has the following form:

```json
{"present": true, "raw": "Yes."}
```

Run the regression tests from the repository root:

```bash
python -m unittest discover -s evaluation -p "test_*.py"
```
