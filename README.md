# Resolvance — SIH26142 NTRO Sentinel-SRM

**10m Sentinel-2 → 3.3m super-resolution** with spectral truth (SAM) + per-pixel uncertainty. Fresh build per `docs/UPDATED_FULL_v2.md` (not a fork).

## Quickstart
```
pip install -r requirements.txt
py app.py
# http://127.0.0.1:5000
```

## API
`POST /api/infer` multipart `file` (.tif/.tiff/.png/.jpg ≤50MB) → `{success,images{input,sr,heatmap: data URI},download,download_tif,download_heatmap,meta{job_id,input_size,output_size,crs,elapsed,file_type},metrics{psnr,ssim,sam_mean_deg,ergas,ndvi_delta,ndvi_corr,rmse_px}}`
`GET /api/download/<file>` `GET /api/health`

## Pipeline
Ingest N-band `C×H×W` → per-band 2-98% clip → TileManager 256+16 Gaussian → SR 3× → stitch `Affine.scale` → MC-Dropout heatmap viridis → COG planar → data URI

## Tests
`py -m pytest -v` — 6 tests: N-band roundtrip, stitch RMSE<1, 4 & 8-band e2e

## Deploy
`docker build -t resolvance .` + `gunicorn core.app:create_app()` ; `vercel.json` for demo

## Project Structure
```
Resolvance/
├── app.py                 # Flask launcher
├── core/                  # Core pipeline package
│   ├── app.py            # Flask factory
│   ├── config.py         # Settings
│   ├── io.py             # N-band GeoTIFF I/O + CRS
│   ├── patch.py          # TileManager 256+16
│   ├── transforms.py     # SRModel + uncertainty
│   ├── metrics.py        # PSNR/SSIM/SAM/ERGAS/NDVI
│   ├── datasets.py       # Synthetic degradation
│   ├── pipeline.py       # End-to-end orchestration
│   ├── models.py         # Data classes
│   └── ...
├── api/routes.py         # /api/infer, /api/download
├── frontend/             # Vanilla JS + Leaflet viewer
├── sample/               # Test GeoTIFFs
├── tests/                # pytest suite
├── weights/              # Model checkpoints (gitignored)
├── uploads/              # Temp uploads (gitignored)
├── static/results/       # Output images (gitignored)
├── requirements.txt      # Vercel slim (80MB)
├── requirements-full.txt # Docker full (torch, rasterio)
├── Dockerfile            # python:3.9-slim + GDAL
├── vercel.json           # Vercel functions python3.9
└── SIH_Final_Presentation_Final.pdf  # SIH submission
```

## Demo
Upload `sample/sentinel_10m_4band_512.tif` → `SAM 2.66°` `NDVI 0.94` `RMSE 0.0px` → download COG for QGIS.

## Team
**Antariskh Setu** — SIH26142 NTRO Space Technology