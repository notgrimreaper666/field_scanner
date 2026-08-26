"""
visualize.py

Produces human-readable outputs from a FieldReport:
    - a green-mask overlay image (shows exactly which pixels were
      counted as vegetation)
    - a grid heatmap image (color-coded by coverage status per cell,
      with % labels) -- this is the "where does it need greenery" map
"""

from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .vegetation_index import green_mask

STATUS_COLORS = {
    "healthy": "#2e7d32",          # dark green
    "moderate": "#f9a825",         # amber
    "needs_attention": "#ef6c00",  # orange
    "bare": "#c62828",             # red
}


def save_mask_overlay(img_rgb: np.ndarray, out_path: str,
                       exgr_threshold: float = 10.0,
                       use_hsv_confirmation: bool = True):
    mask = green_mask(img_rgb, exgr_threshold, use_hsv_confirmation)

    overlay = img_rgb.copy()
    highlight = np.zeros_like(img_rgb)
    highlight[..., 1] = 255  # green channel
    alpha = 0.45
    overlay[mask] = (
        (1 - alpha) * overlay[mask] + alpha * highlight[mask]
    ).astype(np.uint8)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes[0].imshow(img_rgb)
    axes[0].set_title("Original")
    axes[0].axis("off")

    axes[1].imshow(overlay)
    axes[1].set_title(f"Detected vegetation ({mask.mean()*100:.1f}%)")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_grid_heatmap(img_rgb: np.ndarray, report, out_path: str):
    """
    Draws the field image with a grid overlay, each cell tinted by its
    coverage status and labeled with its green %. This is the map you'd
    hand to a field crew: red/orange cells = go plant there first.
    """
    h, w = img_rgb.shape[:2]
    rows, cols = report.grid_rows, report.grid_cols
    row_edges = np.linspace(0, h, rows + 1)
    col_edges = np.linspace(0, w, cols + 1)

    fig, ax = plt.subplots(figsize=(10, 10 * h / w if w else 10))
    ax.imshow(img_rgb)

    cell_lookup = {(c.row, c.col): c for c in report.cells}

    for r in range(rows):
        for c in range(cols):
            cell = cell_lookup[(r, c)]
            y0, y1 = row_edges[r], row_edges[r + 1]
            x0, x1 = col_edges[c], col_edges[c + 1]
            color = STATUS_COLORS[cell.status]
            rect = Rectangle((x0, y0), x1 - x0, y1 - y0,
                              linewidth=1, edgecolor="white",
                              facecolor=color, alpha=0.40)
            ax.add_patch(rect)
            ax.text((x0 + x1) / 2, (y0 + y1) / 2,
                     f"{cell.green_fraction*100:.0f}%",
                     color="white", ha="center", va="center",
                     fontsize=8, fontweight="bold")

    # legend
    handles = [Rectangle((0, 0), 1, 1, facecolor=col, alpha=0.6, label=name)
               for name, col in STATUS_COLORS.items()]
    ax.legend(handles=handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.02), ncol=4, frameon=False)

    ax.set_title(f"Field Coverage Map — overall {report.overall_green_pct:.1f}% green")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
