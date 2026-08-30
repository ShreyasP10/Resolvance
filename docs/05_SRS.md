# SRS — Software Requirements Specification (IEEE 830)
## SIH26142 Sentinel-SRM v1.0

### 1. Introduction
**Purpose:** Specify software for NTRO SRM to be built from Kepler-404 fork. **Scope:** Web service + ML pipeline + viewer. **Definitions:** SR=Super-Resolution, SAM=Spectral Angle Mapper, COG=Cloud Optimized GeoTIFF, TIR=Thermal Infrared (legacy).

### 2. Overall Description
* **Product Perspective:** Fork of `Kepler-404/app.py` thin launcher (`app.py:9-15`) + `kepler/` package. Extends TIR 200→100m single-channel to Sentinel-2 10→<4m N-channel.
* **User Classes:** Analyst, Evaluator, Developer (as FRD §2).
* **Constraints:** Plan mode → build mode transition, max 50MB upload (`Kepler-404/README.md:281`), Python 3.9+, Flask debug auto-reload (`README.md:161`).

### 3. Specific Requirements

#### 3.1 Functional (Ref FRD)

* **F-SRS-01:** System shall accept `multipart/form-data` `file` `.tif/.tiff/.png/.jpg` (max 50MB) at `POST /api/infer` and return JSON with `success, images{input,sr,heatmap}, download, download_tif, meta{job_id,input_size,output_size,crs,elapsed,file_type}` extending `Kepler-404/README.md:178-197` to include `heatmap`.
* **F-SRS-02:** System shall preserve CRS/transform: read via TIFF tags 33550/33922/34264/34735 (`kepler/io.py:24-52`), write via `33550,33922,34735` (`kepler/io.py:104-142`), scaling via `Affine.scale` (`kepler/pipeline.py:87-89`).
* **F-SRS-03:** System shall auto-detect band count (1,3,4,8) and route through N-channel model without config change.

#### 3.2 External Interfaces

* **API:** `POST /api/infer`, `GET /api/download/<filename>` (`Kepler-404/README.md:210-218`) with CORS (`flask-cors`).
* **UI:** `templates/index.html` + `static/css|js` — drag-drop, progress via actual response, 4-way slider, toast.

#### 3.3 Performance

| Metric | Requirement | Rationale |
|---|---|---|
| Latency (1024×1024×4 CPU) | ≤30s end-to-end | Demo usability |
| Throughput | 1 concurrent job, queue second | Prevent OOM |
| Availability | Purge 24h, stateless pipeline | `Kepler-404/README.md:293` |

#### 3.4 Design Constraints

* Language Python 3.9+, Framework Flask, Libs Rasterio/GDAL optional but preferred for CRS robustness over tifffile-only.
* Model weights under `weights/` dir, lazy load via config.

#### 3.5 Software System Attributes

* **Reliability:** Wrap unexpected exc → `ProcessingError` 500 (`kepler/pipeline.py:61-63`).
* **Usability:** Keyboard navigable, ARIA, `prefers-reduced-motion` (`Kepler-404/README.md:50`).
* **Security:** No persistence of user data beyond 24h, data URI not file path leak.
* **Portability:** Docker + `vercel.json` (`Kepler-404/vercel.json`) for cloud and on-prem.

#### 3.6 Validation Metrics (SRS-Level)

* PSNR/SSIM/LPIPS per `scikit-image`/`lpips`, SAM `arccos`, ERGAS, NDVI ` (NIR-Red)/(NIR+Red)` delta.
* Geospatial RMSE <0.3px via affine tiepoint check.

### 4. Appendix: Verbal Traceability

* `prompt.txt:47-52` Expected Solution → F-SRS-01/02/03
* `prompt.txt:62-66` PSNR/SSIM/SAM + NDVI → §3.6
