import io

import numpy as np
import streamlit as st
from PIL import Image

from field_scanner.analyzer import FieldAnalyzer
from field_scanner.visualize import save_mask_overlay, save_grid_heatmap


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FieldScanner",
    page_icon="🌱",
    layout="wide",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        color: #777;
        margin-bottom: 30px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        text-align: center;
        background: white;
    }

    .metric-label {
        font-size: 14px;
        color: #777;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
    }

    .section-title {
        font-size: 24px;
        font-weight: 650;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌱 FieldScanner</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Agricultural field vegetation intelligence"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Analysis Settings")

    uploaded_file = st.file_uploader(
        "Upload a field image",
        type=["jpg", "jpeg", "png", "tif", "tiff"],
    )

    st.divider()

    field_area = st.number_input(
        "Field area (hectares)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        help="Optional. Used to calculate real-world area.",
    )

    target_coverage = st.slider(
        "Target vegetation coverage",
        min_value=10,
        max_value=100,
        value=80,
        step=5,
    )

    grid_size = st.select_slider(
        "Zone resolution",
        options=[4, 6, 8, 10, 12, 16],
        value=8,
    )

    sensitivity = st.slider(
        "Vegetation detection sensitivity",
        min_value=0.0,
        max_value=30.0,
        value=10.0,
        step=1.0,
        help=(
            "Lower values detect weaker vegetation but may increase "
            "false positives."
        ),
    )

    st.divider()

    analyze_button = st.button(
        "🔍 Analyze Field",
        use_container_width=True,
        type="primary",
    )


# ============================================================
# EMPTY STATE
# ============================================================

if uploaded_file is None:

    st.info(
        "👈 Upload a field image from the sidebar to begin analysis."
    )

    st.markdown("### How FieldScanner works")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📷 1. Upload")
        st.write(
            "Upload an RGB aerial, drone, satellite, or field image."
        )

    with col2:
        st.markdown("### 🌱 2. Analyze")
        st.write(
            "FieldScanner detects vegetation and calculates coverage."
        )

    with col3:
        st.markdown("### 🗺️ 3. Locate")
        st.write(
            "The field is divided into zones to identify areas "
            "with lower vegetation coverage."
        )

    st.stop()


# ============================================================
# IMAGE LOADING
# ============================================================

try:
    pil_image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(pil_image)

except Exception as e:
    st.error(f"Could not read this image: {e}")
    st.stop()


# ============================================================
# IMAGE PREVIEW
# ============================================================

st.markdown(
    '<div class="section-title">📷 Field Image</div>',
    unsafe_allow_html=True,
)

preview_col1, preview_col2 = st.columns([2, 1])

with preview_col1:
    st.image(
        img_array,
        caption=uploaded_file.name,
        use_container_width=True,
    )

with preview_col2:
    st.markdown("#### Image information")

    st.write(f"**Filename:** {uploaded_file.name}")
    st.write(f"**Width:** {img_array.shape[1]} px")
    st.write(f"**Height:** {img_array.shape[0]} px")
    st.write(f"**Channels:** {img_array.shape[2]}")
    st.write(
        f"**Grid:** {grid_size} × {grid_size}"
    )

    if field_area > 0:
        st.write(f"**Field area:** {field_area:.2f} ha")
    else:
        st.write("**Field area:** Not specified")


# ============================================================
# ANALYSIS
# ============================================================

if analyze_button:

    with st.spinner("Analyzing field..."):

        try:

            analyzer = FieldAnalyzer(
                exgr_threshold=sensitivity,
                grid_rows=grid_size,
                grid_cols=grid_size,
            )

            # IMPORTANT:
            # We now analyze the image directly from memory.
            report = analyzer.analyze_image(
                img_array,
                image_path=uploaded_file.name,
                field_area_hectares=(
                    field_area
                    if field_area > 0
                    else None
                ),
                target_coverage_pct=float(target_coverage),
            )

        except Exception as e:

            st.error(
                f"Analysis failed: {e}"
            )

            st.stop()


    # ========================================================
    # RESULTS
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Field Analysis</div>',
        unsafe_allow_html=True,
    )

    needing = (
        report.status_breakdown["needs_attention"]
        + report.status_breakdown["bare"]
    )

    total_cells = (
        report.grid_rows * report.grid_cols
    )

    coverage_gap = max(
        0.0,
        target_coverage - report.overall_green_pct,
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "🌱 Green Coverage",
            f"{report.overall_green_pct:.1f}%",
        )

    with m2:
        st.metric(
            "🎯 Target",
            f"{target_coverage:.0f}%",
        )

    with m3:
        st.metric(
            "📉 Coverage Gap",
            f"{coverage_gap:.1f}%",
        )

    with m4:
        st.metric(
            "⚠️ Attention Zones",
            f"{needing}/{total_cells}",
        )


    # --------------------------------------------------------
    # REAL-WORLD AREA
    # --------------------------------------------------------

    if report.total_area_m2 is not None:

        st.markdown(
            '<div class="section-title">📐 Area Analysis</div>',
            unsafe_allow_html=True,
        )

        a1, a2, a3 = st.columns(3)

        with a1:
            st.metric(
                "Total Field Area",
                f"{report.total_area_m2:,.0f} m²",
            )

        with a2:
            st.metric(
                "Vegetated Area",
                f"{report.vegetated_area_m2:,.0f} m²",
            )

        with a3:
            st.metric(
                "Additional Area Needed",
                f"{report.deficit_area_m2:,.0f} m²",
            )


    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">💡 Analysis Summary</div>',
        unsafe_allow_html=True,
    )

    st.info(report.recommendation)


    # ========================================================
    # VISUAL ANALYSIS
    # ========================================================

    st.markdown(
        '<div class="section-title">🗺️ Vegetation Analysis Map</div>',
        unsafe_allow_html=True,
    )

    overlay_buffer = io.BytesIO()

    try:

        from field_scanner.visualize import save_mask_overlay

        save_mask_overlay(
            img_array,
            overlay_buffer,
            exgr_threshold=sensitivity,
        )

        overlay_buffer.seek(0)

    except Exception as e:

        st.warning(
            f"Could not generate vegetation overlay: {e}"
        )

        overlay_buffer = None


    heatmap_buffer = io.BytesIO()

    try:

        save_grid_heatmap(
            img_array,
            report,
            heatmap_buffer,
        )

        heatmap_buffer.seek(0)

    except Exception as e:

        st.warning(
            f"Could not generate zone map: {e}"
        )

        heatmap_buffer = None


    map_col1, map_col2 = st.columns(2)

    with map_col1:

        st.markdown("#### 🌱 Detected Vegetation")

        if overlay_buffer is not None:
            st.image(
                overlay_buffer,
                use_container_width=True,
            )

    with map_col2:

        st.markdown("#### 🗺️ Zone Coverage Map")

        if heatmap_buffer is not None:
            st.image(
                heatmap_buffer,
                use_container_width=True,
            )


    # ========================================================
    # ZONE BREAKDOWN
    # ========================================================

    st.markdown(
        '<div class="section-title">📍 Zone Breakdown</div>',
        unsafe_allow_html=True,
    )

    b = report.status_breakdown

    z1, z2, z3, z4 = st.columns(4)

    with z1:
        st.metric(
            "🟢 Healthy",
            b["healthy"],
        )

    with z2:
        st.metric(
            "🟡 Moderate",
            b["moderate"],
        )

    with z3:
        st.metric(
            "🟠 Needs Attention",
            b["needs_attention"],
        )

    with z4:
        st.metric(
            "🔴 Bare",
            b["bare"],
        )


    # ========================================================
    # DETAILED ZONES
    # ========================================================

    with st.expander("🔎 View individual zones"):

        for cell in report.cells:

            st.write(
                f"**Zone {cell.row + 1}-{cell.col + 1}** — "
                f"{cell.green_fraction * 100:.1f}% vegetation — "
                f"`{cell.status}`"
            )


    # ========================================================
    # DOWNLOAD REPORT
    # ========================================================

    st.markdown(
        '<div class="section-title">📄 Export</div>',
        unsafe_allow_html=True,
    )

    report_json = report.to_dict()

    st.download_button(
        "⬇️ Download JSON Report",
        data=str(report_json).encode(),
        file_name="field_coverage_report.json",
        mime="application/json",
        use_container_width=True,
    )

else:

    st.success(
        "Image loaded. Configure your settings and click "
        "**Analyze Field** to begin."
    )
