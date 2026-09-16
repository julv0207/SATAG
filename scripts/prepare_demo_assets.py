"""Extract demo assets without re-encoding. Development only.

Usage: python scripts/prepare_demo_assets.py --source /workspace
Requires beautifulsoup4 and pymupdf. The built site has no dependencies.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
import pymupdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    docs = Path(__file__).resolve().parents[1] / "docs"
    assets = docs / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    provenance = []

    def extract(node, stem, source):
        header, payload = node["src"].split(",", 1)
        extension = {"data:audio/mpeg;base64": "mp3", "data:audio/wav;base64": "wav", "data:image/png;base64": "png"}[header]
        data = base64.b64decode(payload, validate=True)
        name = f"{stem}.{extension}"
        (assets / name).write_bytes(data)
        provenance.append({"asset": f"assets/{name}", "source": source, "sha256": hashlib.sha256(data).hexdigest()})
        return f"assets/{name}"

    conditions = {0: [[0.73, 4.31], [5.77, 9.35]], 50: [[1.31, 5.87], [3.59, 8.15]], 100: [[2.24, 6.97], [2.24, 6.97]]}
    pairs = {"keyboard-bird": ["Keyboard Typing", "Bird Chirping"], "speech-cat": ["Man Talking", "Cat Meowing"]}

    def events(pair, overlap):
        return [{"name": name, "start": interval[0], "end": interval[1]} for name, interval in zip(pairs[pair], conditions[overlap])]

    filename = "AudioCaps_TalkMeow_TypeChirp_Muted_Mels.html"
    soup = BeautifulSoup((args.source / filename).read_text(), "html.parser")
    articles = soup.select("article")
    assert len(articles) == 4
    figure = []
    for index, pair, overlap, panel in [(1, "keyboard-bird", 0, "a"), (2, "speech-cat", 0, "b"), (0, "keyboard-bird", 50, "c"), (3, "speech-cat", 100, "d")]:
        article = articles[index]
        assert pairs[pair][0] in article.h2.get_text()
        assert f"{overlap}%" in article.h2.get_text()
        stem = f"fig1-{pair}-{overlap}"
        figure.append({"id": stem, "panel": panel, "pair": pair, "overlap": overlap, "events": events(pair, overlap), "duration": 10, "audio": extract(article.audio, stem, filename), "image": extract(article.img, stem, filename)})

    filename = "AudioCaps_TalkMeow_TypeChirp_Times.html"
    soup = BeautifulSoup((args.source / filename).read_text(), "html.parser")
    comparisons = []
    for pair, pair_id in [("keyboard-bird", "p2"), ("speech-cat", "p1")]:
        for article, overlap in zip(soup.select(f"#{pair_id} article"), [0, 50, 100]):
            clip = article.select_one(".clip")
            assert clip.h5.get_text(strip=True) == "s00"
            stem = f"baseline-{pair}-{overlap}"
            comparisons.append({"id": stem, "pair": pair, "overlap": overlap, "events": events(pair, overlap), "duration": 10, "baseline": {"audio": extract(clip.audio, stem, filename), "image": extract(clip.img, stem, filename)}, "satag": None})

    filename = "AudioCaps_Duration_SpotSound_Qualitative_100.html"
    soup = BeautifulSoup((args.source / filename).read_text(), "html.parser")
    dataset = []
    for audio_id in ["4YMXgLFcR94", "BMayJId0X1s", "c6YJgZ3qzOw"]:
        article = soup.select_one(f'article[data-audio-id="{audio_id}"]')
        assert article is not None, f"Missing AudioCaps-T example: {audio_id}"
        dataset_events = []
        for row in article.select(".event-row"):
            event_name = row.select_one(".event-name").get_text(" ", strip=True)
            intervals = []
            for bar in row.select(".bar"):
                match = __import__("re").fullmatch(r"([0-9.]+)–([0-9.]+)s", bar["title"])
                assert match, f"Unexpected interval for {audio_id}: {bar['title']}"
                intervals.append([float(match.group(1)), float(match.group(2))])
            dataset_events.append({"name": event_name, "intervals": intervals})
        stem = f"audiocaps-t-{audio_id}"
        dataset.append({
            "id": audio_id,
            "duration": 10,
            "caption": article.select_one(".source-caption").get_text(" ", strip=True),
            "spot_caption": article.select_one(".prediction p").get_text(" ", strip=True),
            "events": dataset_events,
            "audio": extract(article.audio, stem, filename),
        })

    filename = "음향 조절 예시.html"
    soup = BeautifulSoup((args.source / filename).read_text(), "html.parser")
    mixing = []
    for stale_asset in assets.glob("mixing-pair-*-variant-*.*"):
        stale_asset.unlink()
    variant_metadata = [
        (0, "Raw summation", "Source summation without peak normalization", None),
        (2, "Main 7 : Background 3", "Source peak normalization followed by 7:3 weighting", [7, 3]),
        (3, "Main 3 : Background 7", "Source peak normalization followed by 3:7 weighting", [3, 7]),
    ]
    source_pairs = soup.select("section.pair")
    assert len(source_pairs) == 5, "Expected five amplitude-control event pairs"
    published_pairs = [source_pairs[0], source_pairs[4]]
    for pair_index, pair in enumerate(published_pairs, start=1):
        names = [node.get_text(" ", strip=True) for node in pair.select("h2 strong")]
        assert len(names) == 2
        articles = pair.select("article")
        assert len(articles) == 4
        variants = []
        for variant_index, (source_index, label, description, weights) in enumerate(variant_metadata, start=1):
            article = articles[source_index]
            stem = f"mixing-pair-{pair_index}-variant-{variant_index}"
            variants.append({
                "label": label,
                "description": description,
                "weights": weights,
                "peak": float(article.select_one(".peak").get_text(" ", strip=True).split()[-1]),
                "audio": extract(article.audio, stem, filename),
                "image": extract(article.img, stem, filename),
            })
        mixing.append({
            "id": f"mixing-pair-{pair_index}",
            "main": names[0],
            "background": names[1],
            "inference_time": pair.select_one("h2 em").get_text(" ", strip=True),
            "seed": 42,
            "start": 2.24,
            "end": 6.97,
            "variants": variants,
        })

    existing_path = docs / "samples.js"
    prefix = "window.SATAG_SAMPLES = "
    if existing_path.exists():
        existing = json.loads(existing_path.read_text().removeprefix(prefix).strip().removesuffix(";"))
        connected = {sample["id"]: sample.get("satag") for sample in existing.get("comparisons", [])}
        for sample in comparisons:
            sample["satag"] = connected.get(sample["id"])
    existing_path.write_text(prefix + json.dumps({"figure": figure, "dataset": dataset, "comparisons": comparisons, "mixing": mixing}, indent=2) + ";\n")
    (assets / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    pdf = pymupdf.open(args.source / "Template.pdf")
    pdf[1].get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=pymupdf.Rect(33, 34, 580, 300)).save(assets / "satag-framework.png")
    (assets / "SATAG-draft.pdf").write_bytes((args.source / "Template.pdf").read_bytes())
    print(f"Prepared {len(figure)} figure clips, {len(dataset)} AudioCaps-T clips, {len(comparisons)} baseline clips, and {sum(len(pair['variants']) for pair in mixing)} mixing clips in {docs}")


if __name__ == "__main__":
    main()
