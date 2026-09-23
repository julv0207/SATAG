"""Extract the ten-pair comparison without re-encoding any audio or images.

python scripts/prepare_overlap_assets.py --source ../Overlap_Comparison_10.html
Only the comparison assets, overlap-samples.js, and their provenance are updated.
"""

import argparse
import base64
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


CONDITIONS = [
    ("DegDiT", 0, [[0.73, 4.31], [5.77, 9.35]]),
    ("DegDiT", 50, [[1.13, 5.33], [3.23, 7.43]]),
    ("DegDiT", 100, [[1.13, 5.33], [1.13, 5.33]]),
    ("SATAG", 50, [[1.13, 5.33], [3.23, 7.43]]),
    ("SATAG", 100, [[1.13, 5.33], [1.13, 5.33]]),
]

# Keep the source media intact; omit only the row excluded by the author.
EXCLUDED_PAIR_IDS = {"09738_telephone_ringing__woman_giving_a_speech"}


class ComparisonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pairs = []
        self.pair = None
        self.clip = None
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "article" and "pair" in classes:
            self.pair = {"title": "", "id": "", "clips": []}
            self.pairs.append(self.pair)
            self.clip = None
        if self.pair is None:
            return
        if tag == "h3":
            self.capture = (tag, self.pair, "title")
        elif tag == "p" and "pid" in classes:
            self.capture = (tag, self.pair, "id")
        elif tag == "div" and "clip" in classes:
            self.clip = {"label": "", "intervals": []}
            self.pair["clips"].append(self.clip)
        elif tag == "div" and "clip-label" in classes:
            self.capture = (tag, self.clip, "label")
        elif self.clip is not None:
            if tag in ("img", "audio"):
                self.clip[tag] = attrs
            elif tag == "i" and ("a" in classes or "b" in classes):
                style = attrs.get("style", "")
                left = float(re.search(r"left:([\d.]+)%", style)[1])
                width = float(re.search(r"width:([\d.]+)%", style)[1])
                self.clip["intervals"].append([round(left / 10, 2), round((left + width) / 10, 2)])

    def handle_data(self, data):
        if self.capture:
            _, obj, key = self.capture
            obj[key] += data

    def handle_endtag(self, tag):
        if self.capture and self.capture[0] == tag:
            self.capture = None
        if tag == "article":
            self.pair = None
            self.clip = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    docs = Path(__file__).resolve().parents[1] / "docs"
    source = args.source.read_bytes()
    html = ComparisonParser()
    html.feed(source.decode("utf-8"))
    if len(html.pairs) != 10 or len({p["id"] for p in html.pairs}) != 10:
        raise ValueError("Expected ten distinct source event pairs")
    records = []
    prepared = []
    source_hash = hashlib.sha256(source).hexdigest()
    provenance_path = docs / "assets/provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance = [p for p in provenance if not p["asset"].startswith("assets/overlap-")]
    for pair in html.pairs:
        names = pair["title"].strip().split(" + ")
        pair_id = pair["id"].strip()
        if len(names) != 2 or len(pair["clips"]) != 5 or not re.fullmatch(r"[a-z0-9_]+", pair_id):
            raise ValueError(f"Invalid source event pair: {pair_id}")
        record = {"id": pair_id, "events": names, "clips": []}
        for clip, (method, overlap, intervals) in zip(pair["clips"], CONDITIONS):
            label = f"{method} {overlap}%"
            if clip["label"].strip() != label or clip["intervals"] != intervals:
                raise ValueError(f"Unexpected method/timing for {pair_id}: {clip['label']}")
            if clip["img"].get("alt") != f"{pair['title'].strip()} {label}":
                raise ValueError(f"Spectrogram label mismatch for {pair_id}: {label}")
            stem = f"overlap-{pair_id}-{method.lower()}-{overlap}"
            sample = {"id": stem, "method": method, "overlap": overlap, "duration": 10,
                      "events": [{"name": name, "start": start, "end": end}
                                 for name, (start, end) in zip(names, intervals)]}
            for tag, key, mime, ext in [("audio", "audio", "audio/mpeg", "mp3"), ("img", "image", "image/png", "png")]:
                header, payload = clip[tag]["src"].split(",", 1)
                if header != f"data:{mime};base64":
                    raise ValueError(f"Unexpected embedded {key} format: {header}")
                data = base64.b64decode(payload, validate=True)
                asset = f"assets/{stem}.{ext}"
                sample[key] = asset
                prepared.append((docs / asset, data))
                provenance.append({"asset": asset, "source": args.source.name,
                                   "source_sha256": source_hash, "source_pair_id": pair_id,
                                   "source_condition": label, "sha256": hashlib.sha256(data).hexdigest()})
            record["clips"].append(sample)
        if pair_id not in EXCLUDED_PAIR_IDS:
            records.append(record)
    # Write only after validating every row, condition, and media payload.
    for path, data in prepared:
        path.write_bytes(data)
    (docs / "overlap-samples.js").write_text(
        "window.SATAG_OVERLAP_SAMPLES = " + json.dumps(records, indent=2) + ";\n", encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(records)} pairs and {sum(len(p['clips']) for p in records)} players; all source media preserved.")


if __name__ == "__main__":
    main()
