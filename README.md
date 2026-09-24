# 🌱 FieldScanner

**FieldScanner** is an image-based agricultural field analysis application built with Python and Streamlit.

It analyzes field images to estimate visible vegetation coverage, divide the image into zones, identify areas requiring attention, and generate visual and PDF reports.

> **Note:** FieldScanner is an image-analysis tool. Its vegetation confidence and coverage measurements are estimates derived from RGB imagery and should not be treated as direct measurements of crop physiological health.

---

## ✨ Features

### 🔍 Field Analysis

* Upload a field image directly through the Streamlit dashboard.
* Analyze vegetation using RGB-based vegetation indices.
* Estimate visible vegetation coverage.
* Divide the field image into analysis zones.
* Classify zones according to vegetation coverage.

### 📊 Coverage Analytics

FieldScanner provides:

* Overall vegetation coverage percentage
* Target coverage comparison
* Zone distribution
* High, moderate, low, and very-low coverage areas
* Per-zone vegetation measurements

### 🗺️ Visual Analysis

The application generates several visualizations:

* **Vegetation Mask Overlay** — highlights detected vegetation.
* **Zone Coverage Heatmap** — displays vegetation coverage across field zones.
* **Vegetation Confidence Map** — shows how strongly individual pixels match the RGB characteristics used by the vegetation model.

### 📄 Reports & Export

Analysis results can be exported as:

* **JSON** — structured analysis data
* **CSV** — detailed zone-by-zone data
* **PDF** — professional field analysis report

The PDF report can include:

* Executive summary
* Coverage statistics
* Area analysis
* Original field image
* Vegetation overlay
* Zone coverage map
* Vegetation confidence map
* Zone summary
* Detailed zone analysis
* Interpretation
* Methodology
* Limitations
* Final status

---

## 🧠 How It Works

FieldScanner uses RGB image processing to identify vegetation characteristics.

A simplified analysis pipeline is:

```text
Field Image
     │
     ▼
Image Preprocessing
     │
     ▼
RGB Vegetation Analysis
     │
     ├── ExG
     ├── ExR
     └── ExGR
     │
     ▼
Vegetation Detection
     │
     ▼
Zone-Based Analysis
     │
     ├── Coverage %
     ├── Zone Status
     └── Area Estimation
     │
     ▼
Visualizations
     │
     ├── Vegetation Overlay
     ├── Coverage Heatmap
     └── Confidence Map
     │
     ▼
Reports & Export
     ├── JSON
     ├── CSV
     └── PDF
```

---

## 📁 Project Structure

```text
field_scanner/
│
├── app.py
├── requirements.txt
├── README.md
│
└── field_scanner/
    ├── analyzer.py
    ├── vegetation_index.py
    ├── visualize.py
    └── report_generator.py
```

### `app.py`

Main Streamlit application and user interface.

### `analyzer.py`

Contains the main field-analysis logic, including:

* `FieldAnalyzer`
* `FieldReport`
* `CellResult`

### `vegetation_index.py`

Contains RGB vegetation-analysis functions, including:

* ExG
* ExR
* ExGR
* HSV-based confirmation
* Continuous vegetation confidence
* NDVI helper functionality

### `visualize.py`

Generates analysis visualizations:

* Vegetation mask overlay
* Grid heatmap
* Vegetation confidence map

### `report_generator.py`

Creates professional PDF field-analysis reports using ReportLab.

---

## 🛠️ Technology Stack

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| Python     | Core programming language      |
| Streamlit  | Interactive web dashboard      |
| NumPy      | Numerical image processing     |
| OpenCV     | Image-processing operations    |
| Pillow     | Image loading and manipulation |
| Matplotlib | Visualization generation       |
| Pandas     | CSV/data handling              |
| ReportLab  | PDF report generation          |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd field_scanner
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running FieldScanner

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

## 📷 Using the Application

### Step 1 — Upload

Upload a suitable RGB field image through the dashboard.

### Step 2 — Configure

Adjust the analysis settings, including vegetation-detection sensitivity and target coverage where applicable.

### Step 3 — Analyze

Run the field analysis.

FieldScanner calculates vegetation coverage and produces zone-level results.

### Step 4 — Inspect

Review:

* Overall coverage
* Zone classifications
* Coverage analytics
* Vegetation overlay
* Zone heatmap
* Confidence map

### Step 5 — Export

Download the results in:

```text
JSON
CSV
PDF
```

---

## 📐 Area Analysis

When appropriate field dimensions or scale information are available, FieldScanner can associate detected pixel areas with estimated real-world areas.

Zone results may include:

* Pixel area
* Vegetation coverage
* Estimated real area in square metres

Real-world area estimates depend on the accuracy of the supplied scale information.

---

## 🎯 Zone Classification

Field zones are grouped into four categories:

| Category          | Description                        |
| ----------------- | ---------------------------------- |
| High Coverage     | Strong visible vegetation coverage |
| Moderate Coverage | Intermediate vegetation coverage   |
| Low Coverage      | Lower vegetation coverage          |
| Very Low Coverage | Very limited visible vegetation    |

These classifications are image-derived and should be interpreted together with the original field image.

---

## ⚠️ Limitations

FieldScanner currently works primarily with **RGB imagery**.

Therefore:

* Lighting conditions can affect vegetation detection.
* Shadows can influence RGB measurements.
* Soil and vegetation with similar colours may affect classification.
* Camera characteristics can influence results.
* Image quality and resolution affect analysis.
* RGB vegetation confidence is not equivalent to plant-health probability.
* The system does not directly measure physiological crop health.
* Estimated real-world areas depend on reliable image scaling.

For agricultural decision-making, FieldScanner should therefore be considered an **analysis and visualization aid**, rather than a replacement for field inspection or calibrated agricultural sensing.

---

## 🔮 Future Development

Potential future improvements include:

* Multispectral imagery support
* NDVI-based analysis using appropriate sensor data
* GPS/geospatial field mapping
* Historical analysis and trend tracking
* Before/after field comparison
* More advanced crop segmentation
* Automated anomaly detection
* Expanded PDF analytics and charts
* Field-level dashboards
* Machine-learning-based vegetation classification

---

## 🚀 Deployment

FieldScanner is designed to run as a Streamlit application and can be deployed through **Streamlit Community Cloud**.

Deployment configuration:

```text
Branch: master
Main file: app.py
```

Dependencies are provided in:

```text
requirements.txt
```

---

## 📜 License

Add your preferred license here.

For example:

```text
MIT License
```

---

## 👨‍💻 Project

**FieldScanner**

An image-based field vegetation analysis and reporting application built with Python and Streamlit.
