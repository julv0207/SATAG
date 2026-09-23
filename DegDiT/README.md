# DegDiT

원본 DegDiT 학습 코드입니다. TangoFlux backbone + Dynamic Event Graph(DEG)로
AudioCaps-style JSONL을 학습합니다.

```bash
accelerate launch --num_processes 1 train.py \
  --config configs/tangoflux_deg_audiocaps.yaml
```

데이터 경로는 `configs/tangoflux_deg_audiocaps.yaml`의 `paths`를 환경에 맞게 바꿉니다.
추론과 source-wise mix는 상위 `SATAG/`와 `infer.py`를 사용합니다.
