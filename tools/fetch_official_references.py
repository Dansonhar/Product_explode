from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

PAGES = [
    ("feeder", "https://linkk.com.my/product/feeder/"),
    ("feeder-with-plug-in", "https://linkk.com.my/product/plug-in-feeder-assembly/"),
    ("edgewise-elbow", "https://linkk.com.my/product/edgewise-elbow/"),
    ("edgewise-offset", "https://linkk.com.my/product/edgewise-offset/"),
    ("edgewise-tee", "https://linkk.com.my/product/edgewise-tee/"),
    ("flatwise-elbow", "https://linkk.com.my/product/flatwise-elbow/"),
    ("flatwise-offset", "https://linkk.com.my/product/flatwise-offset/"),
    ("flatwise-tee", "https://linkk.com.my/product/flatwise-tee/"),
    ("flange-end", "https://linkk.com.my/product/fe-r1/"),
    ("end-feed-cable-box", "https://linkk.com.my/product/end-feed-box/"),
    ("end-cover", "https://linkk.com.my/product/end-cover/"),
    ("combination-elbow", "https://linkk.com.my/product/combination-elbow/"),
    ("reducer", "https://linkk.com.my/product/reducer/"),
    ("phase-transposition-unit", "https://linkk.com.my/product/phase-transportation/"),
    ("expansion-unit", "https://linkk.com.my/product/expansion-unit/"),
    ("tap-off-unit", "https://linkk.com.my/product/tou/"),
    ("feeder-hanger-support", "https://linkk.com.my/product/feeder-with-hanger-rod-support/"),
    ("fixed-support", "https://linkk.com.my/product/fixed-support/"),
    ("vertical-spring-hanger", "https://linkk.com.my/product/vsh-r1/"),
]

root = Path(__file__).resolve().parents[1]
out = root / "references" / "official-highres"
out.mkdir(parents=True, exist_ok=True)
records = []
for index, (slug, page) in enumerate(PAGES):
    request = urllib.request.Request(page, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "ignore")
    match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not match:
        raise RuntimeError(f"No primary product image found at {page}")
    image_url = match.group(1)
    suffix = Path(image_url.split("?", 1)[0]).suffix or ".jpg"
    target = out / f"{index:02d}-{slug}{suffix}"
    image_request = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
    target.write_bytes(urllib.request.urlopen(image_request, timeout=30).read())
    records.append({"id": index, "slug": slug, "page": page, "image": image_url, "local": target.name})
    print(index, slug, image_url)
(out / "manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
