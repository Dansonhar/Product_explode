# MEGADUCT reference reconstruction viewer

Private local viewer for 23 rebuilt product families plus one connected-system explainer / 37 assemblies, based on the user's September 2026 brochure photographs. No public deployment has been performed.

## Run

With Node 22+ installed, run `npm install`, then `npm run dev` in this folder. Open `http://127.0.0.1:4180/`. `npm run build` creates the production bundle locally. The build intentionally omits full-resolution review PNG/JPEG files because the website uses their WebP derivatives.

## Features and limits

Source-photo comparison with enlarged view; assembly variants; assembled/exploded view; named part selection; enclosure X-ray; end view; orbit/zoom; copper/aluminium appearance; assembled GLB download. Native Blender sources are in `../blender/products/`.

Dimensions not explicitly established by the photos are estimated. Material selection is visual only. No current-rating selector implies validated engineering geometry. Read `../DESIGN_REBUILD.md` and `../SOURCE_NOTES.md` before using these presentation models.

## Regeneration and checks

From the project root, run Blender in background mode with `--python tools/build_realistic_products.py -- --render`. Optional `--only slug,slug` rebuilds selected assets. This produces native sources, GLBs, renders and the catalogue.

After changing renders or reference photos, run `python tools/optimize_web_assets.py` with Pillow available. The viewer uses these small WebP thumbnails and reference derivatives while retaining the originals for review and packaging.

From this folder, `node check-export.mjs` validates all GLBs, finite coordinates, dimensions, component counts and required source files. It does not regenerate geometry. From the project root, `node tools/check_browser.mjs` tests all catalogue variants against the running local server, interactions and download, and saves review screenshots. Its Chrome/runtime paths are configured for this workstation.

Latest checks: all 37 assemblies parsed successfully; 3,477 meshes checked; production build passed. Browser results are recorded in `../review/browser-check.json`.
