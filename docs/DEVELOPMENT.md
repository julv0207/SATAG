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

CSS and JavaScript URLs in `index.html` include a `?v=` content hash (the first
12 characters of the file's SHA-256). Refresh the corresponding hash when
changing these files so returning visitors do not combine new HTML with cached
rendering code or sample data from an earlier deployment.

## Connect SATAG samples

The published **Comparison Across Overlap Ratios** section now uses
`overlap-samples.js`, with nine pairs and five actual audio outputs per pair.
Refresh this section independently with:

```bash
python scripts/prepare_overlap_assets.py --source ../Overlap_Comparison_10.html
```

The extractor validates row labels, all five method/overlap conditions, requested
intervals, image labels, and embedded media types before writing. It copies the
50 MP3s and 50 PNGs without re-encoding and records source/asset SHA-256 hashes.
The 0% intervals are A 0.73–4.31 s / B 5.77–9.35 s; 50% uses A 1.13–5.33 s /
B 3.23–7.43 s; 100% uses 1.13–5.33 s for both events. These are the source
comparison's conditions, not the different Figure 1 overlapping conditions.
The author excluded only `09738_telephone_ringing__woman_giving_a_speech` from
the published rows. `EXCLUDED_PAIR_IDS` retains that choice on regeneration;
the original source and its media remain intact.
Desktop shows a nine-row, five-condition table; narrower screens group all five
players under each pair with method labels and explicit timing. No tabs or
pair selector are used. The old `comparisons` field in `samples.js` and baseline
assets remain as legacy source data and are no longer rendered on the page.

### Legacy comparison data

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

- Figure 1 audio: `Fig1 AudioFile/AudioCaps_TalkMeow_TypeChirp_Muted_Mels.html`
  for DegDiT (a-d), and the masked variants in
  `Fig1 AudioFile/AudioCaps_TalkMeow_TypeChirp_SATAG_Muted_Mels.html` for SATAG (e-f).
  All six clips are silenced outside the union of the requested event intervals.
  The separate DegDiT MP3 files in `원본 Wav` differ from the figure clips;
  they must not be substituted silently. SATAG e/f match the separate MP3 files.
- Figure 1 images: existing manuscript-matched a-d assets, plus the author's
  `satag-typechirp-50.png` (e) and `satag-talkmeow-100.png` (f). All six PNGs
  remain byte-for-byte intact. `imageCrop` metadata clips their top 95 pixels
  in both the table and enlarged viewer, removing numeric labels above the
  plots while keeping the colored event boxes and bottom time axes.
- Header, Abstract, Figure 1 panel labels/timing, and the linked paper:
  `SATAG 0923 수정본.pdf`. Abstract wording is transcribed verbatim, with
  typesetting line breaks and split words removed.
- Baselines: `AudioCaps_TalkMeow_TypeChirp_Times.html`, six original `s00` clips.
  Source header: DegDiT joint, epoch 90, CFG 4.0, 50 steps.
- Comparison Across Overlap Ratios: `Overlap_Comparison_10.html`, nine published
  pairs from the ten source pairs, in their supplied order. Telephone Ringing +
  Woman Giving A Speech is excluded at the author's request.
  The 0% DegDiT output is the common non-overlap reference. Images are used
  exactly as supplied and already contain no top numeric labels.
- AudioCapsT examples: five samples drawn from the ten evaluation CSVs in
  `Dataset 평가/결과`, filtering for `decision == accurate` and blank `issues`
  (840 of 1,000 records). `scripts/prepare_audiocaps_samples.py` uses seed
  `20260923`, sorted CSV filenames, source row order, and sampling without
  replacement. Selected IDs: `hqtGOGfZaOI`, `2YmcQSvWAN8`, `GD4fETZRtSc`,
  `0j94maKQDLY`, `8nOUvamr2PE`. It copies audio from the matching evaluation
  HTML without re-encoding, checks both captions against the CSV, and preserves
  every event interval at source precision. Selection and source hashes live in
  `assets/audiocaps-selection.json`; the page reads `audiocaps-samples.js`.
  Run the extractor from the repository root to reproduce the same selection.
  The older three entries in `samples.js` are legacy data and are not rendered.
- Mixing-control examples: `음향 조절 예시.html`, two published event pairs
  (Dog Barking + Bird Chirping and Car Horn Honking + Waves Crashing) with three
  conditions each: raw summation, main/background 7:3, and 3:7.
  The no-user-ratio amplitude-normalized condition is intentionally excluded.
  Audio, mel spectrograms, peak values, seed, overlap interval, and reported
  per-pair inference times are extracted from the supplied source.
  The standalone Relative Amplitude Control section follows the overlap table
  and shows both pairs at once: raw summation, 7:3, and 3:7. The old pair selector
  and separate Method presentation have been replaced by this six-player table;
  the framework image remains available as a source asset. No media was changed.
  Amplitude plots use CSS cropping to show only the mel spectrogram, removing
  Hz/time axes and surrounding margins: source 660 × 235, crop rectangle
  (64, 4)–(650, 192). This applies to thumbnails and the enlarged viewer;
  source PNGs remain unchanged. The comparison layout keeps its original size.
- BibTeX uses the supplied manuscript title and author names, plus the repository
  URL. Publication year and venue are omitted until confirmed. A copy button
  copies the visible citation with a live success or manual-copy message.
- Existing framework asset: `Template.pdf`. The legacy Temporal generation results
  section and Table 1 were removed at the author's request; AudioCapsT is followed
  directly by BibTeX.
- Layout reference for the paper header and audio comparison table:
  https://sakshamsingh1.github.io/diff-sage/ .
  No reference-site text, generated audio, or model results have been copied.

`assets/provenance.json` records SHA-256 hashes and source filenames for extracted media.
Audio is extracted from the HTML verbatim, without another normalization or encoding pass.
The existing framework figure is rasterized from page 2 of `Template.pdf`.

To update only Figure 1 from the local source folder (standard library only):

```bash
python scripts/prepare_fig1_assets.py --source "../Fig1 AudioFile" --paper "../../SATAG 0923 수정본.pdf"
```

Add `--satag-figures PATH` to import the two author-supplied PNGs initially;
subsequent runs preserve and verify the published PNG bytes and crop metadata.

This preserves the dataset, general comparison, and amplitude-control samples.
`paper.css` styles the header, Abstract, and Figure 1. The Figure 1 table shows
two event-pair rows and three method/overlap columns on desktop, then stacks
each pair's three samples on narrow screens. Labels remain lowercase (a-f).

To regenerate source assets (development dependencies: `beautifulsoup4`, `pymupdf`):

```bash
python scripts/prepare_demo_assets.py --source /workspace
```

The legacy script preserves a completed six-panel Figure 1, its linked paper, and connected
`satag` comparison entries, but regenerates the baseline metadata.
No training/inference is run by this script or the website.

## Content still awaiting author confirmation

- The supplied nine-pair SATAG comparison and existing mixing examples are now
  connected; additional or replacement examples require author-supplied outputs.
- Manuscript draft: abstract/conclusion and MOS are unfinished; no MOS is shown.
- Table 1 is reproduced as written, including lower SATAG Event Recall at 100% overlap.
  Confirm these draft numbers before the final research release.
- Draft Table 1 uses an epoch-100 experiment; demo source clips use epoch 90.

## Manual verification

Check all six Figure 1 players, both event pairs and the three columns,
exclusive playback, spectrogram modal (including Escape), keyboard focus, download
links, and phone/desktop layouts. A missing SATAG file must not result in a fake player.
For the overlap section, confirm nine rows, five clips per row, the matching
method/time headers, and one active audio player across sections. Verify the
first and last row's audio, spectrograms, and downloads on desktop and mobile.
For Relative Amplitude Control, verify both event pairs, all six clips,
main/background labels, ratio ordering, enlargement, and one-player playback.
Test at the repository subpath `/SATAG/` before enabling Pages.
