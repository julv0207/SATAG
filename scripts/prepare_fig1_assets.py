"""Refresh only the six Fig. 1 samples from approved HTML, Git, and PNG sources.

Usage: python scripts/prepare_fig1_assets.py --source "../Fig1 AudioFile" --paper PATH
Use --satag-figures DIR to replace e/f with the author's supplied PNGs.
Uses the standard library. Media bytes are preserved; imageCrop metadata hides
all six images' top numeric labels only in the page and enlarged viewer.
"""

import argparse
import base64
import hashlib
import json
import struct
import subprocess
from html.parser import HTMLParser
from pathlib import Path

PREFIX = "window.SATAG_SAMPLES = "
SOURCE_FILES = {
    "DegDiT": "AudioCaps_TalkMeow_TypeChirp_Muted_Mels.html",
    "SATAG": "AudioCaps_TalkMeow_TypeChirp_SATAG_Muted_Mels.html",
}
PAIR_EVENTS = {
    "keyboard-bird": ["Keyboard Typing", "Bird Chirping"],
    "speech-cat": ["Man Talking", "Cat Meowing"],
}
CONDITIONS = {
    0: [[0.73, 4.31], [5.77, 9.35]],
    50: [[1.31, 5.87], [3.59, 8.15]],
    100: [[2.24, 6.97], [2.24, 6.97]],
}
# HTML article index and media index are explicit: the SATAG source presents
# unmasked media first and masked media second. Fig. 1 uses the latter.
PANELS = [
    ("a", "keyboard-bird", 0, "DegDiT", 1, 0, "Brid Chirping Keyboard Typing 0 overlap.mp3"),
    ("b", "speech-cat", 0, "DegDiT", 2, 0, "Man Talkng Cat meowing 0 overlap.mp3"),
    ("c", "keyboard-bird", 50, "DegDiT", 0, 0, "Brid Chirping Keyboard Typing 50 overlap.mp3"),
    ("d", "speech-cat", 100, "DegDiT", 3, 0, "Man Talkng Cat meowing 100 overlap.mp3"),
    ("e", "keyboard-bird", 50, "SATAG", 2, 1, "Keyboard Typing × Bird Chirping · 50% SATAG ver.mp3"),
    ("f", "speech-cat", 100, "SATAG", 5, 1, "Man Talking × Cat Meowing · 100% SATAG ver.mp3"),
]
PROCESSING = "Supplied audio is silenced outside the union of the requested event intervals."
FIGURE_REVISION = "603851800eea3e76795ef25c88036aa022cc7483"
FIGURE_IMAGE_HASHES = {
    "a": "21d25693d62e2512472da4eb99675d2d5934a2e521aaebc97d7aa898439bcfbc",
    "b": "0bddb4b046a24aefc1ca51a97fd35518a821a8710cc8b9e388687e1c75ddb5dd",
    "c": "0b9d289721173508416b61e920e8ca195f1671c6217a42456ab0687bb154b667",
    "d": "37c607dc641c44a232f4a3324092ac9805bc1b6223253734def20672f797f257",
}


class ArticleParser(HTMLParser):
    """Read text and media attributes without copying data URLs into logs."""

    def __init__(self):
        super().__init__()
        self.articles = []
        self.current = None
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.current = {"heading": [], "audio": [], "img": []}
            self.articles.append(self.current)
        if self.current is not None:
            if tag == "h2":
                self.in_heading = True
            if tag in ("audio", "img"):
                self.current[tag].append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_heading = False
        if tag == "article":
            self.current = None

    def handle_data(self, data):
        if self.current is not None and self.in_heading:
            self.current["heading"].append(data)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--satag-figures", type=Path)
    args = parser.parse_args()
    docs = Path(__file__).resolve().parents[1] / "docs"
    assets = docs / "assets"
    sample_path = docs / "samples.js"
    existing_text = sample_path.read_text(encoding="utf-8")
    if not existing_text.startswith(PREFIX):
        raise ValueError("Unexpected samples.js assignment")
    samples = json.loads(existing_text.removeprefix(PREFIX).strip().removesuffix(";"))
    provenance_path = assets / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    known_provenance = {entry["asset"]: entry for entry in provenance}
    provenance = [entry for entry in provenance if not entry["asset"].startswith("assets/fig1-")]
    paper_asset = "assets/SATAG-draft.pdf"
    paper_hash = sha256(args.paper.read_bytes())
    if sha256((docs / paper_asset).read_bytes()) != paper_hash:
        raise ValueError("Copy the supplied paper into docs/assets/SATAG-draft.pdf first")

    def figure_image(panel, asset):
        if panel in "abcd":
            # The supplied HTML has differently annotated PNGs. Retain the
            # sharper original a-d images whose annotations match the paper.
            local_path = docs / asset
            data = local_path.read_bytes() if local_path.exists() else b""
            if sha256(data) != FIGURE_IMAGE_HASHES[panel]:
                data = subprocess.check_output(
                    ["git", "show", f"{FIGURE_REVISION}:docs/{asset}"], cwd=docs.parent
                )
            entry = {
                "asset": asset,
                "source": "https://github.com/julv0207/SATAG",
                "source_revision": FIGURE_REVISION,
                "source_path": f"docs/{asset}",
            }
        else:
            filename = "satag-typechirp-50.png" if panel == "e" else "satag-talkmeow-100.png"
            if args.satag_figures:
                data = (args.satag_figures / filename).read_bytes()
                entry = {"asset": asset, "source": filename}
            else:
                entry = known_provenance.get(asset, {}).copy()
                if entry.get("source") != filename or "display_crop" not in entry:
                    raise ValueError("Use --satag-figures to supply the author's approved e/f PNGs")
                data = (docs / asset).read_bytes()
                if sha256(data) != entry["sha256"]:
                    raise ValueError(f"Published SATAG image provenance mismatch: {asset}")
        if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", data[16:24]) != (1420, 603):
            raise ValueError(f"Unexpected source image dimensions for panel {panel}")
        entry["display_crop"] = {"top": 95, "width": 1420, "height": 603}
        entry["processing"] = "Original PNG bytes; CSS hides top numeric labels in thumbnail and enlarged viewer."
        if panel in FIGURE_IMAGE_HASHES and sha256(data) != FIGURE_IMAGE_HASHES[panel]:
            raise ValueError(f"Approved Fig. 1 image mismatch for panel {panel}")
        entry["sha256"] = sha256(data)
        return data, entry

    sources = {}
    for method, filename in SOURCE_FILES.items():
        html = ArticleParser()
        html.feed((args.source / filename).read_text(encoding="utf-8"))
        expected = 4 if method == "DegDiT" else 6
        if len(html.articles) != expected:
            raise ValueError(f"Expected {expected} {method} source articles")
        sources[method] = html.articles

    figure = []
    prepared = []
    for panel, pair, overlap, method, article_index, media_index, standalone in PANELS:
        article = sources[method][article_index]
        heading = " ".join(article["heading"])
        if not all(name in heading for name in PAIR_EVENTS[pair]) or f"{overlap}%" not in heading:
            raise ValueError(f"Unexpected source heading for panel {panel}: {heading}")
        media_count = 1 if method == "DegDiT" else 2
        if len(article["audio"]) != media_count or len(article["img"]) != media_count:
            raise ValueError(f"Unexpected media count for panel {panel}")
        method_suffix = "-satag" if method == "SATAG" else ""
        stem = f"fig1-{pair}{method_suffix}-{overlap}"
        sample = {
            "id": stem,
            "panel": panel,
            "pair": pair,
            "method": method,
            "overlap": overlap,
            "events": [
                {"name": name, "start": interval[0], "end": interval[1]}
                for name, interval in zip(PAIR_EVENTS[pair], CONDITIONS[overlap])
            ],
            "duration": 10,
        }
        for tag, key, mime, extension in [
            ("audio", "audio", "audio/mpeg", "mp3"),
            ("img", "image", "image/png", "png"),
        ]:
            asset = f"assets/{stem}.{extension}"
            if tag == "img":
                data, entry = figure_image(panel, asset)
                prepared.append((docs / asset, data))
                sample[key] = asset
                if "display_crop" in entry:
                    sample["imageCrop"] = entry["display_crop"]
                provenance.append(entry)
                continue
            header, payload = article[tag][media_index]["src"].split(",", 1)
            if header != f"data:{mime};base64":
                raise ValueError(f"Unexpected {tag} format for panel {panel}: {header}")
            data = base64.b64decode(payload, validate=True)
            prepared.append((docs / asset, data))
            sample[key] = asset
            entry = {
                "asset": asset,
                "source": f"Fig1 AudioFile/{SOURCE_FILES[method]}",
                "source_article_index": article_index,
                "source_media_index": media_index,
                "sha256": sha256(data),
                "processing": PROCESSING,
            }
            if tag == "audio":
                standalone_path = args.source / "원본 Wav" / standalone
                standalone_hash = sha256(standalone_path.read_bytes())
                entry["standalone_source"] = f"Fig1 AudioFile/원본 Wav/{standalone}"
                entry["standalone_sha256"] = standalone_hash
                entry["standalone_matches"] = standalone_hash == entry["sha256"]
                if method == "SATAG" and not entry["standalone_matches"]:
                    raise ValueError(f"SATAG standalone no longer matches the selected HTML audio: {panel}")
            provenance.append(entry)
        figure.append(sample)

    provenance = [entry for entry in provenance if entry["asset"] != paper_asset]
    provenance.append({"asset": paper_asset, "source": args.paper.name, "sha256": paper_hash})

    # All checks precede writes. Preserve every non-Fig. 1 sample section.
    for path, data in prepared:
        path.write_bytes(data)
    samples["figure"] = figure
    sample_path.write_text(PREFIX + json.dumps(samples, indent=2) + ";\n", encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(figure)} Fig. 1 clips and {len(prepared)} byte-preserved assets.")
    print("Preserved dataset, comparisons, mixing, and non-Fig. 1 provenance.")


if __name__ == "__main__":
    main()
