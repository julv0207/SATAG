"""Training-free source-wise mix for temporally overlapping events.

Applied only at inference, after each event is decoded to a waveform.
Training, DEG encoding, and latent sampling are unchanged.
"""

from __future__ import annotations

import re
from typing import Any, Sequence

import numpy as np


Event = tuple[str, float, float]
PEAK_EPS = 1e-8
MIX_PEAK_TARGET = 1.0

_AMPLITUDE_KEYS = ("amplitude", "amplitude_ratio", "relative_amplitude")
_PROMPT_RATIO_RE = re.compile(
    r"(?:relative\s+)?amplitude(?:s|\s+ratios?)?\s*[:=]?\s*"
    r"(-?\d+(?:\.\d+)?(?:\s*[:/,]\s*-?\d+(?:\.\d+)?)+)",
    re.IGNORECASE,
)


def parse_events(event_description: Any) -> list[Event]:
    """Normalize prompt events to ``(type, start, end)`` tuples."""
    if event_description is None:
        return []

    events = getattr(event_description, "events", None)
    if events is not None:
        return [
            (str(event.event_type), float(event.start_time), float(event.end_time))
            for event in events
        ]

    if isinstance(event_description, list) and event_description:
        first = event_description[0]
        if isinstance(first, dict):
            return [
                (str(event["type"]), float(event["start"]), float(event["end"]))
                for event in event_description
            ]
        if (
            len(event_description) in {3, 4}
            and all(isinstance(item, (list, tuple)) for item in event_description)
            and event_description[0]
            and not isinstance(event_description[0][0], (list, tuple))
        ):
            types, starts, ends = event_description[:3]
            return [
                (str(event_type), float(start), float(end))
                for event_type, start, end in zip(types, starts, ends)
            ]
    return []


def _amplitude_from_mapping(payload: dict[str, Any]) -> float | None:
    for key in _AMPLITUDE_KEYS:
        if key in payload and payload[key] is not None:
            return float(payload[key])
    return None


def parse_event_amplitudes(event_description: Any) -> list[float | None]:
    """Per-event relative amplitude, or ``None`` when that event has no ratio."""
    if event_description is None:
        return []

    events = getattr(event_description, "events", None)
    if events is not None:
        values = []
        for event in events:
            properties = getattr(event, "properties", None) or {}
            value = _amplitude_from_mapping(properties) if isinstance(properties, dict) else None
            values.append(value)
        return values

    if isinstance(event_description, list) and event_description:
        first = event_description[0]
        if isinstance(first, dict):
            return [_amplitude_from_mapping(event) for event in event_description]
        if (
            len(event_description) == 4
            and all(isinstance(item, (list, tuple)) for item in event_description)
        ):
            return [float(value) for value in event_description[3]]
    return [None] * len(parse_events(event_description))


def parse_prompt_amplitude_ratios(prompt: str | None, n_events: int) -> list[float] | None:
    """Read ``amplitude 2:1`` / ``relative amplitude 0.5, 1`` from the caption."""
    if not prompt or n_events < 1:
        return None
    match = _PROMPT_RATIO_RE.search(prompt)
    if match is None:
        return None
    values = [float(item) for item in re.split(r"[:/,]\s*", match.group(1).strip())]
    if len(values) != n_events:
        return None
    return values


def resolve_amplitude_ratios(
    event_description: Any,
    *,
    amplitude_ratios: Sequence[float] | None = None,
    prompt: str | None = None,
) -> list[float] | None:
    """Return mix weights only when the user specified a relative amplitude."""
    events = parse_events(event_description)
    n_events = len(events)
    if amplitude_ratios is not None:
        if len(amplitude_ratios) != n_events:
            raise ValueError(
                f"amplitude_ratios has {len(amplitude_ratios)} values for {n_events} events"
            )
        return [float(value) for value in amplitude_ratios]

    parsed = parse_event_amplitudes(event_description)
    if parsed and any(value is not None for value in parsed):
        if len(parsed) != n_events:
            raise ValueError("parsed amplitudes do not match event count")
        return [1.0 if value is None else float(value) for value in parsed]

    return parse_prompt_amplitude_ratios(prompt, n_events)


def intervals_overlap(
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
    *,
    min_overlap: float = 0.0,
) -> bool:
    """True when two half-open intervals share more than ``min_overlap`` seconds."""
    return min(end_a, end_b) - max(start_a, start_b) > min_overlap


def has_temporal_overlap(
    events: Sequence[Event],
    *,
    min_overlap: float = 0.0,
) -> bool:
    """True when any pair of events overlaps in time."""
    for index, (_, start_a, end_a) in enumerate(events):
        for _, start_b, end_b in events[index + 1 :]:
            if intervals_overlap(
                start_a, end_a, start_b, end_b, min_overlap=min_overlap
            ):
                return True
    return False


def should_mix_sourcewise(
    events: Sequence[Event],
    overlap_mix: str = "sourcewise",
) -> bool:
    """Use per-event generation plus sample add only when intervals overlap."""
    return overlap_mix == "sourcewise" and len(events) >= 2 and has_temporal_overlap(events)


def caption_one(event_type: str, start: float, end: float) -> str:
    return f"{event_type} from {start:.2f} to {end:.2f}"


def graph_one(event_type: str, start: float, end: float) -> list[list]:
    return [[event_type], [start], [end]]


def waveform_peak(wave: np.ndarray, *, eps: float = PEAK_EPS) -> float:
    peak = float(np.max(np.abs(wave)))
    return peak if peak > eps else 0.0


def peak_normalize(
    wave: np.ndarray,
    *,
    target: float = MIX_PEAK_TARGET,
    eps: float = PEAK_EPS,
) -> np.ndarray:
    """Scale a waveform so its global peak equals ``target``."""
    peak = waveform_peak(wave, eps=eps)
    if peak == 0.0:
        return np.zeros_like(wave)
    return (wave * (target / peak)).astype(np.float32, copy=False)


def mix_waveforms(
    waves: Sequence[np.ndarray],
    *,
    amplitude_ratios: Sequence[float] | None = None,
    peak_target: float = MIX_PEAK_TARGET,
    normalize_mixture: bool = True,
) -> np.ndarray:
    """Mix aligned source waveforms, then apply global peak normalization.

    Without ``amplitude_ratios``, sources are summed as generated.
    With ratios, each source is peak-normalized to the same reference, then
    weighted by the specified relative amplitude before summing.
    """
    if not waves:
        raise ValueError("mix_waveforms requires at least one waveform")
    length = min(wave.shape[0] for wave in waves)
    aligned = [np.asarray(wave[:length], dtype=np.float32) for wave in waves]
    mixed = np.zeros_like(aligned[0])
    if amplitude_ratios is None:
        for wave in aligned:
            mixed = mixed + wave
    else:
        if len(amplitude_ratios) != len(aligned):
            raise ValueError(
                f"amplitude_ratios has {len(amplitude_ratios)} values for {len(aligned)} sources"
            )
        for wave, ratio in zip(aligned, amplitude_ratios):
            mixed = mixed + float(ratio) * peak_normalize(wave, target=1.0)
    if not normalize_mixture:
        return mixed
    return peak_normalize(mixed, target=peak_target)
