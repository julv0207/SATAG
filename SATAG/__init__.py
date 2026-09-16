"""SATAG inference: source-wise mix and amplitude control on DegDiT."""

from .sourcewise_mix import mix_waveforms, resolve_amplitude_ratios

__all__ = ["mix_waveforms", "resolve_amplitude_ratios"]
