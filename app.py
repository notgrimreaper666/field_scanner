"""
app.py -- Streamlit web app for the Field Green-Coverage Scanner.

Run with:
    streamlit run app.py

Then open the browser tab it launches (usually http://localhost:8501),
upload a field photo, and see the coverage % + heatmap live.
"""
import io
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

from field_scanner.analyzer import FieldAnalyzer
from field_scanner.visualize import save_mask_overlay, save_grid_heatmap

st.set_page_config(
    page_title="Field Green Coverage Scanner",
    page_icon="🌱",
    layout="wide",
)

# ---------- Header ----------
st.title("🌱 Field Green Coverage Scanner")
st.caption(
    "Upload an aerial/drone/satellite photo of a field to measure green "
    "vegetation coverage and see exactly which zones need more greenery."
)

# ---------- Sidebar controls ----------
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader(
        "Field photo", type=["jpg", "jpeg", "png", "tif", "tiff"]
    )

    st.divider()
    area_hectares = st.number_input(
        "Field area (hectares) — optional",
        min_value=0.0, value=0.0, step=0.1,
        help="If known, enables real-world m² deficit numbers. Leave 0 to skip.",
    )
    target_pct = st.slider(
        "Target coverage %", min_value=10, max_value=100, value=80, step=5,
        help="The green-coverage goal you're aiming for.",
    )

    st.divider()
    grid_size = st.select_slider(
        "Grid resolution", options=[4, 6, 8, 10, 12, 16], value=8,
        help="How finely to divide the field into zones for the heatmap.",
    )
    sensitivity = st.slider(
        "Detector sensitivity (ExGR threshold)",
        min_value=0.0, max_value=30.0, value=10.0, step=1.0,
        help="Lower = catches sparser/paler vegetation but more false positives. "
             "Higher = stricter, misses faint growth.",
    )

    st.divider()
    use_demo = st.button("▶ Try with sample field (no upload needed)")


def load_demo_image() -> np.ndarray:
    """Generates the same synthetic field used in demo.py, for live demos."""
    rng = np.random.default_rng(7)
    h, w = 900, 1200
    img = np.zeros((h, w, 3), dtype=np.float32)
    soil = np.array([150, 120, 85], dtype=np.float32)
    img[:] = soil
    img += rng.normal(0, 8, img.shape)

    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(14):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        ry, rx = rng.uniform(60, 220), rng.uniform(60, 220)
        density = rng.uniform(0.2, 1.0)
        dist = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2
        strength = np.clip(1 - dist, 0, 1) * density
        green = np.array([60, 140, 50], dtype=np.float32)
        for ch in range(3):
            img[..., ch] = np.where(
                dist < 1.0,
                img[..., ch] * (1 - strength) + green[ch] * strength,
                img[..., ch]
            )
    return np.clip(img + rng.normal(0, 5, img.shape), 0, 255).astype(np.uint8)


# ---------- Resolve input image ----------
img_array = None
image_label = None

if uploaded_file is not None:
    pil_img = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(pil_img)
    image_label = uploaded_file.name
elif use_demo:
    img_array = load_demo_image()
    image_label = "sample_field.png"

# ---------- Run analysis ----------
if img_array is not None:
    with st.spinner("Analyzing field coverage..."):
        analyzer = FieldAnalyzer(
            exgr_threshold=sensitivity,
            grid_rows=grid_size,
            grid_cols=grid_size,
        )

        # analyzer.analyze() expects a file path, so write a temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            Image.fromarray(img_array).save(tmp.name)
            tmp_path = tmp.name

        report = analyzer.analyze(
            tmp_path,
            field_area_hectares=(area_hectares if area_hectares > 0 else None),
            target_coverage_pct=float(target_pct),
        )

        overlay_buf = io.BytesIO()
        save_mask_overlay(img_array, overlay_buf, exgr_threshold=sensitivity)
        overlay_buf.seek(0)

        heatmap_buf = io.BytesIO()
        save_grid_heatmap(img_array, report, heatmap_buf)
        heatmap_buf.seek(0)

        Path(tmp_path).unlink(missing_ok=True)

    # ---------- Top metrics row ----------
    st.subheader(f"Results — {image_label}")
    cols = st.columns(4)
    cols[0].metric("Green coverage", f"{report.overall_green_pct:.1f}%")
    if report.total_area_m2:
        cols[1].metric("Vegetated area", f"{report.vegetated_area_m2:,.0f} m²")
        cols[2].metric("Deficit to target", f"{report.deficit_area_m2:,.0f} m²")
    else:
        cols[1].metric("Vegetated area", "— (add field area)")
        cols[2].metric("Deficit to target", "—")
    needing = report.status_breakdown["needs_attention"] + report.status_breakdown["bare"]
    total_cells = grid_size * grid_size
    cols[3].metric("Zones needing attention", f"{needing}/{total_cells}")

    st.info(report.recommendation)

    # ---------- Images ----------
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        st.image(overlay_buf, caption="Detected vegetation (green overlay)", use_container_width=True)
    with img_col2:
        st.image(heatmap_buf, caption="Zone coverage map — where greenery is needed", use_container_width=True)

    # ---------- Breakdown table ----------
    with st.expander("Zone status breakdown"):
        b = report.status_breakdown
        st.write(
            f"🟢 **Healthy** (≥70%): {b['healthy']} zones &nbsp;|&nbsp; "
            f"🟡 **Moderate** (40–70%): {b['moderate']} zones &nbsp;|&nbsp; "
            f"🟠 **Needs attention** (15–40%): {b['needs_attention']} zones &nbsp;|&nbsp; "
            f"🔴 **Bare** (<15%): {b['bare']} zones"
        )

    with st.expander("Raw report (JSON)"):
        st.json(report.to_dict())

    st.download_button(
        "Download full report (JSON)",
        data=str(report.to_dict()).encode(),
        file_name="field_coverage_report.json",
        mime="application/json",
    )

else:
    st.info("👈 Upload a field photo in the sidebar, or click **Try with sample field** to see a live demo.")