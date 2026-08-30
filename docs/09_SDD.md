# SDD — Software Design Document
## SIH26142 Sentinel-SRM Detailed Software Architecture

### 1. Introduction
Detailed architecture for Sentinel-SRM, companion to TDD/HLD.

### 2. System Overview

* **Type:** Web service + batch ML pipeline.
* **Deployment:** Single container, stateless, 24h ephemeral storage.

### 3. Module Breakdown

```
Kepler-404/
├── app.py (thin launcher, unchanged)
├── kepler/
│   ├── app.py (create_app, CORS, purge_stale)
│   ├── config.py (Settings dataclass, ensure_dirs, is_geotiff, new: tile/scale/device)
│   ├── exceptions.py (DecodingError, ProcessingError)
│   ├── logging_setup.py (get_logger)
│   ├── io.py (GeoReadResult, read/write, normalize) ← modified N-band
│   ├── transforms.py (super_resolve, uncertainty) ← modified N-ch
│   ├── patch.py (TileManager, blend) ← new
│   ├── metrics.py (sam, psnr, ssim, ergas, ndvi) ← new
│   ├── datasets.py (synthetic degradation) ← new
│   ├── models.py (FileType, ImageSet, InferenceResult, JobMeta) ← extended heatmap
│   ├── pipeline.py (Pipeline, _process_geotiff/_image, _shared_stages) ← tiling
│   └── routes.py (api infer/download) ← +heatmap field
├── templates/index.html
├── static/{css,js}
├── weights/{real_esrgan_4ch.pth, swinir_4ch.pth}
├── uploads/ results/ (ephemeral)
└── tests/
```

### 4. Data Model

#### 4.1 GeoReadResult (modified)

```python
@dataclass
class GeoReadResult:
    band: np.ndarray  # N×H×W or H×W×C, float32/DN preserved → uint8 via normalize per-band
    transform: Affine
    crs: object  # "EPSG:32643"
    width: int; height: int; count: int  # new: band count
```

#### 4.2 InferenceResult (extended)

```python
@dataclass
class InferenceResult:
    job_id: str
    images: ImageSet  # input, sr, heatmap (renamed from colorized)
    download_png: str; download_tif: str|None
    meta: JobMeta
    metrics: dict|None  # {psnr, ssim, sam_mean, ergas, ndvi_delta}
```

#### 4.3 JobMeta

```
job_id, input_size "H×W×C", output_size "H'×W'×C", crs, elapsed, file_type (GEOTIFF/IMAGE)
```

### 5. Component Interaction (Sequence)

```
Client -> Routes /api/infer: multipart file
Routes -> Pipeline.run(path, job_id): is_geo?
Pipeline -> IO.read_geotiff: N×H×W + transform
Pipeline -> IO.normalize_to_uint8 per-band
Pipeline -> Patch.tile(): list[Tile(coords, data, weight)]
Pipeline -> Transforms.super_resolve() per tile (batched if GPU)
Pipeline -> Patch.stitch(): H'×W'×C + new_transform
Pipeline -> Transforms.uncertainty() -> heatmap H'×W'
Pipeline -> Metrics.compute() if reference
Pipeline -> IO.write_geotiff() + write_png() ×3 + heatmap PNG
Pipeline -> Result.to_dict() -> JSON response with data URIs
```

### 6. Algorithm Design

#### 6.1 Super Resolution

* **Model:** Real-ESRGAN Generator (RRDB) with `in_nc=N, out_nc=N, nf=64, nb=23`, upscale 3× via `×3 PixelShuffle` or 2×+1.5 resize.
* **Adaptation:** First conv weight `conv_first.weight: [64,N,3,3]` — initRGB copied, NIR channel init = mean(R,G,B).
* **Forward:** `T = normalize(tile/255) → model(T) → clip 0-1 → uint8`.

#### 6.2 Loss (Training)

```
Loss = L1 + 0.1·Perceptual(VGG19) + 0.05·SAM
SAM = mean(arccos( dot(pred,gt) / (|pred||gt|) ))
Perceptual = L1(VGG features)
```
Physics bonus: optional NDVI consistency `|NDVI_sr - NDVI_gt|`.

#### 6.3 Tiling & Blending

* Tile 256, overlap 16, stride 240. Weight map 2D Gaussian σ=overlap/2.
* Accumulator `acc[C,H',W']`, weight_sum `[H',W']`. Stitch `acc / weight_sum`.

#### 6.4 Uncertainty

* MC-Dropout: enable dropout in tail (p=0.2), T=10 passes → `mean, std`. Heatmap `std_norm = (std - min)/(max-min)` viridis colormap.
* Threshold 0.6 std → red overlay warning.

#### 6.5 Metrics

* PSNR `10·log10(255²/MSE)`, SSIM `skimage`, LPIPS `lpips.VGG`, SAM per pixel mean, ERGAS `100·(h/l)·sqrt(mean((RMSE/B)²))`, NDVI `(NIR-Red)/(NIR+Red)` delta.

### 7. Database / Storage

* No DB — filesystem `uploads/` + `static/results/` purged 24h. Future: SQLite job log if needed.

### 8. Error Handling

| Exception | HTTP | Message |
|---|---|---|
| `DecodingError` | 400 | "Could not read GeoTIFF {name}: {exc}" |
| `ProcessingError` (OOM) | 500 | "Pipeline failure: ..." with log id |
| Channel mismatch | 400 | "Model expects 4ch, got 8ch — use ... " |

### 9. Configuration

```python
@dataclass
class Settings:
    host="0.0.0.0"; port=5000; debug=True
    upload_dir="uploads"; results_dir="static/results"
    max_bytes=50*1024*1024; mock_delay_seconds=0.0
    tile_size=256; overlap=16; scale=3; device="cuda:0" if torch.cuda.is_available() else "cpu"
    model_name="real_esrgan_4ch"; dropout_p=0.2; mc_passes=10
```

### 10. Testing & QA

* `tests/test_io.py`: N-band roundtrip CRS+transform preservation.
* `tests/test_patch.py`: Seam RMSE <1 DN on synthetic checkerboard.
* `tests/test_transforms.py`: N=4,8 shape correct, uncertainty range 0-1.
* `tests/test_pipeline_e2e.py`: full run on `sample.tiff` (1-band) + synthetic 4-band, JSON contract.

