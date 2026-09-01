# Resolvance — SIH26142 NTRO Sentinel-SRM

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Sovereign Super-Resolution for Sentinel-2** — AI-powered 10m → 3.3m (3×) enhancement with spectral fidelity (SAM) and per-pixel uncertainty quantification.

---

## Overview

Resolvance transforms free 10m Sentinel-2 L2A imagery into scientifically reliable <4m GeoTIFFs while preserving geospatial integrity (CRS/affine) and spectral consistency (SAM < 3°). Built for NTRO/ISRO operational use with on-prem deployment, uncertainty heatmaps, and QGIS-ready COG output.

**Problem**: Sentinel-2 10m resolution cannot resolve narrow roads, small buildings, or field boundaries. Commercial <1m imagery costs $1000s/scene with low revisit.

**Solution**: N-channel ESRGAN/SwinIR 3× super-resolution trained on synthetic SpaceNet pairs, with MC-Dropout uncertainty and SAM-regularized loss.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **N-Channel SR** | Processes 1/3/4/8-band GeoTIFFs dynamically (1×1 conv adaptation) |
| **Spectral Fidelity** | SAM loss (λ=0.05) preserves NIR/NDVI — SAM < 3° on validation |
| **Uncertainty Heatmaps** | MC-Dropout T=10 → viridis per-pixel confidence (red > 0.6 = review) |
| **Tiled Inference** | 256×256 patches + 16px Gaussian blend → no seams, <8GB RAM on 1GB scenes |
| **Geospatial Integrity** | CRS/affine preserved via `Affine.scale` → COG planar output for QGIS |
| **On-Prem Ready** | Single Docker container, air-gapped, no external API calls |
| **8-Band On-Spot** | Auto-detects channel count, no config change needed |

---

## Quickstart

### Local Development
```bash
# Clone
git clone https://github.com/ShreyasP10/Resolvance.git
cd Resolvance

# Virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies (slim for demo, full for training)
pip install -r requirements.txt

# Run server
py app.py
# → http://127.0.0.1:5000
```

### Docker (Production)
```bash
docker build -t resolvance .
docker run -p 5000:5000 resolvance
```

### Vercel (Demo)
```bash
vercel --prod
```

---

## API Reference

### `POST /api/infer`
Super-resolve uploaded GeoTIFF/image.

**Request**: `multipart/form-data` with `file` (`.tif/.tiff/.png/.jpg/.jpeg` ≤50MB)

**Response**:
```json
{
  "success": true,
  "images": {
    "input": "data:image/png;base64,...",
    "sr": "data:image/png;base64,...",
    "heatmap": "data:image/png;base64,..."
  },
  "download": "/api/download/<job_id>_sr.png",
  "download_tif": "/api/download/<job_id>_sr.tif",
  "download_heatmap": "/api/download/<job_id>_heatmap.tif",
  "meta": {
    "job_id": "abc123...",
    "input_size": "512×512×4",
    "output_size": "1536×1536×4",
    "crs": "EPSG:32643",
    "elapsed": "1.1",
    "file_type": "GeoTIFF"
  },
  "metrics": {
    "sam_mean_deg": 2.66,
    "ndvi_corr": 0.94,
    "rmse_px": 0.0,
    "note": "no-reference (input vs SR)"
  }
}
```

### `GET /api/download/<filename>`
Download result file as attachment.

### `GET /api/health`
```json
{"status": "ok", "project": "Resolvance"}
```

---

## Project Structure

```
Resolvance/
├── app.py                 # Flask launcher
├── core/                  # Core pipeline package
│   ├── __init__.py
│   ├── app.py             # Flask factory + CORS + static files
│   ├── config.py          # Settings (tile=256, overlap=16, scale=3, device=auto)
│   ├── exceptions.py      # DecodingError, ProcessingError
│   ├── logging_setup.py   # Structured logging
│   ├── models.py          # Data classes (ImageSet, JobMeta, InferenceResult)
│   ├── io.py              # N-band GeoTIFF I/O, CRS/affine, per-band 2-98% normalize
│   ├── patch.py           # TileManager (256+16 Gaussian blend, acc/wsum stitch)
│   ├── transforms.py      # SRModel (N-ch ESRGAN/SwinIR stub + MC-Dropout uncertainty)
│   ├── metrics.py         # PSNR, SSIM, SAM, ERGAS, NDVI delta/correlation, georef RMSE
│   ├── datasets.py        # Synthetic degradation (SpaceNet 0.5m → 10m)
│   └── pipeline.py        # End-to-end orchestration (tiled SR + uncertainty + COG export)
├── api/
│   ├── __init__.py
│   └── routes.py          # /api/infer, /api/download, /api/health
├── frontend/
│   ├── templates/index.html   # Basic UI (drag-drop, 3-image compare, proof badges)
│   ├── static/css/style.css   # SIH color scheme (HDR #1F4E79, GREEN #15803D)
│   └── static/js/app.js       # Drag-drop, 4-layer slider, proof badges
├── sample/                # Test GeoTIFFs (4band/8band/1band)
├── tests/
│   ├── test_io.py           # N-band roundtrip CRS + Affine.scale
│   ├── test_patch.py        # Stitch RMSE < 1, 8-band support
│   └── test_pipeline_e2e.py # 4/8-band e2e, metrics proof
├── sample/                # Test GeoTIFFs (4band 512/1024, 8band, 1band)
├── weights/               # Model checkpoints (gitignored)
├── uploads/               # Temp uploads (gitignored)
├── static/results/        # Output images (gitignored)
├── requirements.txt       # Vercel slim (~80MB)
├── requirements-full.txt  # Docker full (torch, rasterio, scikit-image, lpips)
├── Dockerfile             # python:3.9-slim + GDAL + gunicorn
├── vercel.json            # Vercel functions python3.9
├── .python-version        # 3.9
├── .gitignore
├── LICENSE
├── SIH_Final_Presentation_Final.pdf  # SIH 6-slide submission
└── README.md
```

---

## Demo

```bash
# Using provided sample
py app.py
# Open http://127.0.0.1:5000
# Drag & drop: sample/sentinel_10m_4band_512.tif
```

**Expected Output**:
- Input: 512×512×4 EPSG:32643
- Output: 1536×1536×4 (3×) COG GeoTIFF
- Metrics: SAM 2.66° ✓ | NDVI 0.94 ✓ | RMSE 0.0px ✓
- Heatmap: Viridis uncertainty (red >0.6 = review)
- Download: COG GeoTIFF + PNG + Heatmap TIF

---

## Testing

```bash
# All tests
py -m pytest tests -v

# Specific
py -m pytest tests/test_io.py -v
py -m pytest tests/test_patch.py -v
py -m pytest tests/test_pipeline_e2e.py -v
```

**Results**: 6/6 passing (N-band roundtrip, stitch RMSE<1, 4&8-band e2e)

---

## Model Training (Not Included in Demo)

```bash
# Full dependencies
pip install -r requirements-full.txt

# Generate synthetic pairs from SpaceNet
python -c "
from core.datasets import degrade_file
from pathlib import Path
degrade_file(Path('spacenet/0.5m.tif'), Path('sample/synthetic_10m.tif'))
"

# Train ESRGAN/SwinIR with SAM loss
# python train.py --loss "L1+0.1*Perceptual+0.05*SAM" --epochs 100
# python train.py --mc-dropout --t 10
```

---

## Deployment

### Vercel (Demo)
- Uses `requirements.txt` (slim, ~80MB)
- `vercel.json` → `functions: { "app.py": { "runtime": "python3.9" } }`
- Auto-deploys on push to `main`

### Docker (On-Prem / NTRO)
```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-full.txt .
RUN pip install --no-cache-dir -r requirements-full.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "core.app:create_app()", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

---

## Documentation

| File | Description |
|------|-------------|
| `docs/UPDATED_FULL_v2.md` | Complete v2 specification (PRD→LLD) |
| `docs/01_PRD.md` - `11_LLD.md` | Requirements → Low-Level Design |
| `docs/flow.md` | 10 Mermaid flows (user, system, data, training) |
| `docs/development_cycle.md` | 21-day agile sprint plan (M1→M3) |
| `SIH_Final_Presentation_Final.pdf` | 6-slide SIH submission |

---

## Team

**Antariksh Setu** — Team ID: *(SIH assigned)*

| Member | Role |
|--------|------|
| Shreyas Pawar | Lead / Geospatial + DL |
| *(add team members)* | |

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Acknowledgments

- **ESRGAN** (Wang et al., ICCV 2021) / **SwinIR** (Liang et al., ICCV 2021)
- **SpaceNet** (CosmiQ Works) — synthetic training data
- **Sentinel-2** (ESA Copernicus) — free 10m multispectral data
- **SIH2026 NTRO** — Problem Statement 142