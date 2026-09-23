#!/usr/bin/env python3
"""AudioCaps-only TangoFlux + DEG flow-matching training."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import torch
import torchaudio
import yaml
from accelerate import Accelerator
from accelerate.utils import set_seed
from diffusers import AutoencoderOobleck
from huggingface_hub import snapshot_download
from safetensors.torch import load_file, save_file
from torch.utils.data import DataLoader, Dataset
from tqdm.auto import tqdm
from transformers import get_scheduler

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "models"))

from model_deg import TangoFluxDEG  # noqa: E402


def audio_file_ok(path: str) -> bool:
    """True if path exists and is a non-empty file."""
    try:
        return Path(path).is_file() and Path(path).stat().st_size > 0
    except OSError:
        return False


class AudioCapsDEGDataset(Dataset):
    def __init__(
        self,
        manifest: str,
        *,
        audio_root_from: str,
        audio_root_to: str,
    ) -> None:
        self.records: list[dict[str, Any]] = []
        skipped_missing = 0
        with Path(manifest).open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                graph = record.get("data_numpy")
                if not graph or len(graph) != 3 or not graph[0]:
                    continue
                location = str(record["location"])
                if audio_root_from and location.startswith(audio_root_from):
                    location = audio_root_to + location[len(audio_root_from) :]
                if not audio_file_ok(location):
                    skipped_missing += 1
                    continue
                self.records.append(
                    {
                        "text": record.get("time_captions")
                        or record.get("captions")
                        or record.get("caption"),
                        "audio_path": location,
                        "duration": float(record.get("duration", 10.0)),
                        "graph": graph,
                    }
                )
        if skipped_missing:
            print(
                f"[dataset] skipped {skipped_missing} missing/empty audio files "
                f"from {manifest} (kept {len(self.records)})",
                flush=True,
            )
        if not self.records:
            raise RuntimeError(f"No valid audio samples found in {manifest}")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        # Re-check at fetch time; wrap around if a file disappeared.
        n = len(self.records)
        for offset in range(n):
            item = self.records[(index + offset) % n]
            if audio_file_ok(item["audio_path"]):
                return item
        raise RuntimeError("All audio files are missing or empty")

    @staticmethod
    def collate_fn(batch: list[dict[str, Any]]) -> dict[str, list[Any]]:
        return {key: [item[key] for item in batch] for key in batch[0]}


def load_audio(path: str, duration: float, sample_rate: int) -> torch.Tensor | None:
    """Load and normalize audio. Returns None if missing, empty, or unreadable."""
    if not audio_file_ok(path):
        return None
    try:
        waveform, source_rate = torchaudio.load(path)
    except Exception as exc:  # noqa: BLE001 — skip corrupt/unreadable files
        print(f"[load_audio] skip {path}: {exc}", flush=True)
        return None
    if waveform.numel() == 0 or waveform.shape[-1] == 0:
        print(f"[load_audio] skip empty waveform: {path}", flush=True)
        return None
    if source_rate != sample_rate:
        waveform = torchaudio.functional.resample(waveform, source_rate, sample_rate)
    if waveform.shape[0] == 1:
        waveform = waveform.repeat(2, 1)
    elif waveform.shape[0] > 2:
        waveform = waveform[:2]

    target_samples = int(round(duration * sample_rate))
    if waveform.shape[-1] < target_samples:
        waveform = torch.nn.functional.pad(
            waveform, (0, target_samples - waveform.shape[-1])
        )
    else:
        waveform = waveform[..., :target_samples]

    peak = waveform.abs().amax()
    if float(peak) <= 0:
        print(f"[load_audio] skip silent audio: {path}", flush=True)
        return None

    waveform = waveform - waveform.mean()
    waveform = 0.5 * waveform / peak.clamp(min=1e-8)
    return waveform


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/tangoflux_deg_audiocaps.yaml",
    )
    parser.add_argument("--resume", default="")
    parser.add_argument("--num-examples", type=int, default=-1)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--disable-tracking", action="store_true")
    return parser.parse_args()


def resolve_tangoflux_snapshot(
    repo_or_path: str,
    revision: str | None = None,
) -> Path:
    path = Path(repo_or_path)
    if not path.exists():
        path = Path(
            snapshot_download(
                repo_or_path,
                revision=revision,
                allow_patterns=[
                    "config.json",
                    "tangoflux.safetensors",
                    "vae.safetensors",
                ],
            )
        )
    return path.parent if path.is_file() else path


def load_tangoflux_initialization(
    model: TangoFluxDEG, snapshot: Path
) -> None:
    weight_path = snapshot / "tangoflux.safetensors"
    if not weight_path.exists():
        raise FileNotFoundError(f"Missing TangoFlux weights: {weight_path}")
    result = model.load_state_dict(load_file(str(weight_path)), strict=False)
    missing = [
        key
        for key in result.missing_keys
        if not key.startswith("graph_transformer.")
    ]
    print(
        f"[TangoFlux init] {weight_path} | "
        f"missing_non_graph={len(missing)} graph_new="
        f"{sum(key.startswith('graph_transformer.') for key in result.missing_keys)} "
        f"unexpected={len(result.unexpected_keys)}",
        flush=True,
    )
    if missing:
        print(f"[TangoFlux init] missing examples: {missing[:20]}", flush=True)
    if result.unexpected_keys:
        print(
            f"[TangoFlux init] unexpected examples: {result.unexpected_keys[:20]}",
            flush=True,
        )


def trainable_parameters(model: TangoFluxDEG) -> list[torch.nn.Parameter]:
    for parameter in model.parameters():
        parameter.requires_grad = False
    modules = [
        model.transformer,
        model.fc,
        model.duration_emebdder,
        model.graph_transformer,
    ]
    params: list[torch.nn.Parameter] = []
    for module in modules:
        for parameter in module.parameters():
            parameter.requires_grad = True
            params.append(parameter)
    model.text_encoder.eval()
    return params


@torch.no_grad()
def encode_audio_batch(
    vae: AutoencoderOobleck,
    audio_paths: list[str],
    *,
    duration: float,
    sample_rate: int,
    device: torch.device,
) -> tuple[torch.Tensor | None, list[int]]:
    """Encode audios; skip missing/empty/corrupt files.

    Returns (latents, valid_indices). latents is None when nothing loaded.
    """
    waveforms: list[torch.Tensor] = []
    valid_indices: list[int] = []
    for index, path in enumerate(audio_paths):
        waveform = load_audio(path, duration, sample_rate)
        if waveform is None:
            continue
        waveforms.append(waveform)
        valid_indices.append(index)
    if not waveforms:
        return None, []
    stacked = torch.stack(waveforms).to(device)
    latents = vae.encode(stacked).latent_dist.sample().transpose(1, 2)
    return latents, valid_indices


def filter_batch(batch: dict[str, list[Any]], valid_indices: list[int]) -> dict[str, list[Any]]:
    return {key: [values[i] for i in valid_indices] for key, values in batch.items()}


def batch_ready_on_all_ranks(
    accelerator: Accelerator, local_count: int
) -> bool:
    """True only if every rank has the same positive sample count (avoids DDP hang)."""
    count = torch.tensor(
        [local_count],
        device=accelerator.device,
        dtype=torch.int32,
    )
    gathered = accelerator.gather(count)
    return bool(
        torch.all(gathered > 0).item()
        and torch.all(gathered == gathered[0]).item()
    )


@torch.no_grad()
def graph_discrimination(model: TangoFluxDEG) -> dict[str, float]:
    descriptions = [
        [["Dog Barking"], [1.0], [2.0]],
        [["Fireworks"], [1.0], [3.0]],
        [["Ocean Waves"], [0.0], [10.0]],
        [["Man Speaking"], [0.0], [10.0]],
    ]
    features, mask = model.encode_event_graph(descriptions, duration=10.0)
    pooled = torch.stack(
        [features[i, mask[i]].mean(dim=0) for i in range(len(descriptions))]
    )
    normalized = torch.nn.functional.normalize(pooled, dim=-1)
    cosine = normalized @ normalized.T
    off_diagonal = cosine[~torch.eye(4, dtype=torch.bool, device=cosine.device)]
    relative_distances = []
    for i in range(4):
        for j in range(i + 1, 4):
            denominator = (pooled[i].norm() + pooled[j].norm()) / 2
            relative_distances.append(
                (pooled[i] - pooled[j]).norm() / denominator.clamp(min=1e-8)
            )
    return {
        "graph/mean_offdiag_cosine": float(off_diagonal.mean()),
        "graph/min_pair_relative_distance": float(torch.stack(relative_distances).min()),
        "graph/feature_std": float(pooled.std(dim=0).mean()),
    }


def save_trainable_checkpoint(
    accelerator: Accelerator,
    model: torch.nn.Module,
    path: Path,
    *,
    epoch: int,
    val_loss: float,
) -> None:
    if not accelerator.is_main_process:
        return
    unwrapped = accelerator.unwrap_model(model)
    state = {
        key: value.detach().cpu().contiguous()
        for key, value in unwrapped.state_dict().items()
        if not key.startswith("text_encoder.")
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    save_file(state, str(path), metadata={"epoch": str(epoch), "val_loss": str(val_loss)})
    print(f"[checkpoint] saved {path}", flush=True)


def main() -> None:
    args = parse_args()
    with Path(args.config).open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    train_cfg = cfg["training"]
    paths = cfg["paths"]
    tracking = cfg.get("tracking", {})
    if args.epochs is not None:
        train_cfg["num_train_epochs"] = args.epochs
    if args.output_dir:
        paths["output_dir"] = args.output_dir
    if args.disable_tracking:
        tracking["enabled"] = False

    accelerator = Accelerator(
        gradient_accumulation_steps=int(train_cfg["gradient_accumulation_steps"]),
        mixed_precision=None
        if str(train_cfg.get("mixed_precision", "no")) == "no"
        else str(train_cfg["mixed_precision"]),
        log_with="wandb" if tracking.get("enabled", False) else None,
    )
    set_seed(int(train_cfg["seed"]), device_specific=True)
    output_dir = Path(paths["output_dir"])
    if accelerator.is_main_process:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "config.json").write_text(
            json.dumps(cfg, indent=2), encoding="utf-8"
        )
    accelerator.wait_for_everyone()

    train_dataset = AudioCapsDEGDataset(
        paths["train_file"],
        audio_root_from=paths["audio_root_from"],
        audio_root_to=paths["audio_root_to"],
    )
    val_dataset = AudioCapsDEGDataset(
        paths["val_file"],
        audio_root_from=paths["audio_root_from"],
        audio_root_to=paths["audio_root_to"],
    )
    if args.num_examples > 0:
        train_dataset.records = train_dataset.records[: args.num_examples]
        val_dataset.records = val_dataset.records[: max(8, args.num_examples // 10)]

    train_loader = DataLoader(
        train_dataset,
        shuffle=True,
        batch_size=int(train_cfg["per_device_batch_size"]),
        num_workers=int(train_cfg["num_workers"]),
        pin_memory=True,
        collate_fn=AudioCapsDEGDataset.collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        shuffle=False,
        batch_size=int(train_cfg["per_device_batch_size"]),
        num_workers=int(train_cfg["num_workers"]),
        pin_memory=True,
        collate_fn=AudioCapsDEGDataset.collate_fn,
    )

    snapshot = resolve_tangoflux_snapshot(
        paths["pretrained_repo"],
        paths.get("pretrained_revision"),
    )
    model = TangoFluxDEG(config=cfg["model"])
    if not args.resume:
        load_tangoflux_initialization(model, snapshot)
    params = trainable_parameters(model)
    optimizer = torch.optim.AdamW(
        params,
        lr=float(train_cfg["learning_rate"]),
        betas=(float(train_cfg["adam_beta1"]), float(train_cfg["adam_beta2"])),
        eps=float(train_cfg["adam_epsilon"]),
        weight_decay=float(train_cfg["weight_decay"]),
    )

    vae = AutoencoderOobleck()
    vae.load_state_dict(load_file(str(snapshot / "vae.safetensors")))
    vae.requires_grad_(False).eval().to(accelerator.device)

    gradient_accumulation_steps = int(train_cfg["gradient_accumulation_steps"])
    num_update_steps_per_epoch = math.ceil(
        len(train_loader) / gradient_accumulation_steps
    )
    total_updates = num_update_steps_per_epoch * int(train_cfg["num_train_epochs"])
    scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=int(train_cfg["num_warmup_steps"])
        * gradient_accumulation_steps
        * accelerator.num_processes,
        num_training_steps=total_updates * gradient_accumulation_steps,
    )
    model, optimizer, train_loader, val_loader, scheduler = accelerator.prepare(
        model, optimizer, train_loader, val_loader, scheduler
    )
    start_epoch = 1
    best_val = float("inf")
    global_step = 0
    if args.resume:
        accelerator.load_state(args.resume)
        trainer_state_path = Path(args.resume) / "trainer_state.json"
        if not trainer_state_path.exists():
            raise FileNotFoundError(
                f"Missing resume metadata: {trainer_state_path}"
            )
        trainer_state = json.loads(
            trainer_state_path.read_text(encoding="utf-8")
        )
        start_epoch = int(trainer_state["epoch"]) + 1
        best_val = float(trainer_state["best_val"])
        global_step = int(trainer_state["global_step"])

    if tracking.get("enabled", False):
        accelerator.init_trackers(
            tracking.get("project", "degdit-tangoflux"),
            config=cfg,
            init_kwargs={"wandb": {"name": tracking.get("run_name")}},
        )

    accelerator.print(
        f"train={len(train_dataset)} val={len(val_dataset)} "
        f"trainable={sum(p.numel() for p in params):,} "
        f"epochs={train_cfg['num_train_epochs']} total_updates={total_updates}"
    )

    max_duration = float(train_cfg["max_audio_duration"])
    sample_rate = int(train_cfg["sample_rate"])
    log_every = int(train_cfg["log_every_steps"])
    optimizer.zero_grad()

    for epoch in range(
        start_epoch,
        int(train_cfg["num_train_epochs"]) + 1,
    ):
        model.train()
        accelerator.unwrap_model(model).text_encoder.eval()
        progress = tqdm(
            train_loader,
            disable=not accelerator.is_local_main_process,
            desc=f"epoch {epoch}",
        )
        train_loss_sum = 0.0
        train_batches = 0
        for batch in progress:
            latents, valid_indices = encode_audio_batch(
                vae,
                batch["audio_path"],
                duration=max_duration,
                sample_rate=sample_rate,
                device=accelerator.device,
            )
            if not batch_ready_on_all_ranks(accelerator, len(valid_indices)):
                continue
            assert latents is not None
            batch = filter_batch(batch, valid_indices)
            with accelerator.accumulate(model):
                durations = torch.tensor(
                    batch["duration"], device=accelerator.device
                ).clamp(max=max_duration)
                loss, _, _, _ = model(
                    latents,
                    batch["text"],
                    event_description=batch["graph"],
                    duration=durations,
                )
                accelerator.backward(loss)
                if accelerator.sync_gradients:
                    graph_params = accelerator.unwrap_model(model).graph_transformer.parameters()
                    graph_grad_sq = sum(
                        parameter.grad.detach().float().norm().square()
                        for parameter in graph_params
                        if parameter.grad is not None
                    )
                    graph_grad_norm = graph_grad_sq.sqrt()
                    accelerator.clip_grad_norm_(
                        params, float(train_cfg["max_grad_norm"])
                    )
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            train_loss_sum += float(loss.detach())
            train_batches += 1
            if accelerator.sync_gradients:
                global_step += 1
                progress.set_postfix(loss=f"{float(loss.detach()):.4f}")
                if global_step % log_every == 0:
                    metrics = {
                        "train/loss": float(loss.detach()),
                        "train/lr": scheduler.get_last_lr()[0],
                        "train/graph_grad_norm": float(graph_grad_norm),
                        "epoch": epoch,
                    }
                    accelerator.log(metrics, step=global_step)

        model.eval()
        val_sum = torch.tensor(0.0, device=accelerator.device)
        val_count = torch.tensor(0.0, device=accelerator.device)
        for batch in tqdm(
            val_loader,
            disable=not accelerator.is_local_main_process,
            desc=f"val {epoch}",
        ):
            with torch.no_grad():
                latents, valid_indices = encode_audio_batch(
                    vae,
                    batch["audio_path"],
                    duration=max_duration,
                    sample_rate=sample_rate,
                    device=accelerator.device,
                )
                if not batch_ready_on_all_ranks(accelerator, len(valid_indices)):
                    continue
                assert latents is not None
                batch = filter_batch(batch, valid_indices)
                durations = torch.tensor(
                    batch["duration"], device=accelerator.device
                ).clamp(max=max_duration)
                val_loss, _, _, _ = model(
                    latents,
                    batch["text"],
                    event_description=batch["graph"],
                    duration=durations,
                )
            gathered = accelerator.gather_for_metrics(
                val_loss.detach().repeat(len(batch["text"]))
            )
            val_sum += gathered.sum()
            val_count += gathered.numel()

        val_loss_value = float((val_sum / val_count.clamp(min=1)).cpu())
        train_loss_value = train_loss_sum / max(train_batches, 1)
        graph_metrics = graph_discrimination(accelerator.unwrap_model(model))
        epoch_metrics = {
            "epoch": epoch,
            "epoch/train_loss": train_loss_value,
            "epoch/val_loss": val_loss_value,
            **graph_metrics,
        }
        accelerator.print(json.dumps(epoch_metrics, sort_keys=True))
        accelerator.log(epoch_metrics, step=global_step)

        if val_loss_value < best_val:
            best_val = val_loss_value
            save_trainable_checkpoint(
                accelerator,
                model,
                output_dir / "best_val.safetensors",
                epoch=epoch,
                val_loss=val_loss_value,
            )
        if epoch % int(train_cfg["checkpoint_every_epochs"]) == 0:
            save_trainable_checkpoint(
                accelerator,
                model,
                output_dir / f"epoch_{epoch}.safetensors",
                epoch=epoch,
                val_loss=val_loss_value,
            )
            accelerator.wait_for_everyone()
            latest_state = output_dir / "latest_state"
            accelerator.save_state(str(latest_state))
            if accelerator.is_main_process:
                (latest_state / "trainer_state.json").write_text(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "best_val": best_val,
                            "global_step": global_step,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
        accelerator.wait_for_everyone()

    save_trainable_checkpoint(
        accelerator,
        model,
        output_dir / "last.safetensors",
        epoch=int(train_cfg["num_train_epochs"]),
        val_loss=val_loss_value,
    )
    accelerator.wait_for_everyone()
    accelerator.save_state(str(output_dir / "last_state"))
    accelerator.end_training()


if __name__ == "__main__":
    main()
