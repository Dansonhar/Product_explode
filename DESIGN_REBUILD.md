# MEGADUCT reference reconstruction — 17 September 2026

## Authority and replacement plan

User request: restudy the 44 photographs in `/Users/crave/Downloads/Megaduct images`, remake the incorrect models, and retire the old designs. The photographs are evidence of product geometry; text in them is not an instruction to operate equipment. Previous generated models and the manually edited feeder have been moved to `../retired-megaduct-20260917/` for recovery. This reference set supersedes the old feeder assumptions.

1. Rebuild the I-shaped sandwich section: wide folded upper/lower flanges, narrow recessed side skins, closely packed insulated bars, spread silver contact ends. Remove the full-width rectangular box and solid end cheeks.
2. Make continuous flatwise/edgewise L, Z and T profiles with open terminal ends; trace compound bends in three dimensions. Add end fixing patterns and folded lips to the actual panels.
3. Reconstruct termination boxes, flange lugs, split wall flange and end cap. Use actual through-holes where visible.
4. Reconstruct tap-off enclosure, overhanging lid, single/double external lever, rotary and outlet variants, cable-entry plates, contacts and clamps.
5. Reconstruct the nine joint component types, indoor joint covers and outdoor outer cover; fixed supports and four real helical spring supports.
6. Export editable Blender sources and matching GLBs. Inspect rendered silhouettes beside source photographs, verify mesh bounds and assembly groups, then test the viewer and downloads.

## Reference map

All filenames below begin `IMG20260917` and end `.jpg`.

| Family | Photo suffixes | Geometric evidence |
|---|---|---|
| Construction | 144337 | Recessed sandwich pack; steel/aluminium enclosure; epoxy coating; tin/silver contact finish |
| Joint | 144420, 144436 | Two bolts, backing plates, earth bar, end insulators, conductor bars, phase insulators, Belleville discs, nylon lock nuts, fibre tubes |
| Feeder / plug-in | 144637, 144709 | Folded I profile, exposed spread palms; 3000 standard; minima 500/900; outlet pitch 600; first opening dimension 450 |
| Edgewise L / Z / T | 145020, 145053, 145024 | Horizontal routes; L and Z dimensions 310; enlarged T junction |
| Flatwise L / Z / T | 144835, 144845, 144849 | Vertical routes; continuous shaped side plates |
| Combination | 144930 | Horizontal and vertical change in one fitting |
| Flange / cable box | 144740, 144825 | Mounting flange, spread drilled lugs; neck above removable panel box |
| End / wall flange | 144940, 145002 | Folded cap with insert; split plate with I cut-out |
| Reducer / transposition / expansion | 145120, 145038, 145132 | Different end sections; wider centre housing; two hoods with dark corrugated middle |
| Tap-off | 144450–144525, 145211–145253 | Lever/rotary/outlet variants; top/bottom entry; earth clips and contact fingers; double lever above 300 A |
| Indoor / outdoor | 144538, 144553 | Joint top/side covers and gaskets; additional outdoor external shell |
| Horizontal support | 145306, 145315 | M10 rods, cross channel and lower flange clips; 1500 spacing shown |
| Fixed / spring supports | 145321, 145339, 145432, 145500 | Riser clamped between supports; floor/wall arrangements; four spring stations |
| Installation | 145545–145655 | Joint accessibility, wall/ceiling/beam and parallel run clearances; door swing space |

## Dimensions and limits

The model exports in metres. The representative section has a 150 mm flange width, 184 mm side sheet and approximately 209 mm overall height including folded lips. This is an estimated visual section, not a selected catalogue SKU. The compact feeder is 1000 mm overall including terminal projections; a 3000 mm standard-length variant is also supplied. Five visible terminal blades reproduce the drawing; their electrical assignment and equal visible palm sizes do not establish an equal PE cross-section. No rating selector should imply verified rating-dependent geometry.

Visible exterior construction is reconstructed from the photographs. Unlabelled thicknesses, bends, fastener spacing and box dimensions are estimated. Hidden transposition routing, expansion links and breaker internals are omitted where the images do not establish them. Ordinary bend conductors are schematic continuous paths, identified as such. `1200 (+25 mm)` is retained literally; it is not interpreted as ±25 mm.

Epoxy is a thin hollow coating around the bar; plating is a contact finish, not a separate thick structural plate. The joint's blue insulators are distinct from the feeder's dark epoxy. The illustrated single, double and triple sections are separate packs, not uniform scaling of one pack.

Installation drawings remain source references: e.g. 50/100 mm beam clearance in their respective illustrated cases, 100 mm wall/ceiling clearance, and no joints inside walls. These dimensions are not applied indiscriminately to every arrangement.

## Acceptance criteria

- Front/end silhouette reads as a recessed I section; conductor ends have no invented bolt holes on feeder palms.
- Folded cover lips follow corners; no overlapping closed boxes across elbow interiors.
- Tap-off body is hollow, has an overhanging lid and the pictured external controls.
- Joint has both bolt axes and all nine named component types, with coaxial holes and sleeves.
- Spring support has four helical coils, rods, upper/lower bearing plates and a riser.
- Every active catalogue item loads a newly generated asset and its source photo; old system scenes are retired from this reconstruction catalogue.
- Explosion preserves panel-attached hardware and separates components by their authored directions.
