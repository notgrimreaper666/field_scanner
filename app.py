from pathlib import Path
import io
import json

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from field_scanner.analyzer import FieldAnalyzer
from field_scanner.visualize import (
    save_mask_overlay,
    save_grid_heatmap,
    save_confidence_map,
)
from field_scanner.report_generator import generate_pdf_report


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FieldScanner",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "report" not in st.session_state:
    st.session_state.report = None

if "image_array" not in st.session_state:
    st.session_state.image_array = None

if "image_name" not in st.session_state:
    st.session_state.image_name = ""

if "overlay_buffer" not in st.session_state:
    st.session_state.overlay_buffer = None

if "heatmap_buffer" not in st.session_state:
    st.session_state.heatmap_buffer = None
if "confidence_buffer" not in st.session_state:
    st.session_state.confidence_buffer = None

if "target_coverage" not in st.session_state:
    st.session_state.target_coverage = 80.0


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       GLOBAL
    -------------------------------------------------------- */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* --------------------------------------------------------
       HEADER
    -------------------------------------------------------- */

    .hero {
        padding: 28px 32px;
        border-radius: 20px;
        background:
            linear-gradient(
                135deg,
                #e8f5e9 0%,
                #f7fbf7 55%,
                #ffffff 100%
            );
        border: 1px solid #d5ead7;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #1b5e20;
        letter-spacing: -1px;
        margin-bottom: 4px;
    }

    .hero-subtitle {
        font-size: 17px;
        color: #607064;
        margin-bottom: 0;
    }

    .hero-badge {
        display: inline-block;
        margin-top: 15px;
        padding: 6px 12px;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid #c8e6c9;
        color: #2e7d32;
        font-size: 13px;
        font-weight: 600;
    }

    /* --------------------------------------------------------
       SECTION HEADERS
    -------------------------------------------------------- */

    .section-header {
        font-size: 25px;
        font-weight: 750;
        color: #1b5e20;
        margin-top: 30px;
        margin-bottom: 14px;
    }

    .section-description {
        color: #68756b;
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 16px;
    }

    /* --------------------------------------------------------
       METRIC CARDS
    -------------------------------------------------------- */

    .metric-card {
        background: #ffffff;
        border: 1px solid #e1e8e2;
        border-radius: 16px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.035);
    }

    .metric-icon {
        font-size: 21px;
        margin-bottom: 5px;
    }

    .metric-label {
        color: #6b756e;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .metric-value {
        color: #1f2b22;
        font-size: 29px;
        font-weight: 800;
    }

    .metric-sub {
        color: #879188;
        font-size: 12px;
        margin-top: 3px;
    }

    /* --------------------------------------------------------
       STATUS
    -------------------------------------------------------- */

    .status-good {
        padding: 18px 20px;
        border-radius: 14px;
        background: #edf7ee;
        border: 1px solid #c8e6c9;
        color: #245c29;
    }

    .status-warning {
        padding: 18px 20px;
        border-radius: 14px;
        background: #fff8e7;
        border: 1px solid #ffe0a3;
        color: #775719;
    }

    /* --------------------------------------------------------
       INFO CARDS
    -------------------------------------------------------- */

    .info-card {
        padding: 20px;
        border-radius: 16px;
        background: #f8faf8;
        border: 1px solid #e1e8e2;
    }

    .info-title {
        font-size: 15px;
        font-weight: 700;
        color: #2e4733;
        margin-bottom: 8px;
    }

    .info-text {
        font-size: 14px;
        color: #68756b;
        line-height: 1.6;
    }

    /* --------------------------------------------------------
       SIDEBAR
    -------------------------------------------------------- */

    section[data-testid="stSidebar"] {
        border-right: 1px solid #e1e8e2;
    }

    /* --------------------------------------------------------
       BUTTONS
    -------------------------------------------------------- */

    div.stButton > button {
        border-radius: 10px;
        font-weight: 650;
    }

    div.stDownloadButton > button {
        border-radius: 10px;
        font-weight: 650;
    }

    /* --------------------------------------------------------
       DIVIDERS
    -------------------------------------------------------- */

    hr {
        border-color: #e7ece8;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🌱 FieldScanner</div>
        <div class="hero-subtitle">
            Agricultural field vegetation intelligence from RGB imagery
        </div>
        <div class="hero-badge">
            ● RGB Field Analysis
        </div>
    </div>
    """,
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
        help="Upload an RGB field, drone, aerial, or satellite image.",
    )

    st.divider()

    # --------------------------------------------------------
    # SAMPLE FIELD IMAGES
    # --------------------------------------------------------

    st.markdown("### 🌱 Try a Sample Field")

    st.caption(
        "No field image? Choose one of our built-in samples."
    )

    sample_dir = Path(__file__).parent / "sample_images"

    sample_files = sorted(
        sample_dir.glob("sample_image*.jpg")
    )

    sample_options = [
        path.name
        for path in sample_files
    ]

    selected_sample = None

    if sample_options:

        selected_sample = st.selectbox(
            "Choose a sample",
            ["None"] + sample_options,
            format_func=lambda x: (
                "— Select a sample —"
                if x == "None"
                else x.replace(
                    "sample_image",
                    "Sample Field "
                ).replace(
                    ".jpg",
                    ""
                )
            ),
        )

    else:

        st.warning(
            "No sample images found."
        )

    st.divider()

    # --------------------------------------------------------
    # FIELD SETTINGS
    # --------------------------------------------------------

    field_area = st.number_input(
        "Field area (hectares)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        help="Optional. Enables real-world area calculations.",
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
            "Lower values detect weaker green signals but may "
            "increase false positives."
        ),
    )

    st.divider()

    analyze_button = st.button(
        "🔍 Analyze Field",
        width="stretch",
        type="primary",
    )

    st.caption(
        "FieldScanner estimates visible vegetation coverage "
        "from RGB imagery. It is not a crop-health diagnostic."
    )

# ============================================================
# EMPTY STATE
# ============================================================

if (
    uploaded_file is None
    and (selected_sample is None or selected_sample == "None")
    and st.session_state.report is None
):

    st.markdown(
        '<div class="section-header">Get started</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "👈 Upload a field image from the sidebar to begin analysis."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">📷 1. Upload</div>
                <div class="info-text">
                    Upload an RGB field, drone, aerial or satellite image.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">🌱 2. Analyze</div>
                <div class="info-text">
                    FieldScanner detects visible green vegetation
                    using RGB color characteristics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">🗺️ 3. Understand</div>
                <div class="info-text">
                    The field is divided into zones so lower-coverage
                    areas can be identified spatially.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


# ============================================================
# IMAGE LOADING
# ============================================================

if uploaded_file is not None:

    try:

        pil_image = Image.open(uploaded_file).convert("RGB")
        current_image = np.array(pil_image)

        st.session_state.image_array = current_image
        st.session_state.image_name = uploaded_file.name

    except Exception as e:

        st.error(f"Could not read this image: {e}")
        st.stop()


# ============================================================
# ANALYZE
# ============================================================

if analyze_button:

    # --------------------------------------------------------
    # Determine which image to analyze
    # --------------------------------------------------------

    if uploaded_file is not None:

        image_to_analyze = st.session_state.image_array
        image_name = st.session_state.image_name

    elif selected_sample is not None and selected_sample != "None":

        selected_path = sample_dir / selected_sample

        try:

            sample_image = Image.open(
                selected_path
            ).convert("RGB")

            image_to_analyze = np.array(
                sample_image
            )

            image_name = selected_sample

            st.session_state.image_array = image_to_analyze
            st.session_state.image_name = image_name

        except Exception as e:

            st.error(
                f"Could not load sample image: {e}"
            )

            st.stop()

    else:

        st.error(
            "Please upload an image or choose a sample field."
        )

        st.stop()

    # --------------------------------------------------------
    # Run analysis
    # --------------------------------------------------------

    with st.spinner("Analyzing field..."):

        try:

            analyzer = FieldAnalyzer(
                exgr_threshold=sensitivity,
                grid_rows=grid_size,
                grid_cols=grid_size,
            )

            report = analyzer.analyze_image(
                image_to_analyze,
                image_path=image_name,
                field_area_hectares=(
                    field_area
                    if field_area > 0
                    else None
                ),
                target_coverage_pct=float(
                    target_coverage
                ),
            )

            st.session_state.report = report

            st.session_state.target_coverage = float(
                target_coverage
            )

            # ------------------------------------------------
            # Generate visual outputs
            # ------------------------------------------------

            overlay_buffer = io.BytesIO()

            save_mask_overlay(
                image_to_analyze,
                overlay_buffer,
                exgr_threshold=sensitivity,
            )

            overlay_buffer.seek(0)

            heatmap_buffer = io.BytesIO()

            save_grid_heatmap(
                image_to_analyze,
                report,
                heatmap_buffer,
            )

            heatmap_buffer.seek(0)

            st.session_state.overlay_buffer = (
                overlay_buffer.getvalue()
            )

            st.session_state.heatmap_buffer = (
                heatmap_buffer.getvalue()
            )

            confidence_buffer = io.BytesIO()

            save_confidence_map(
                image_to_analyze,
                confidence_buffer,
                exgr_threshold=sensitivity,
            )

            confidence_buffer.seek(0)

            st.session_state.confidence_buffer = (
                confidence_buffer.getvalue()
            )

        except Exception as e:

            st.error(
                f"Analysis failed: {e}"
            )

            st.stop()


# ============================================================
# RETRIEVE RESULTS
# ============================================================

report = st.session_state.report

if report is None:

    st.info(
        "Configure your settings and click **Analyze Field**."
    )

    st.stop()


img_array = st.session_state.image_array

target_coverage = st.session_state.target_coverage


# ============================================================
# IMAGE INFORMATION
# ============================================================

st.markdown(
    '<div class="section-header">📷 Field Image</div>',
    unsafe_allow_html=True,
)

image_col, info_col = st.columns([2.2, 1])

with image_col:

    st.image(
        img_array,
        caption=st.session_state.image_name,
        width="stretch",
    )

with info_col:

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">Image Information</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        f"**Filename:** {st.session_state.image_name}"
    )

    st.write(
        f"**Resolution:** "
        f"{img_array.shape[1]:,} × {img_array.shape[0]:,} px"
    )

    st.write(
        f"**Channels:** {img_array.shape[2]}"
    )

    st.write(
        f"**Grid:** "
        f"{report.grid_rows} × {report.grid_cols}"
    )

    if report.total_area_m2 is not None:

        st.write(
            f"**Field area:** "
            f"{report.total_area_m2 / 10_000:.2f} ha"
        )

    else:

        st.write(
            "**Field area:** Not specified"
        )


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-header">📊 Field Overview</div>',
    unsafe_allow_html=True,
)

coverage = report.overall_green_pct

coverage_gap = max(
    0.0,
    target_coverage - coverage,
)

total_cells = (
    report.grid_rows * report.grid_cols
)

low_coverage_zones = (
    report.status_breakdown["needs_attention"]
    + report.status_breakdown["bare"]
)


# ============================================================
# METRIC CARDS
# ============================================================

m1, m2, m3, m4 = st.columns(4)


with m1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">🌱</div>
            <div class="metric-label">Visible Vegetation</div>
            <div class="metric-value">{coverage:.1f}%</div>
            <div class="metric-sub">Detected from RGB imagery</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with m2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-label">Target Coverage</div>
            <div class="metric-value">{target_coverage:.0f}%</div>
            <div class="metric-sub">Configured field target</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with m3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">📉</div>
            <div class="metric-label">Coverage Gap</div>
            <div class="metric-value">{coverage_gap:.1f}%</div>
            <div class="metric-sub">Relative to target</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with m4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">📍</div>
            <div class="metric-label">Low-Coverage Zones</div>
            <div class="metric-value">
                {low_coverage_zones}/{total_cells}
            </div>
            <div class="metric-sub">
                Below the configured coverage classification
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COVERAGE STATUS
# ============================================================

st.markdown(
    '<div class="section-header">🎯 Coverage Status</div>',
    unsafe_allow_html=True,
)

if coverage >= target_coverage:

    st.markdown(
        f"""
        <div class="status-good">
            <b>Target coverage reached.</b><br>
            Detected visible vegetation coverage is
            <b>{coverage:.1f}%</b>, compared with the configured
            target of <b>{target_coverage:.1f}%</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="status-warning">
            <b>Coverage is below the configured target.</b><br>
            Detected visible vegetation coverage is
            <b>{coverage:.1f}%</b>, which is
            <b>{coverage_gap:.1f} percentage points</b>
            below the target of <b>{target_coverage:.1f}%</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COVERAGE PROGRESS
# ============================================================

st.markdown(
    '<div class="section-header">📈 Coverage Progress</div>',
    unsafe_allow_html=True,
)

progress_value = min(
    coverage / 100,
    1.0,
)

st.progress(
    progress_value,
    text=f"{coverage:.1f}% visible vegetation coverage",
)

st.caption(
    f"Configured target: {target_coverage:.0f}%"
)


# ============================================================
# AREA ANALYSIS
# ============================================================

# ============================================================
# ANALYTICS
# ============================================================

st.markdown(
    '<div class="section-header">📊 Coverage Analytics</div>',
    unsafe_allow_html=True,
)

chart_col1, chart_col2 = st.columns(2)


# ------------------------------------------------------------
# COVERAGE VS TARGET
# ------------------------------------------------------------

with chart_col1:

    st.markdown("#### 🎯 Coverage vs Target")

    coverage_chart = pd.DataFrame(
        {
            "Metric": [
                "Visible Vegetation",
                "Target Coverage",
            ],
            "Coverage (%)": [
                coverage,
                target_coverage,
            ],
        }
    )

    st.bar_chart(
        coverage_chart.set_index("Metric"),
        y="Coverage (%)",
        horizontal=True,
    )

    st.caption(
        "Comparison between detected visible vegetation "
        "coverage and the configured target."
    )


# ------------------------------------------------------------
# ZONE DISTRIBUTION
# ------------------------------------------------------------

with chart_col2:

    st.markdown("#### 🗺️ Zone Distribution")

    zone_chart = pd.DataFrame(
    {
        "Coverage Category": [
            "High Coverage",
            "Moderate Coverage",
            "Low Coverage",
            "Very Low Coverage",
        ],
        "Zones": [
            report.status_breakdown["healthy"],
            report.status_breakdown["moderate"],
            report.status_breakdown["needs_attention"],
            report.status_breakdown["bare"],
        ],
    }
)

    st.bar_chart(
        zone_chart.set_index(
            "Coverage Category"
        ),
        y="Zones",
    )

    st.caption(
        "Number of image zones in each vegetation "
        "coverage category."
    )

if report.total_area_m2 is not None:

    st.markdown(
        '<div class="section-header">📐 Area Analysis</div>',
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
            "Visible Vegetated Area",
            f"{report.vegetated_area_m2:,.0f} m²",
        )

    with a3:

        st.metric(
            "Estimated Coverage Shortfall",
            f"{report.deficit_area_m2:,.0f} m²",
        )


# ============================================================
# ANALYSIS SUMMARY
# ============================================================

st.markdown(
    '<div class="section-header">💡 Analysis Summary</div>',
    unsafe_allow_html=True,
)

st.info(
    report.recommendation
)


# ============================================================
# VISUAL ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-header">🗺️ Visual Analysis</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-description">'
    "Compare the original field with the detected vegetation "
    "and spatial coverage classification."
    "</div>",
    unsafe_allow_html=True,
)


visual_col1, visual_col2, visual_col3 = st.columns(3)


with visual_col1:

    st.markdown("#### 🌱 Detected Vegetation")

    if st.session_state.overlay_buffer is not None:

        st.image(
            st.session_state.overlay_buffer,
            width="stretch",
        )

    st.caption(
        "Green highlighting represents pixels classified as "
        "visible vegetation by the RGB detector."
    )


with visual_col2:

    st.markdown("#### 🗺️ Coverage Zone Map")

    if st.session_state.heatmap_buffer is not None:

        st.image(
            st.session_state.heatmap_buffer,
            width="stretch",
        )

    st.caption(
        "Zones are classified according to their detected "
        "visible vegetation coverage."
    )

with visual_col3:

    st.markdown("#### 🌡️ Vegetation Confidence")

    if st.session_state.confidence_buffer is not None:

        st.image(
            st.session_state.confidence_buffer,
            width="stretch",
        )

    st.caption(
        "Higher values indicate stronger agreement with "
        "the RGB vegetation characteristics used by the model."
    )

# ============================================================
# ZONE SUMMARY
# ============================================================

st.markdown(
    '<div class="section-header">📍 Coverage Zone Summary</div>',
    unsafe_allow_html=True,
)

b = report.status_breakdown

z1, z2, z3, z4 = st.columns(4)


with z1:

    st.metric(
        "🟢 High Coverage",
        b["healthy"],
    )


with z2:

    st.metric(
        "🟡 Moderate Coverage",
        b["moderate"],
    )


with z3:

    st.metric(
        "🟠 Low Coverage",
        b["needs_attention"],
    )


with z4:

    st.metric(
        "🔴 Very Low Coverage",
        b["bare"],
    )


# ============================================================
# ZONE TABLE
# ============================================================

st.markdown(
    '<div class="section-header">📋 Detailed Zone Analysis</div>',
    unsafe_allow_html=True,
)

zone_rows = []

status_display = {
    "healthy": "High Coverage",
    "moderate": "Moderate Coverage",
    "needs_attention": "Low Coverage",
    "bare": "Very Low Coverage",
}

for cell in report.cells:

    zone_rows.append(
        {
            "Zone": f"{cell.row + 1}-{cell.col + 1}",
            "Vegetation Coverage": (
                f"{cell.green_fraction * 100:.1f}%"
            ),
            "Coverage Status": status_display.get(
                cell.status,
                cell.status,
            ),
            "Pixel Area": cell.pixel_area,
            "Real Area": (
                f"{cell.real_area_m2:,.1f} m²"
                if cell.real_area_m2 is not None
                else "—"
            ),
        }
    )

st.dataframe(
    zone_rows,
    width="stretch",
    hide_index=True,
)


# ============================================================
# INTERPRETATION
# ============================================================

st.markdown(
    '<div class="section-header">🧠 Interpretation</div>',
    unsafe_allow_html=True,
)

if coverage >= target_coverage:

    interpretation_text = (
        f"The image contains approximately "
        f"{coverage:.1f}% visibly green vegetation according "
        f"to the current RGB classification settings. "
        f"This is at or above the configured target of "
        f"{target_coverage:.1f}%."
    )

else:

    interpretation_text = (
        f"The image contains approximately "
        f"{coverage:.1f}% visibly green vegetation according "
        f"to the current RGB classification settings. "
        f"This is {coverage_gap:.1f} percentage points below "
        f"the configured target of {target_coverage:.1f}%."
    )

st.markdown(
    f"""
    <div class="info-card">
        <div class="info-title">What the analysis indicates</div>
        <div class="info-text">
            {interpretation_text}
            <br><br>
            The zone map shows how detected vegetation coverage
            varies spatially across the image.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LIMITATIONS
# ============================================================

with st.expander("ℹ️ About this analysis"):

    st.write(
        """
        FieldScanner currently uses RGB imagery and
        color-based vegetation detection.

        The result represents visible vegetation coverage
        estimated from image characteristics. It should not
        be interpreted as a direct measurement of physiological
        crop health, biomass, nutrient status, water stress,
        or yield.

        Lighting, shadows, camera characteristics, soil color,
        image quality and environmental conditions can affect
        RGB classification.

        Future multispectral analysis can incorporate
        Near-Infrared information and indices such as NDVI.
        """
    )


# ============================================================
# EXPORT
# ============================================================

st.markdown(
    '<div class="section-header">📄 Export Results</div>',
    unsafe_allow_html=True,
)

export_col1, export_col2, export_col3 = st.columns(3)


# ------------------------------------------------------------
# JSON
# ------------------------------------------------------------

with export_col1:

    report_json = json.dumps(
        report.to_dict(),
        indent=2,
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download JSON",
        data=report_json,
        file_name="field_coverage_report.json",
        mime="application/json",
        width="stretch",
    )


# ------------------------------------------------------------
# CSV
# ------------------------------------------------------------

with export_col2:

    csv_rows = []

    for cell in report.cells:

        csv_rows.append(
            {
                "Zone": f"{cell.row + 1}-{cell.col + 1}",
                "Row": cell.row + 1,
                "Column": cell.col + 1,
                "Vegetation Coverage (%)": round(
                    cell.green_fraction * 100,
                    2,
                ),
                "Coverage Status": status_display.get(
                    cell.status,
                    cell.status,
                ),
                "Pixel Area": cell.pixel_area,
                "Real Area (m²)": (
                    round(cell.real_area_m2, 2)
                    if cell.real_area_m2 is not None
                    else None
                ),
            }
        )

    csv_df = pd.DataFrame(csv_rows)

    csv_data = csv_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📊 Download CSV",
        data=csv_data,
        file_name="fieldscanner_zone_analysis.csv",
        mime="text/csv",
        width="stretch",
    )


# ------------------------------------------------------------
# PDF
# ------------------------------------------------------------

with export_col3:

    try:

        overlay_for_pdf = None
        heatmap_for_pdf = None
        confidence_for_pdf = None

        if st.session_state.overlay_buffer is not None:

            overlay_for_pdf = io.BytesIO(
                st.session_state.overlay_buffer
            )

        if st.session_state.heatmap_buffer is not None:

            heatmap_for_pdf = io.BytesIO(
                st.session_state.heatmap_buffer
            )

        if st.session_state.confidence_buffer is not None:

            confidence_for_pdf = io.BytesIO(
                st.session_state.confidence_buffer
            )

        pdf_buffer = generate_pdf_report(
            report=report,
            original_image=img_array,
            overlay_buffer=overlay_for_pdf,
            heatmap_buffer=heatmap_for_pdf,
            confidence_buffer=confidence_for_pdf,
            target_coverage_pct=target_coverage,
            field_name=st.session_state.image_name,
        )

        st.download_button(
            "📄 Download Professional PDF",
            data=pdf_buffer.getvalue(),
            file_name="fieldscanner_field_report.pdf",
            mime="application/pdf",
            width="stretch",
            type="primary",
        )

    except Exception as e:

        st.error(
            f"Could not generate PDF report: {e}"
        )