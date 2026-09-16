#!/usr/bin/env python3
"""SATAG inference CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from tqdm import tqdm

from SATAG.generate import (
    SAMPLE_RATE,
    generate_waveform,
    load_config,
    load_model,
    load_prompt_records,
    stable_seed,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--prompt-file", default="examples/prompts.json")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--config", default=None)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--num-steps", type=int, default=50)
    parser.add_argument("--guidance", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--overlap-mix", choices=["sourcewise", "joint"], default="sourcewise")
    args = parser.parse_args()

    config = load_config(args.config)
    device = torch.device(args.device)
    records = load_prompt_records(args.prompt_file)
    model, vae = load_model(args.checkpoint, device, config)
    audio_dir = Path(args.output_dir) / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for record in tqdm(records, desc="generate"):
        waveform, mix_mode = generate_waveform(
            model,
            vae,
            device,
            record["prompt"],
            record["data_numpy"],
            float(record.get("duration", args.duration)),
            args.num_steps,
            args.guidance,
            stable_seed(args.seed, str(record["id"])),
            overlap_mix=args.overlap_mix,
            amplitude_ratios=record.get("amplitude_ratios"),
        )
        path = audio_dir / f"{str(record['id']).replace('/', '_')}.wav"
        sf.write(path, np.clip(waveform, -1.0, 1.0), SAMPLE_RATE, subtype="PCM_16")
        manifest.append({"id": record["id"], "mix_mode": mix_mode, "audio": str(path)})
    (Path(args.output_dir) / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {len(manifest)} clips to {audio_dir}")


if __name__ == "__main__":
    main()
