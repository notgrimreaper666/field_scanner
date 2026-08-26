"""
analyzer.py

FieldAnalyzer: loads a field image, computes overall green coverage %,
and runs a grid-based analysis to identify *which zones* of the field
are under-vegetated and how much area/effort would be needed to fix them.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
from PIL import Image

from .vegetation_index import green_mask


@dataclass
class CellResult:
    row: int
    col: int
    green_fraction: float          # 0.0 - 1.0
    status: str                    # "healthy" | "moderate" | "needs_attention" | "bare"
    pixel_area: int                # pixel count of the cell
    real_area_m2: float | None = None


@dataclass
class FieldReport:
    image_path: str
    image_width: int
    image_height: int
    overall_green_pct: float
    total_area_m2: float | None
    vegetated_area_m2: float | None
    deficit_area_m2: float | None
    grid_rows: int
    grid_cols: int
    status_breakdown: dict          # e.g. {"healthy": 12, "moderate": 5, ...}
    cells: list[CellResult] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self):
        d = asdict(self)
        return d

    def save_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# Status thresholds -- tune these for your crop/region.
# "healthy": plenty of canopy cover, no action needed
# "moderate": partial cover, could benefit from over-seeding / infill planting
# "needs_attention": sparse cover, prioritize for replanting / irrigation check
# "bare": essentially no vegetation, treat as highest priority
STATUS_THRESHOLDS = (
    ("healthy", 0.70),
    ("moderate", 0.40),
    ("needs_attention", 0.15),
    ("bare", 0.0),
)


def classify_fraction(frac: float) -> str:
    for name, cutoff in STATUS_THRESHOLDS:
        if frac >= cutoff:
            return name
    return "bare"


class FieldAnalyzer:
    def __init__(self,
                 exgr_threshold: float = 10.0,
                 use_hsv_confirmation: bool = True,
                 grid_rows: int = 8,
                 grid_cols: int = 8):
        self.exgr_threshold = exgr_threshold
        self.use_hsv_confirmation = use_hsv_confirmation
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

    def load_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        return np.array(img)

    def analyze(self,
                image_path: str,
                field_area_hectares: float | None = None,
                target_coverage_pct: float = 80.0) -> FieldReport:
        """
        Run full analysis.

        field_area_hectares: real-world area the image covers, if known.
            Enables real_area_m2 per cell and total deficit-area estimates.
        target_coverage_pct: the coverage % you're aiming for (e.g. 80%
            canopy cover). Used to compute how much area still needs
            greenery to reach that goal.
        """
        img = self.load_image(image_path)
        h, w = img.shape[:2]

        mask = green_mask(img,
                           exgr_threshold=self.exgr_threshold,
                           use_hsv_confirmation=self.use_hsv_confirmation)

        overall_green_pct = float(mask.mean() * 100)

        total_area_m2 = None
        m2_per_pixel = None
        if field_area_hectares is not None:
            total_area_m2 = field_area_hectares * 10_000
            m2_per_pixel = total_area_m2 / (h * w)

        # --- grid analysis ---
        rows, cols = self.grid_rows, self.grid_cols
        row_edges = np.linspace(0, h, rows + 1, dtype=int)
        col_edges = np.linspace(0, w, cols + 1, dtype=int)

        cells: list[CellResult] = []
        status_breakdown = {"healthy": 0, "moderate": 0, "needs_attention": 0, "bare": 0}

        for r in range(rows):
            for c in range(cols):
                r0, r1 = row_edges[r], row_edges[r + 1]
                c0, c1 = col_edges[c], col_edges[c + 1]
                cell_mask = mask[r0:r1, c0:c1]
                pixel_area = cell_mask.size
                frac = float(cell_mask.mean()) if pixel_area > 0 else 0.0
                status = classify_fraction(frac)
                status_breakdown[status] += 1

                real_area = (pixel_area * m2_per_pixel) if m2_per_pixel else None

                cells.append(CellResult(
                    row=r, col=c,
                    green_fraction=round(frac, 4),
                    status=status,
                    pixel_area=pixel_area,
                    real_area_m2=round(real_area, 2) if real_area else None,
                ))

        # --- deficit / recommendation math ---
        vegetated_area_m2 = None
        deficit_area_m2 = None
        if total_area_m2 is not None:
            vegetated_area_m2 = total_area_m2 * (overall_green_pct / 100)
            target_area_m2 = total_area_m2 * (target_coverage_pct / 100)
            deficit_area_m2 = max(0.0, target_area_m2 - vegetated_area_m2)

        recommendation = self._build_recommendation(
            overall_green_pct, target_coverage_pct,
            deficit_area_m2, status_breakdown, rows * cols
        )

        return FieldReport(
            image_path=str(image_path),
            image_width=w,
            image_height=h,
            overall_green_pct=round(overall_green_pct, 2),
            total_area_m2=round(total_area_m2, 2) if total_area_m2 else None,
            vegetated_area_m2=round(vegetated_area_m2, 2) if vegetated_area_m2 else None,
            deficit_area_m2=round(deficit_area_m2, 2) if deficit_area_m2 else None,
            grid_rows=rows,
            grid_cols=cols,
            status_breakdown=status_breakdown,
            cells=cells,
            recommendation=recommendation,
        )

    @staticmethod
    def _build_recommendation(overall_pct, target_pct, deficit_m2,
                               status_breakdown, total_cells) -> str:
        gap = target_pct - overall_pct
        needing = status_breakdown["needs_attention"] + status_breakdown["bare"]
        pct_zones_needing = 100 * needing / total_cells if total_cells else 0

        if gap <= 0:
            return (f"Coverage ({overall_pct:.1f}%) already meets or exceeds the "
                    f"{target_pct:.0f}% target. No large-scale intervention needed; "
                    f"monitor periodically.")

        msg = (f"Current coverage is {overall_pct:.1f}%, which is {gap:.1f} "
               f"percentage points below the {target_pct:.0f}% target. "
               f"{needing}/{total_cells} grid zones ({pct_zones_needing:.0f}%) are "
               f"classified 'needs_attention' or 'bare' and should be prioritized.")
        if deficit_m2 is not None:
            msg += f" Estimated additional vegetated area needed: ~{deficit_m2:,.0f} m²."
        return msg
