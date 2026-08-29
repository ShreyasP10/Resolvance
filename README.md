# Resolvance — SIH26142 NTRO Sentinel-SRM

**10m Sentinel-2 → 3.3m super-resolution** with spectral truth (SAM) + per-pixel uncertainty. Fresh build per `docs/UPDATED_FULL_v2.md` (not a fork).

**Stack:** Flask + PyTorch ESRGAN/SwinIR (stub bicubic, drop-in), Rasterio/GDAL/Affine/tifffile, Vanilla JS + Leaflet

## Quickstart
```
pip install -r requirements.txt
py app.py
# http://127.0.0.1:5000
```

## API
`POST /api/infer` multipart `file` (.tif/.tiff/.png/.jpg ≤50MB) → `{success,images{input,sr,heatmap: data URI},download,download_tif,download_heatmap,meta{job_id,input_size,output_size,crs,elapsed,file_type},metrics{psnr,ssim,sam_mean_deg,ergas,ndvi_delta}}`
`GET /api/download/<file>` `GET /api/health`

## Pipeline
Ingest N-band `C×H×W` → per-band 2-98% clip → TileManager 256+16 Gaussian → SR 3× → stitch `Affine.scale` → MC-Dropout heatmap viridis → COG planar → data URI

## Tests
`py -m pytest -v` — 6 tests: N-band roundtrip, stitch RMSE<1, 4 & 8-band e2e

## Deploy
`docker build -t resolvance .` + `gunicorn core.app:create_app()` ; `vercel.json` for demo

## Project Structure
`core/{config,io,patch,transforms,metrics,datasets,pipeline,app}` `api/routes.py` `frontend/{templates,static}` `weights/` `tests/`
# Resolvance
