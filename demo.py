#!/usr/bin/env python3
"""
demo.py -- generates a synthetic aerial-field-like test image and runs the
full analysis pipeline on it, so you can see the tool working end-to-end
without needing a real drone photo yet.

Run: python demo.py
Then swap in your own photo with: python cli.py your_photo.jpg
"""
import numpy as np
from pathlib import Path
from PIL import Image

from field_scanner.analyzer import FieldAnalyzer
from field_scanner.visualize import save_mask_overlay, save_grid_heatmap


def make_synthetic_field(w=1200, h=900, seed=7) -> np.ndarray:
    """
    Builds a fake aerial field photo: brown/tan soil base with patches of
    green vegetation of varying density, so coverage genuinely varies
    across the image (some zones lush, some bare) -- useful for testing
    the grid deficit-detection logic.
    """
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=np.float32)

    # Soil base color with mild noise
    soil = np.array([150, 120, 85], dtype=np.float32)
    img[:] = soil
    img += rng.normal(0, 8, img.shape)

    # Scatter several "vegetation patch" blobs of varying density/size
    yy, xx = np.mgrid[0:h, 0:w]
    num_patches = 14
    for _ in range(num_patches):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        ry, rx = rng.uniform(60, 220), rng.uniform(60, 220)
        density = rng.uniform(0.2, 1.0)  # how "full" this patch is
        dist = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2
        patch_mask = dist < 1.0
        # fade intensity toward the edge of the patch, scaled by density
        strength = np.clip(1 - dist, 0, 1) * density
        green = np.array([60, 140, 50], dtype=np.float32)
        for ch in range(3):
            img[..., ch] = np.where(
                patch_mask,
                img[..., ch] * (1 - strength) + green[ch] * strength,
                img[..., ch]
            )

    img = np.clip(img + rng.normal(0, 5, img.shape), 0, 255).astype(np.uint8)
    return img


def main():
    outdir = Path("./demo_output")
    outdir.mkdir(exist_ok=True)

    print("Generating synthetic field image...")
    img = make_synthetic_field()
    Image.fromarray(img).save(outdir / "synthetic_field.png")

    analyzer = FieldAnalyzer(grid_rows=8, grid_cols=8)

    print("Analyzing...")
    report = analyzer.analyze(
        str(outdir / "synthetic_field.png"),
        field_area_hectares=3.0,   # pretend this photo covers 3 hectares
        target_coverage_pct=75.0,
    )

    report.save_json(str(outdir / "report.json"))
    save_mask_overlay(img, str(outdir / "overlay.png"))
    save_grid_heatmap(img, report, str(outdir / "coverage_map.png"))

    print(f"\nOverall green coverage: {report.overall_green_pct:.2f}%")
    print(f"Vegetated area: {report.vegetated_area_m2:,.0f} m² of {report.total_area_m2:,.0f} m²")
    print(f"Deficit area to hit 75% target: {report.deficit_area_m2:,.0f} m²")
    print(f"Zone breakdown: {report.status_breakdown}")
    print(f"\n{report.recommendation}")
    print(f"\nFiles written to {outdir.resolve()}/")


if __name__ == "__main__":
    main()
