# SATAG project page

Dependency-free static demo. Open `index.html` directly or serve locally:

```bash
python -m http.server 8000 --directory docs
```

## GitHub Pages

After these files are merged into `main`, open the repository's **Settings → Pages**.
Choose **Deploy from a branch**, branch **main**, folder **/docs**, and Save.
The project URL is `https://julv0207.github.io/SATAG/`.
The README badge already points there; it will work once Pages is enabled and its deployment succeeds.
All local asset paths are relative, so the site works under `/SATAG/` as well as locally.

No build step, API key, CDN, or backend is required. `samples.js` is a plain JS data file,
so the page also works via `file://` without JSON fetch/CORS restrictions.

## Connect SATAG samples

Find the matching `id` in `samples.js`. Replace only its `satag: null` with:

```javascript
"satag": {
  "audio": "assets/satag-keyboard-bird-50.wav",
  "image": "assets/satag-keyboard-bird-50.png",
  "note": "Matched SATAG output · describe checkpoint / seed"
}
```

Place those actual files in `assets/`. `image` is optional. Keep the same events, target
timestamps, checkpoint, sampling configuration, duration and declared postprocessing
as the baseline, or disclose any difference in the sample notes / protocol text.
Never relabel a baseline clip as SATAG or synthesize a comparison from masked joint outputs.
The empty SATAG panel is intentional until real matched outputs are provided.

## Sources

- Figure 1: `AudioCaps_TalkMeow_TypeChirp_Muted_Mels.html`, all four clips and spectrograms.
  These clips have been silenced outside the union of the target event intervals.
- Baselines: `AudioCaps_TalkMeow_TypeChirp_Times.html`, six original `s00` clips.
  Source header: DegDiT joint, epoch 90, CFG 4.0, 50 steps.
- AudioCaps-T examples: `AudioCaps_Duration_SpotSound_Qualitative_100.html`, IDs
  `4YMXgLFcR94`, `BMayJId0X1s`, and `c6YJgZ3qzOw`. Audio is extracted verbatim;
  captions and SpotSound intervals are parsed from the same source file.
- Mixing-control examples: `음향 조절 예시.html`, two published event pairs
  (Dog Barking + Bird Chirping and Car Horn Honking + Waves Crashing) with three
  conditions each: raw summation, main/background 7:3, and 3:7.
  The no-user-ratio amplitude-normalized condition is intentionally excluded.
  Audio, mel spectrograms, peak values, seed, overlap interval, and reported
  per-pair inference times are extracted from the supplied source.
- Framework image, manuscript, author names and Table 1: `Template.pdf`.
- Structure reference: https://control-audio.github.io/Control-Audio/ .
  No reference-site text, generated audio, or model results have been copied.

`assets/provenance.json` records SHA-256 hashes and source filenames for extracted media.
Media is extracted from the HTML verbatim, without another normalization or encoding pass.
The framework figure is rasterized from page 2 of the supplied PDF.

To regenerate source assets (development dependencies: `beautifulsoup4`, `pymupdf`):

```bash
python scripts/prepare_demo_assets.py --source /workspace
```

The script preserves connected `satag` entries, but regenerates the baseline metadata.
No training/inference is run by this script or the website.

## Content still awaiting author confirmation

- Actual SATAG comparison clips and optional mixing-ratio demonstrations.
- Manuscript draft: abstract/conclusion and MOS are unfinished; no MOS is shown.
- Table 1 is reproduced as written, including lower SATAG Event Recall at 100% overlap.
  Confirm these draft numbers before the final research release.
- Draft Table 1 uses an epoch-100 experiment; demo source clips use epoch 90.

## Manual verification

Check all four Figure 1 players, both event pairs at all three overlap conditions,
exclusive playback, spectrogram modal (including Escape), keyboard focus, download
links, and phone/desktop layouts. A missing SATAG file must not result in a fake player.
Test at the repository subpath `/SATAG/` before enabling Pages.
