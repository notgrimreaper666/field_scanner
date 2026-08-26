#!/usr/bin/env python3
"""
cli.py -- command-line entry point for the field scanner.

Usage:
    python cli.py path/to/field_photo.jpg
    python cli.py path/to/field_photo.jpg --area-hectares 2.5 --target 80
    python cli.py path/to/field_photo.jpg --grid-rows 10 --grid-cols 10 -o out/

Outputs (written to --outdir, default "./output"):
    report.json          machine-readable full report
    overlay.png           original vs. detected-vegetation side by side
    coverage_map.png       grid heatmap showing which zones need greenery
"""
import argparse
from pathlib import Path

from field_scanner.analyzer import FieldAnalyzer
from field_scanner.visualize import save_mask_overlay, save_grid_heatmap


def main():
    p = argparse.ArgumentParser(description="Scan a field photo and report green coverage.")
    p.add_argument("image", help="Path to field image (jpg/png/tif).")
    p.add_argument("--area-hectares", type=float, default=None,
                    help="Real-world area covered by the image, in hectares. "
                         "If given, area-based deficit numbers (m²) are computed.")
    p.add_argument("--target", type=float, default=80.0,
                    help="Target green coverage %% goal (default: 80).")
    p.add_argument("--grid-rows", type=int, default=8)
    p.add_argument("--grid-cols", type=int, default=8)
    p.add_argument("--exgr-threshold", type=float, default=10.0,
                    help="Sensitivity of the green detector. Lower = more permissive "
                         "(catches sparse/pale vegetation, more false positives). "
                         "Higher = stricter. Default 10.0.")
    p.add_argument("-o", "--outdir", default="./output")
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    analyzer = FieldAnalyzer(
        exgr_threshold=args.exgr_threshold,
        grid_rows=args.grid_rows,
        grid_cols=args.grid_cols,
    )

    report = analyzer.analyze(
        args.image,
        field_area_hectares=args.area_hectares,
        target_coverage_pct=args.target,
    )

    report.save_json(str(outdir / "report.json"))

    img = analyzer.load_image(args.image)
    save_mask_overlay(img, str(outdir / "overlay.png"),
                       exgr_threshold=args.exgr_threshold)
    save_grid_heatmap(img, report, str(outdir / "coverage_map.png"))

    print(f"\n=== Field Coverage Report: {args.image} ===")
    print(f"Overall green coverage: {report.overall_green_pct:.2f}%")
    if report.total_area_m2:
        print(f"Total area:      {report.total_area_m2:,.0f} m²")
        print(f"Vegetated area:  {report.vegetated_area_m2:,.0f} m²")
        print(f"Deficit area:    {report.deficit_area_m2:,.0f} m² (to reach {args.target:.0f}% target)")
    print(f"Grid zone breakdown: {report.status_breakdown}")
    print(f"\n{report.recommendation}\n")
    print(f"Saved: {outdir/'report.json'}, {outdir/'overlay.png'}, {outdir/'coverage_map.png'}")


if __name__ == "__main__":
    main()
