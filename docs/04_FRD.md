# FRD — Functional Requirements Document
## SIH26142 Sentinel-SRM

### 1. Overview
Defines what the system **must do** (functions), derived from PRD §7 and `prompt.txt:45-53`.

### 2. Actors

* Analyst (upload, view, download), Evaluator (validate), System (auto-purge 24h `Kepler-404/README.md:284`).

### 3. Functional Requirements

| ID | Function | Input | Output | Rule |
|---|---|---|---|---|
| FR-01 | Ingest GeoTIFF | `.tif/.tiff` 1/3/4/8-band ≤50MB | N×H×W float32 + CRS/affine + job_id | Preserve CRS via `kepler/io.py:24-34` Affine+EPSG tags |
| FR-02 | Validate file | File header | Accept/reject 400/415 JSON | Reject non-GeoTIFF/image with clean error (`Kepler-404/README.md:204`) |
| FR-03 | Normalize | N×H×W raw DN | N×H×W uint8 0-255 | Per-band 2-98 percentile clip (`kepler/io.py:85-96`) |
| FR-04 | Tile image | H×W×C, tile 256+16 overlap | List of tiles + coords | Gaussian blend weights for seam removal |
| FR-05 | Super-resolve tile | 256×256×C | 768×768×C (3×) | `super_resolve` N-channel ESRGAN/SwinIR (`prompt.txt:88`) |
| FR-06 | Uncertainty estimate | Tile + T stochastic passes | H×W heatmap (0-1) | MC-Dropout T=10 std or 3-model ensemble variance |
| FR-07 | Stitch | Tiles + weights + new affine | H'×W'×C SR array + new affine `Affine.scale(w/new_w,...)` (`kepler/pipeline.py:87-89`) | CRS unchanged, pixel size ÷3 |
| FR-08 | Compute metrics | SR vs reference (if paired) or vs input stats | PSNR, SSIM, LPIPS, SAM, ERGAS, NDVI-delta JSON | SAM via `arccos(dot)` per pixel |
| FR-09 | Export | SR array + transform/CRS | COG GeoTIFF + PNG (`kepler/io.py:129-142`) + data URI | Planar `rgb.transpose(2,0,1)` → tifffile with ModelPixelScale/ Tiepoint / GeoKeyDirectory |
| FR-10 | Serve results | job_id | `/{input,sr,colorized}` data URI + `/api/download/<file>` + meta (sizes, CRS, elapsed) (`Kepler-404/README.md:178-197`) | Data URI avoids Vercel /tmp cross-instance (`kepler/pipeline.py:190-193`) |
| FR-11 | Viewer interaction | Upload drag-drop/sample | 4-layer comparison slider (input/SR/heatmap/diff) + stats + download buttons | Mirror `Kepler-404` 3-way but add 4th heatmap |
| FR-12 | Admin purge | Cron on start | Delete `uploads/`+`results/` >24h | `purge_stale()` (`Kepler-404/README.md:293`) |

### 4. Use Case Flows

**UC-01 Upload → SR**
1. User drops `sentinel_10m.tif` → `POST /api/infer` multipart (`Kepler-404/README.md:167`).
2. Pipeline `run()` → `read_geotiff` → tiles → SR → stitch → metrics → write outputs → return JSON.
3. Frontend renders 4 layers, shows metrics, enables download.

**UC-02 Validation (paired synthetic)**
1. System loads synthetic pair (synthetic_10m, true_0.5m downsampled to 3.3m) → computes FR-08 → displays delta table.

### 5. Business Rules (Functional)

* Must not strip NIR — evaluator NDVI test (`prompt.txt:68`).
* Must auto-detect band count — 8-band on-spot must not crash (`prompt.txt:98`).
* Seam error <1 DN RMS at tile borders.

### 6. Non-Functional (Cross-ref SRS)

* Latency ≤30s CPU for 1024×1024 4-band; throughput 1 job concurrent.
* Error handling: `DecodingError`/`ProcessingError` map to 400/500 (`kepler/pipeline.py:59-63`).

### 7. Traceability

| FR | PRD | Prompt |
|---|---|---|
| FR-05 | PR-03, PR-04 | `prompt.txt:47-52` Expected Solution |
| FR-06 | PR-05 | `prompt.txt:42` Innovation Injection |
| FR-08 | PR-06 | `prompt.txt:64-66` Evaluator Perspective |
