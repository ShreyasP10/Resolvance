# TRD — Technical Requirements Document
## SIH26142 Sentinel-SRM

### 1. Purpose
Defines technical constraints and requirements the implementation must satisfy. Extends `prompt.txt:16-27` and `Kepler-404` audit.

### 2. Technical Constraints

| ID | Constraint | Value / Rule | Source |
|---|---|---|---|
| TR-C01 | Max upload | 50 MB per file, else 400 | `Kepler-404/README.md:281` |
| TR-C02 | Accepted formats | `.tif/.tiff` (GeoTIFF), `.png/.jpg` (image, no CRS) | `Kepler-404/README.md:282` |
| TR-C03 | Upscale factor | 3× (10m→3.33m) meets `<4m` spec | `prompt.txt:47` |
| TR-C04 | File retention | 24h auto-purge on server start | `Kepler-404/README.md:284` |
| TR-C05 | Port | 5000 (configurable via `Settings.host/port`) | `kepler/config.py` |
| TR-C06 | Python | 3.9+ (`Kepler-404/README.md:120`) | — |
| TR-C07 | Tiling | 256×256 +16 overlap for GB scenes | `prompt.txt:115` |

### 3. Technology Stack

| Component | Choice | Justification |
|---|---|---|
| Backend | Flask + Flask-CORS (`requirements.txt:1-2`) | Kepler parity, SIH demo simple |
| Geospatial | Rasterio + GDAL + Affine + tifffile | Rasterio windowed read > tifffile for large files |
| Image | opencv-headless, numpy, pillow | Existing + fast |
| ML | PyTorch + ESRGAN/SwinIR (Real-ESRGAN weights) + scikit-image + lpips | `prompt.txt:22` PyTorch + `Kepler-404/README.md:85` target |
| Frontend | Vanilla JS + Leaflet + GeoTIFF.js + CSS custom properties | Glassmorphism `Kepler-404/README.md:43` |
| Infra | Docker, Vercel (`vercel.json`), Gunicorn prod | Cloud + on-prem |

### 4. Hardware Requirements

* **Training:** CUDA GPU 16GB (A100/T4) via Colab Pro/AWS (`prompt.txt:18` High-end GPUs mandatory). 40 GPU-hours for 10k tiles, mixed precision, gradient accumulation.
* **Inference:** CPU 4-core 8GB RAM min, GPU optional; tiled inference ensures <8GB peak for 1GB input.
* **Storage:** 100GB for dataset + weights, SSD for tile I/O.

### 5. Software Dependencies

```
flask, flask-cors, opencv-python-headless, numpy, tifffile, affine
+ rasterio, geopandas, pyproj, scikit-image, lpips, torch, torchvision, albumentations
+ pytest, pillow (dev)
```

### 6. Data Requirements

* **Primary:** Sentinel-2 L2A via Copernicus Dataspace/GEE (10m B02/B03/B04/B08).
* **Synthetic Pair Gen:** SpaceNet 0.5m → `cv2.GaussianBlur` + `INTER_AREA` downsample 6× to 3m + simulate Sentinel-2 PSF to 10m (approx). JSON manifest with CRS.
* **Validation Ref:** PlanetScope 3m or Cartosat 1m (where licensed) for holdout.

### 7. Performance Requirements

* Tile SR <200ms on GPU, <2s on CPU per 256 tile.
* End-to-end 1024×1024×4: GPU ≤10s, CPU ≤30s.
* Seam RMSE <1 DN.

### 8. Security & Compliance

* No auth for SIH demo; CORS enabled globally (`kepler/app.py`).
* Input validation: `is_geotiff()` by extension + TIFF magic, `DecodingError` → 400.
* No user data persistence beyond 24h; data URI avoids path traversal.

### 9. Scalability & Reliability

* Stateless `Pipeline` class (`kepler/pipeline.py:32-35`) — horizontal scale via container replicas, shared `/tmp` not needed (data URI).
* Purge on start, not cron — SIH demo safe.

### 10. Integration Points

* QGIS/ArcGIS via COG; Bhuvan STAC future.
* SIH upload portal → PDF export (6 slides) `SIH2024_IDEA_Presentation_Format.pptx:Slide7` rules.

### 11. Open Technical Decisions

* 4-band vs 13-band MVP defaults to 4-band; 1×1 conv makes future trivial.
* SwinIR vs Real-ESRGAN — both supported via factory.
