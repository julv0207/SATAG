"""Draw five error-free evaluated AudioCaps examples and copy their source audio."""
import base64
import csv
import hashlib
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Dataset 평가"
SEED = 20260923


def main():
    rows = []
    for path in sorted((SOURCE / "결과").glob("*_results.csv")):
        for row in csv.DictReader(path.open(encoding="utf-8-sig")):
            row["csv"] = path.name
            rows.append(row)
    eligible = [r for r in rows if r["decision"] == "accurate" and not r["issues"].strip()]
    assert len({r['audio_id'] for r in eligible}) == len(eligible), "Duplicate eligible audio IDs"
    chosen = random.Random(SEED).sample(eligible, 5)
    samples, provenance = [], []
    for row in chosen:
        source = SOURCE / row["csv"].replace("_results.csv", ".html")
        page = source.read_text(encoding="utf-8")
        article = re.search(r'<article\b[^>]*data-audio-id="' + re.escape(row["audio_id"]) + r'"[^>]*>(.*?)</article>', page, re.S).group(1)
        paragraphs = [html.unescape(x) for x in re.findall(r'<p>(.*?)</p>', article, re.S)]
        assert paragraphs[:2] == [row["audiocaps_source_caption"], row["spotsound_temporal_grounding"]]
        uri = re.search(r'<audio\b[^>]*src="([^"]+)"', article).group(1)
        media, payload = uri.split(",", 1)
        assert media in ("data:audio/mpeg;base64", "data:audio/mp3;base64"), media
        audio = base64.b64decode(payload, validate=True)
        events = {}
        grounding = row["spotsound_temporal_grounding"]
        pattern = r'(.+?) from (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?)(?: and |$)'
        matches = list(re.finditer(pattern, grounding))
        assert ''.join(m.group(0) for m in matches) == grounding
        for match in matches:
            name, start, end = match.groups()
            interval = [float(start), float(end)]
            assert 0 <= interval[0] < interval[1] <= 10
            events.setdefault(name, []).append(interval)
        asset = f"assets/audiocapst-{row['audio_id']}.mp3"
        samples.append(dict(id=row['audio_id'], duration=10, caption=row['audiocaps_source_caption'],
                            spot_caption=grounding, events=[dict(name=k, intervals=v) for k, v in events.items()], audio=asset))
        provenance.append(dict(asset=asset, source=source.name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                               evaluation_csv=row['csv'], evaluation_csv_sha256=hashlib.sha256((SOURCE / '결과' / row['csv']).read_bytes()).hexdigest(),
                               evaluation_index=int(row['index']), decision=row['decision'], issues=row['issues'],
                               sha256=hashlib.sha256(audio).hexdigest()))
        (ROOT / 'docs' / asset).write_bytes(audio)
    (ROOT / 'docs/audiocaps-samples.js').write_text('window.SATAG_AUDIOCAPS_SAMPLES = ' + json.dumps(samples, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
    manifest = dict(seed=SEED, selection="random.Random(seed).sample, without replacement, sorted CSV filenames and source row order",
                    criteria="decision == accurate and issues blank", total_rows=len(rows), eligible_rows=len(eligible),
                    selected_ids=[r['audio_id'] for r in chosen], assets=provenance)
    (ROOT / 'docs/assets/audiocaps-selection.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(eligible=len(eligible), selected=manifest['selected_ids']), ensure_ascii=False))


if __name__ == '__main__':
    main()
