# 🌱 Agridrone AI — FieldScanner

**FieldScanner** is an image-based agricultural field analysis application developed under **Agridrone AI**.

It uses RGB imagery to estimate visible vegetation coverage, divide a field image into analysis zones, identify lower-coverage areas, generate visualizations, and produce downloadable reports.

## 🚀 Live Demo

The application is deployed using **Streamlit Community Cloud**.

**Live App:** `YOUR_STREAMLIT_APP_URL`

---

## ✨ Features

### 📷 Image Input

FieldScanner supports:

* User-uploaded field images
* Built-in sample field images
* JPG, JPEG, PNG, TIFF and TIF formats
* RGB field, drone, aerial and satellite imagery

Users can either upload their own image or select from the built-in sample fields for an immediate demonstration.

### 🌱 Vegetation Analysis

FieldScanner performs RGB-based vegetation detection using image-derived vegetation characteristics, including:

* Excess Green (ExG)
* Excess Red (ExR)
* Excess Green minus Excess Red (ExGR)
* HSV-based confirmation
* Continuous vegetation confidence estimation

The result is an estimate of **visible vegetation coverage from the image**.

### 🗺️ Zone-Based Analysis

The field image can be divided into configurable zones.

For each zone, FieldScanner reports:

* Vegetation coverage
* Coverage classification
* Pixel area
* Estimated real-world area when field area information is provided

Zones are classified as:

| Classification       | Meaning                                  |
| -------------------- | ---------------------------------------- |
| 🟢 High Coverage     | Strong visible vegetation coverage       |
| 🟡 Moderate Coverage | Intermediate visible vegetation coverage |
| 🟠 Low Coverage      | Reduced visible vegetation coverage      |
| 🔴 Very Low Coverage | Limited visible vegetation coverage      |

### 📊 Coverage Analytics

The dashboard provides:

* Overall visible vegetation coverage
* Configured target coverage
* Coverage gap
* Number of low-coverage zones
* Coverage-vs-target chart
* Zone distribution chart
* Area analysis when field area is available

### 🎨 Visual Analysis

FieldScanner generates:

**Detected Vegetation Overlay**
Highlights image regions classified as visible vegetation.

**Coverage Zone Map**
Shows spatial variation in vegetation coverage across the field.

**Vegetation Confidence Map**
Shows how strongly individual RGB pixels match the vegetation characteristics used by the image-based model.

### 📄 Export

Analysis results can be downloaded as:

* **JSON** — structured field analysis data
* **CSV** — zone-by-zone analysis
* **PDF** — professional field analysis report

The PDF can contain:

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

## 🧠 How FieldScanner Works

```text
              Field Image
                   │
                   ▼
          Image Preprocessing
                   │
                   ▼
          RGB Vegetation Analysis
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
        ExG       ExR       ExGR
         │         │         │
         └─────────┼─────────┘
                   ▼
         Vegetation Detection
                   │
                   ▼
            Zone Analysis
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Coverage %   Status     Area Estimate
        │          │          │
        └──────────┼──────────┘
                   ▼
             Visual Output
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
   Overlay      Heatmap     Confidence
      │            │            │
      └────────────┼────────────┘
                   ▼
              Export Results
         ┌─────────┼─────────┐
         ▼         ▼         ▼
        JSON      CSV        PDF
```

---

## 📁 Project Structure

```text
field_scanner/
│
├── app.py
├── README.md
├── requirements.txt
│
├── sample_images/
│   ├── sample_image01.jpg
│   ├── sample_image02.jpg
│   ├── sample_image03.jpg
│   ├── sample_image04.jpg
│   ├── sample_image05.jpg
│   ├── sample_image06.jpg
│   ├── sample_image07.jpg
│   ├── sample_image08.jpg
│   └── sample_image09.jpg
│
└── field_scanner/
    ├── analyzer.py
    ├── vegetation_index.py
    ├── visualize.py
    └── report_generator.py
```

### `app.py`

Main Streamlit application and dashboard interface.

### `analyzer.py`

Contains the core field-analysis engine and result data structures.

### `vegetation_index.py`

Contains RGB vegetation-index calculations and vegetation-confidence logic.

### `visualize.py`

Generates:

* Vegetation mask overlays
* Zone heatmaps
* Vegetation confidence maps

### `report_generator.py`

Generates professional PDF field-analysis reports.

### `sample_images/`

Contains built-in images that allow users to test FieldScanner without uploading their own field image.

---

## 🛠️ Technology Stack

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| Python     | Core application             |
| Streamlit  | Interactive web interface    |
| NumPy      | Numerical processing         |
| OpenCV     | Image processing             |
| Pillow     | Image loading and processing |
| Matplotlib | Visualization                |
| Pandas     | Tabular data and CSV export  |
| ReportLab  | PDF report generation        |

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/notgrimreaper666/field_scanner.git
cd field_scanner
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run Locally

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

The local application will normally be available at:

```text
http://localhost:8501
```

---

## 📷 Using FieldScanner

### 1. Upload or Select a Sample

Users can either upload a field image or choose one of the built-in sample fields.

### 2. Configure Analysis

Available settings include:

* Field area
* Target vegetation coverage
* Zone resolution
* Vegetation detection sensitivity

### 3. Analyze

Click:

```text
🔍 Analyze Field
```

FieldScanner processes the image and generates the field report.

### 4. Review

The dashboard provides:

* Field overview
* Coverage status
* Coverage progress
* Analytics
* Visual analysis
* Zone summary
* Detailed zone analysis
* Interpretation

### 5. Export

Download:

```text
JSON
CSV
PDF
```

---

## 📐 Real-World Area Analysis

When field area is supplied, FieldScanner can convert image-derived pixel areas into estimated real-world areas.

This allows the report to include values such as:

* Total field area
* Visible vegetated area
* Estimated coverage shortfall
* Per-zone real area

Real-world area estimates depend on the accuracy of the supplied field-area information and image representation.

---

## ⚠️ Limitations

FieldScanner is currently primarily an **RGB image-analysis system**.

Results can be affected by:

* Lighting conditions
* Shadows
* Camera characteristics
* Image quality
* Soil colour
* Vegetation colour
* Image resolution
* Environmental conditions

The vegetation-confidence value is an **image-derived confidence score**, not a probability.

FieldScanner does **not** directly measure:

* Physiological crop health
* Biomass
* Nutrient status
* Water stress
* Yield
* Disease severity

The system should therefore be treated as an **analysis and visualization aid**, not as a replacement for calibrated agricultural sensors, field inspection, or professional agronomic assessment.

---

## 🔮 Future Development

Planned or potential future improvements include:

* Multispectral imagery support
* Native NDVI analysis with suitable sensor data
* GPS and geospatial field mapping
* Historical field analysis
* Before/after comparisons
* Automated anomaly detection
* Advanced vegetation segmentation
* Machine-learning-based classification
* Trend and time-series dashboards
* Enhanced PDF analytics
* Field-level mapping and reporting

---

## 🌾 Sample Images

FieldScanner includes nine built-in sample images so users can explore the application without supplying their own image.

These sample files are stored locally in:

```text
sample_images/
```

When distributing or publishing the repository, verify that the images are licensed for redistribution and add attribution or license information where required.

---

## 🚀 Deployment

FieldScanner is designed for deployment on **Streamlit Community Cloud**.

Current repository configuration:

```text
Repository: notgrimreaper666/field_scanner
Branch: master
Main file: app.py
```

Updates pushed to the connected GitHub repository can be reflected in the deployed application through Streamlit Community Cloud's repository-based deployment workflow.

---

## 🔄 Development Workflow

The project can be developed through GitHub Codespaces or any local Python environment.

Typical workflow:

```bash
git pull origin master

# Make changes

python -m py_compile app.py

python -m streamlit run app.py

git add .
git commit -m "Describe your changes"
git push origin master
```

---

## 📜 License

Add the project's chosen license here.

For example:

```text
MIT License
```

---

## 👨‍💻 Project

### Agridrone AI

**FieldScanner**

Agricultural field vegetation intelligence from RGB imagery.

Built with Python, Streamlit, OpenCV, NumPy, Pandas, Matplotlib and ReportLab.
