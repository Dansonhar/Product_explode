"""Build lightweight WebP derivatives used by the interactive viewer."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "viewer/public"
catalog = json.loads((PUBLIC / "models/catalog.json").read_text())
(PUBLIC / "thumbs").mkdir(exist_ok=True)
(PUBLIC / "references/web").mkdir(parents=True, exist_ok=True)

for product in catalog:
    variant = product["variants"][0]
    with Image.open(PUBLIC / "renders" / variant["render"]) as image:
        image.thumbnail((240, 180), Image.Resampling.LANCZOS)
        image.convert("RGB").save(PUBLIC / "thumbs" / f'{product["slug"]}.webp', "WEBP", quality=72, method=6)

for photo in {v["photo"] for p in catalog for v in p["variants"]}:
    with Image.open(PUBLIC / "references/brochure" / photo) as image:
        image.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
        image.convert("RGB").save(PUBLIC / "references/web" / (Path(photo).stem + ".webp"), "WEBP", quality=78, method=6)
