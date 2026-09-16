"""Load DegDiT and generate waveforms with SATAG source-wise mix."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import yaml
from diffusers import AutoencoderOobleck
from huggingface_hub import snapshot_download
from safetensors.torch import load_file

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "DegDiT" / "models"))

from model_deg import TangoFluxDEG  # noqa: E402
from SATAG.sourcewise_mix import (  # noqa: E402
    caption_one,
    graph_one,
    mix_waveforms,
    parse_events,
    resolve_amplitude_ratios,
    should_mix_sourcewise,
)

SAMPLE_RATE = 44100
DEFAULT_CONFIG = ROOT / "DegDiT" / "configs" / "tangoflux_deg_audiocaps.yaml"


def load_config(path: str | Path | None = None) -> dict:
    return yaml.safe_load((Path(path) if path else DEFAULT_CONFIG).read_text(encoding="utf-8"))


def load_prompt_records(path: str | Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
        records = payload if isinstance(payload, list) else [payload]
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]

    for index, record in enumerate(records, 1):
        record.setdefault("prompt", record.get("time_captions") or record.get("caption"))
        if not record.get("prompt"):
            raise ValueError(f"Record {index} has no prompt")
        if "data_numpy" not in record:
            events = record.get("events")
            if not events:
                raise ValueError(f"Record {index} has no events or data_numpy")
            record["data_numpy"] = [
                [event["type"] for event in events],
                [float(event["start"]) for event in events],
                [float(event["end"]) for event in events],
            ]
            amplitudes = [
                event.get("amplitude", event.get("amplitude_ratio", event.get("relative_amplitude")))
                for event in events
            ]
            if any(value is not None for value in amplitudes):
                record["data_numpy"].append(
                    [1.0 if value is None else float(value) for value in amplitudes]
                )
        record.setdefault("id", f"{index:04d}")
    return records


def load_model(
    checkpoint: str | Path,
    device: torch.device,
    config: dict | None = None,
) -> tuple[TangoFluxDEG, AutoencoderOobleck]:
    config = config or load_config()
    paths = config["paths"]
    snapshot = Path(
        snapshot_download(
            paths["pretrained_repo"],
            revision=paths.get("pretrained_revision"),
            allow_patterns=["config.json", "tangoflux.safetensors", "vae.safetensors"],
        )
    )
    model = TangoFluxDEG(config=config["model"])
    model.load_state_dict(load_file(str(snapshot / "tangoflux.safetensors")), strict=False)
    model.load_state_dict(load_file(str(checkpoint)), strict=False)
    model.to(device).eval()
    vae = AutoencoderOobleck()
    vae.load_state_dict(load_file(str(snapshot / "vae.safetensors")))
    vae.to(device).eval()
    return model, vae


def stable_seed(base_seed: int, record_id: str) -> int:
    digest = hashlib.blake2b(f"{base_seed}:{record_id}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "little") % (2**31)


def _seeded_latents(model, seeds: Sequence[int], device: torch.device) -> torch.Tensor:
    rows = []
    for seed in seeds:
        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))
        rows.append(torch.randn(model.audio_seq_len, 64))
    return torch.stack(rows, 0).to(device)


def generate_waveforms(
    model,
    vae,
    device: torch.device,
    prompts: Sequence[str],
    event_descriptions: Sequence,
    duration: float,
    num_steps: int,
    guidance: float,
    seeds: Sequence[int],
    sample_rate: int = SAMPLE_RATE,
) -> list[np.ndarray]:
    if len(prompts) != len(event_descriptions) or len(prompts) != len(seeds):
        raise ValueError("prompts, event_descriptions, and seeds must have the same length")
    if not prompts:
        return []
    sample_count = int(duration * sample_rate)
    with torch.inference_mode():
        latents = model.inference_flow_with_deg(
            prompt=list(prompts),
            event_description=list(event_descriptions),
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            duration=torch.tensor([duration], device=device),
            disable_progress=True,
            initial_latents=_seeded_latents(model, seeds, device),
        )
        waveforms = vae.decode(latents.transpose(1, 2)).sample[:, :, :sample_count]
    return [
        waveform.detach().cpu().T.contiguous().numpy().astype(np.float32)
        for waveform in waveforms
    ]


def generate_waveform(
    model,
    vae,
    device: torch.device,
    prompt: str,
    event_description,
    duration: float,
    num_steps: int,
    guidance: float,
    seed: int,
    overlap_mix: str = "sourcewise",
    sample_rate: int = SAMPLE_RATE,
    amplitude_ratios: Sequence[float] | None = None,
) -> tuple[np.ndarray, str]:
    events = parse_events(event_description)
    if should_mix_sourcewise(events, overlap_mix):
        waves = generate_waveforms(
            model,
            vae,
            device,
            [caption_one(event_type, start, end) for event_type, start, end in events],
            [graph_one(event_type, start, end) for event_type, start, end in events],
            duration,
            num_steps,
            guidance,
            [seed + index * 1000 for index in range(len(events))],
            sample_rate=sample_rate,
        )
        ratios = resolve_amplitude_ratios(
            event_description,
            amplitude_ratios=amplitude_ratios,
            prompt=prompt,
        )
        return mix_waveforms(waves, amplitude_ratios=ratios), "sourcewise"
    waveform = generate_waveforms(
        model,
        vae,
        device,
        [prompt],
        [event_description],
        duration,
        num_steps,
        guidance,
        [seed],
        sample_rate=sample_rate,
    )[0]
    return waveform, "joint"
