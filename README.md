# Field Green-Coverage Scanner

Analyzes a photo of an agricultural field (drone, phone, or satellite RGB
image) and reports:

1. **Overall green coverage %** — how much of the field is currently vegetated.
2. **A grid-based coverage map** — which specific zones of the field are
   healthy vs. sparse vs. bare, so you know *where* to focus.
3. **How much area still needs greenery** — in m², if you tell it the
   real-world size of the field, based on a target coverage % you set.

No special camera needed — it works on ordinary RGB photos. If you have
4-band imagery (RGB + Near-Infrared) from a proper ag-drone, an NDVI
function is included too, which is more accurate — see "Upgrading to NDVI" below.

## Quick start

```bash
pip install -r requirements.txt

# Try it instantly on a generated sample field (no photo needed):
python demo.py

# Run on your own photo:
python cli.py path/to/field.jpg --area-hectares 2.5 --target 80
```

Outputs land in `./output/` (or `./demo_output/` for the demo):
- `report.json` — full machine-readable report (per-cell breakdown included)
- `overlay.png` — original photo vs. detected-vegetation mask, side by side
- `coverage_map.png` — grid heatmap: green=healthy, yellow=moderate, orange=needs attention, red=bare — with each cell's % labeled

## CLI options

```
python cli.py IMAGE [options]

--area-hectares FLOAT   Real-world area the photo covers (enables m² deficit numbers)
--target FLOAT          Target coverage % goal (default 80)
--grid-rows INT         Grid rows for zone analysis (default 8)
--grid-cols INT         Grid columns for zone analysis (default 8)
--exgr-threshold FLOAT  Detector sensitivity (default 10.0; lower = catches
                         sparser/paler vegetation but more false positives)
-o, --outdir PATH       Output directory (default ./output)
```

## How it works

Plants absorb red and blue light for photosynthesis but reflect green, so
even in an ordinary photo, vegetation stands out from soil/rock/dead
material on a color basis. The scanner uses:

- **ExGR (Excess Green minus Excess Red)** — `(2G−R−B) − (1.4R−G)` per
  pixel — the standard color-based vegetation index in agricultural
  computer vision, robust to reddish/brown soil tones.
- **HSV hue confirmation** — a pixel must also fall in the green hue band,
  which filters out things like green plastic, algae-tinted water, or
  painted equipment that could otherwise trip the color index.

A pixel counts as "vegetation" only if both agree. The fraction of
vegetation pixels = overall green coverage %.

For the zone map, the image is split into a grid (default 8×8 = 64 cells)
and each cell's green fraction is classified:

| Status | Green fraction | Meaning |
|---|---|---|
| healthy | ≥ 70% | good canopy cover |
| moderate | 40–70% | could benefit from over-seeding/infill |
| needs_attention | 15–40% | sparse, prioritize for replanting/irrigation check |
| bare | < 15% | essentially no vegetation, top priority |

These thresholds are in `field_scanner/analyzer.py` (`STATUS_THRESHOLDS`) —
tune them for your crop type and growth stage.

## Deficit / "how much greenery is needed" math

If you pass `--area-hectares`, the tool converts coverage % into real
area:

```
vegetated_area = total_area * (overall_coverage_pct / 100)
target_area    = total_area * (target_pct / 100)
deficit_area   = target_area - vegetated_area   (0 if already met)
```

This gives you a concrete "you need to vegetate ~X more m²" figure, plus
the list of specific grid cells to prioritize (from `report.json`).

## Upgrading to NDVI (optional, more accurate)

If your imagery includes a Near-Infrared band (common with dedicated ag
drones like DJI P4 Multispectral, MicaSense sensors, or Sentinel-2/Planet
satellite exports), use `field_scanner.vegetation_index.ndvi()` instead of
the RGB-only detector — swap it into `FieldAnalyzer.analyze()` in place of
`green_mask()`. NDVI directly measures chlorophyll reflectance and isn't
fooled by things like green-painted surfaces or lighting variation the way
RGB indices can be.

## Project structure

```
field_scanner/
  field_scanner/
    __init__.py
    vegetation_index.py   # ExG / ExGR / HSV mask / NDVI
    analyzer.py            # FieldAnalyzer, grid logic, deficit math
    visualize.py            # overlay + heatmap image generation
  cli.py                    # command-line entry point
  demo.py                    # generates a synthetic field & runs the pipeline
  requirements.txt
  README.md
```

## Tuning tips

- **False positives on bare soil** (soil looks slightly green in your
  photos): raise `--exgr-threshold` (try 15–20).
- **Missing pale/dry/stressed vegetation**: lower `--exgr-threshold`
  (try 5–8), or widen the hue range in `hsv_green_mask()`.
- **Shadows being misclassified**: shadowed vegetation often still passes
  since hue is stable under shadow, but heavy shadow on bare soil can
  occasionally read as darker — check `min_val` in `hsv_green_mask()` if
  this happens a lot in your imagery.
- Grid resolution (`--grid-rows/--grid-cols`) trades off precision vs.
  actionability — 8×8 is a good default for a single field; go finer
  (e.g. 20×20) for large fields where you want more localized guidance.
