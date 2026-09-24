import json
from dataclasses import asdict, dataclass

import numpy as np
from PIL import Image

from .vegetation_index import green_mask


@dataclass
class CellResult:
    row: int
    col: int
    green_fraction: float
    status: str  # healthy | moderate | needs_attention | bare
    pixel_area: int
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
    status_breakdown: dict
    cells: list[CellResult]
    recommendation: str = ""

    def to_dict(self):
        return asdict(self)

    def save_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


STATUS_THRESHOLDS = (
    ("healthy", 0.70),
    ("moderate", 0.40),
    ("needs_attention", 0.15),
    ("bare", 0.0),
)


def classify_fraction(frac: float) -> str:
    """Classify a zone based on its vegetation fraction."""

    for status, threshold in STATUS_THRESHOLDS:
        if frac >= threshold:
            return status

    return "bare"


class FieldAnalyzer:
    def __init__(
        self,
        exgr_threshold: float = 10.0,
        use_hsv_confirmation: bool = True,
        grid_rows: int = 8,
        grid_cols: int = 8,
    ):
        self.exgr_threshold = exgr_threshold
        self.use_hsv_confirmation = use_hsv_confirmation
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

    def load_image(self, path: str) -> np.ndarray:
        """Load an image from disk as an RGB NumPy array."""

        img = Image.open(path).convert("RGB")

        return np.array(img)

    def analyze(
        self,
        image_path: str,
        field_area_hectares: float | None = None,
        target_coverage_pct: float = 80.0,
    ) -> FieldReport:
        """
        Analyze an image loaded from a file path.

        This is the backwards-compatible file-based entry point.
        """

        img = self.load_image(image_path)

        return self.analyze_image(
            img,
            image_path=str(image_path),
            field_area_hectares=field_area_hectares,
            target_coverage_pct=target_coverage_pct,
        )

    def analyze_image(
        self,
        img: np.ndarray,
        image_path: str = "",
        field_area_hectares: float | None = None,
        target_coverage_pct: float = 80.0,
    ) -> FieldReport:
        """
        Analyze an image already loaded into memory.

        This is the primary entry point for Streamlit and future APIs.
        """

        # ----------------------------------------------------
        # Validate image
        # ----------------------------------------------------

        if not isinstance(img, np.ndarray):
            raise TypeError("img must be a NumPy array.")

        if img.ndim != 3 or img.shape[2] != 3:
            raise ValueError(
                "img must have shape (height, width, 3) for an RGB image."
            )

        height, width = img.shape[:2]

        if height == 0 or width == 0:
            raise ValueError("Image must not be empty.")

        # ----------------------------------------------------
        # Validate settings
        # ----------------------------------------------------

        if self.grid_rows <= 0 or self.grid_cols <= 0:
            raise ValueError(
                "grid_rows and grid_cols must be greater than 0."
            )

        if field_area_hectares is not None and field_area_hectares <= 0:
            raise ValueError(
                "field_area_hectares must be greater than 0."
            )

        if not 0 <= target_coverage_pct <= 100:
            raise ValueError(
                "target_coverage_pct must be between 0 and 100."
            )

        # ----------------------------------------------------
        # Vegetation detection
        # ----------------------------------------------------

        mask = green_mask(
            img,
            exgr_threshold=self.exgr_threshold,
            use_hsv_confirmation=self.use_hsv_confirmation,
        )

        overall_green_pct = float(mask.mean() * 100)

        # ----------------------------------------------------
        # Real-world area calculation
        # ----------------------------------------------------

        total_area_m2 = None
        m2_per_pixel = None

        if field_area_hectares is not None:
            total_area_m2 = field_area_hectares * 10_000

            total_pixels = height * width

            m2_per_pixel = total_area_m2 / total_pixels

        # ----------------------------------------------------
        # Grid analysis
        # ----------------------------------------------------

        rows = self.grid_rows
        cols = self.grid_cols

        row_edges = np.linspace(
            0,
            height,
            rows + 1,
            dtype=int,
        )

        col_edges = np.linspace(
            0,
            width,
            cols + 1,
            dtype=int,
        )

        cells: list[CellResult] = []

        status_breakdown = {
            "healthy": 0,
            "moderate": 0,
            "needs_attention": 0,
            "bare": 0,
        }

        for row in range(rows):

            for col in range(cols):

                r0 = row_edges[row]
                r1 = row_edges[row + 1]

                c0 = col_edges[col]
                c1 = col_edges[col + 1]

                cell_mask = mask[r0:r1, c0:c1]

                pixel_area = cell_mask.size

                if pixel_area > 0:
                    fraction = float(cell_mask.mean())
                else:
                    fraction = 0.0

                status = classify_fraction(fraction)

                status_breakdown[status] += 1

                real_area = None

                if m2_per_pixel is not None:
                    real_area = pixel_area * m2_per_pixel

                cells.append(
                    CellResult(
                        row=row,
                        col=col,
                        green_fraction=round(
                            fraction,
                            4,
                        ),
                        status=status,
                        pixel_area=pixel_area,
                        real_area_m2=(
                            round(real_area, 2)
                            if real_area is not None
                            else None
                        ),
                    )
                )

        # ----------------------------------------------------
        # Vegetated area and coverage deficit
        # ----------------------------------------------------

        vegetated_area_m2 = None
        deficit_area_m2 = None

        if total_area_m2 is not None:

            vegetated_area_m2 = (
                total_area_m2
                * (overall_green_pct / 100)
            )

            target_area_m2 = (
                total_area_m2
                * (target_coverage_pct / 100)
            )

            deficit_area_m2 = max(
                0.0,
                target_area_m2 - vegetated_area_m2,
            )

        # ----------------------------------------------------
        # Recommendation
        # ----------------------------------------------------

        recommendation = self._build_recommendation(
            overall_green_pct=overall_green_pct,
            target_coverage_pct=target_coverage_pct,
            deficit_area_m2=deficit_area_m2,
            status_breakdown=status_breakdown,
            total_cells=rows * cols,
        )

        # ----------------------------------------------------
        # Final report
        # ----------------------------------------------------

        return FieldReport(
            image_path=image_path,
            image_width=width,
            image_height=height,
            overall_green_pct=round(
                overall_green_pct,
                2,
            ),
            total_area_m2=(
                round(total_area_m2, 2)
                if total_area_m2 is not None
                else None
            ),
            vegetated_area_m2=(
                round(vegetated_area_m2, 2)
                if vegetated_area_m2 is not None
                else None
            ),
            deficit_area_m2=(
                round(deficit_area_m2, 2)
                if deficit_area_m2 is not None
                else None
            ),
            grid_rows=rows,
            grid_cols=cols,
            status_breakdown=status_breakdown,
            cells=cells,
            recommendation=recommendation,
        )

    def _build_recommendation(
        self,
        overall_green_pct: float,
        target_coverage_pct: float,
        deficit_area_m2: float | None,
        status_breakdown: dict,
        total_cells: int,
    ) -> str:
        """Generate a simple field-level recommendation."""

        if overall_green_pct >= target_coverage_pct:

            return (
                f"Coverage is {overall_green_pct:.1f}%, "
                f"which meets or exceeds the target of "
                f"{target_coverage_pct:.1f}%. "
                "Continue monitoring the field periodically."
            )

        gap = target_coverage_pct - overall_green_pct

        attention_zones = (
            status_breakdown["needs_attention"]
            + status_breakdown["bare"]
        )

        attention_pct = (
            attention_zones / total_cells * 100
            if total_cells > 0
            else 0
        )

        message = (
            f"Coverage is {overall_green_pct:.1f}%, "
            f"which is {gap:.1f} percentage points below "
            f"the target of {target_coverage_pct:.1f}%. "
        )

        message += (
            f"{attention_zones} of {total_cells} zones "
            f"({attention_pct:.1f}%) are classified as "
            "needs_attention or bare."
        )

        if deficit_area_m2 is not None:
            message += (
                f" Approximately {deficit_area_m2:.1f} m² "
                "of additional vegetated area would be required "
                "to reach the target."
            )

        return message
