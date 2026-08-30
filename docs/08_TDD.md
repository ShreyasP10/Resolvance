# TDD — Technical Design Document
## SIH26142 Sentinel-SRM Implementation Plan

### 1. Overview
Explains **how** the system will be implemented as fork of Kepler-404 to meet FRD/SRS.

### 2. System Context

* **External:** Copernicus Dataspace / GEE (input), SpaceNet (training), QGIS/ArcGIS (consumer), SIH portal (PDF).
* **Internal:** Flask app (`kepler/app.py`), Pipeline (`kepler/pipeline.py`), Transforms (`kepler/transforms.py`), IO (`kepler/io.py`).

### 3. Architecture (Technical)

```
User Browser (Vanilla JS+Leaflet)
   | POST /api/infer (multipart)
   v
Flask create_app() [kepler/app.py] ── Settings(host/port/debug)
   | Pipeline.run(path, job_id) [kepler/pipeline.py:42]
   ├─ read_geotiff() / read_image() [kepler/io.py:55-82]
   ├─ normalize_to_uint8() per-band [kepler/io.py:85-96]
   ├─ TileManager (new) → 256×256+16 tiles, weights
   ├─ super_resolve() N-ch ESRGAN/SwinIR [kepler/transforms.py:34] × tiles → stitch
   ├─ uncertainty() MC-Dropout (new)
   ├─ metrics() SAM/PSNR (new)
   ├─ write_geotiff() COG [kepler/io.py:129-142] + write_png()
   └─ return InferenceResult → data URI [kepler/pipeline.py:190-193]
```

### 4. Component Design

| Component | Responsibility | Key File | New/Modified |
|---|---|---|---|
| `Config` | Env, dirs, is_geotiff() | `kepler/config.py` | Add `tile_size=256, overlap=16, scale=3, device=cuda/cpu` |
| `IO` | Multi-band read/write, CRS extract | `kepler/io.py` | Modify: keep all bands, not `raw[:,:,0]` |
| `Transforms` | SR + uncertainty | `kepler/transforms.py` | Modify: N-channel + factory |
| `Patch` | Tiling/stitching | `kepler/patch.py` *(new)* | New |
| `Metrics` | PSNR/SSIM/SAM/ERGAS/NDVI | `kepler/metrics.py` *(new)* | New |
| `Dataset` | Synthetic pair gen | `kepler/datasets.py` *(new)* | New |
| `Pipeline` | Orchestration | `kepler/pipeline.py` | Modify: branch tiles |
| `Routes` | API | `kepler/routes.py` | Modify: add heatmap to JSON, extend meta |

### 5. Data Flow

1. **Ingest:** `TiffFile` → `GeoReadResult{band:N×H×W, transform, crs, w,h}` (extend from 2D to N×H×W).
2. **Normalize:** per-band percentile clip → uint8.
3. **Tile:** `unfold` with overlap, store coords, Gaussian weight map `exp(-d²/2σ²)`.
4. **SR:** Each tile `1×N×256×256 → 1×N×768×768` via model; MC passes T=10 → mean+std.
5. **Stitch:** Accumulate weighted sum / weight sum, compute new affine `transform * Affine.scale(w/new_w, h/new_h)`.
6. **Export:** `tifffile.imwrite` planar `C×H×W`, tags 33550/33922/34735.

### 6. Technology Choices

* **Rasterio vs tifffile:** Keep tifffile for lightweight read but add Rasterio windowed read for >50MB fallback (GDAL handles large COG better).
* **Model:** Real-ESRGAN pretrained on RGB → replace first conv `3→64` with `N→64` (copy RGB weights, init NIR avg of RGB). SwinIR alternative via `timm`.
* **Uncertainty:** Option A MC-Dropout (dropout p=0.1 at SR tail, T=10, std) ; Option B 3-model ensemble. Choose A for SIH (single weights).

### 7. Deployment Design

* **Dev:** `python app.py` debug True auto-reload (`Kepler-404/README.md:161`).
* **Prod:** `gunicorn kepler.app:create_app()` + Docker `python:3.9-slim` + GDAL apt, `vercel.json` for demo, on-prem systemd for NTRO.
* **CI:** `pytest` (`Kepler-404/.pytest_cache`) + `tests/test_io_roundtrip`, `test_patch_stitch`.

### 8. Migration from TIR

* Flag `MODE=tir|sentinel` in `Settings`; TIR uses single-channel Inferno, Sentinel uses N-channel + SAM.
* Preserve API shape: `images {input,sr,heatmap}` (rename `colorized→heatmap` for sentinel, backwards compat via alias).

### 9. Risks & Mitigations (Technical)

* OOM on 5000×5000×4 → tiled + stream write via `tifffile` memmap.
* Channel mismatch → factory checks `in_ch` from input vs `model.in_ch` → error 400 with hint.
* Hallucination → uncertainty threshold >0.6 flagged red in viewer.

### 10. Testing Strategy

* Unit: `read_geotiff` roundtrip CRS, `super_resolve` shape, `patch` seam RMSE.
* Integration: `Pipeline.run` on `sample.tiff` + synthetic 4-band, check JSON contract.
* Validation: Holdout synthetic 100 tiles → metrics table target §PRD-8.

