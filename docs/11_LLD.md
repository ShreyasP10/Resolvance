# LLD — Low-Level Design
## SIH26142 Sentinel-SRM Detailed Classes, APIs, DB Schemas, Algorithms

### 1. Class Diagram (Key Classes)

```
Settings ──1──> Pipeline ──uses──> TileManager, SRModel, Metrics, IO
Pipeline ──creates──> InferenceResult ──contains──> ImageSet, JobMeta
IO: GeoReadResult, read_geotiff, write_geotiff, normalize_to_uint8
Transforms: super_resolve(), uncertainty()
```

### 2. Class Details

#### 2.1 `Settings` (`kepler/config.py`)

```python
@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = True
    upload_dir: Path = Path("uploads")
    results_dir: Path = Path("static/results")
    max_bytes: int = 50*1024*1024
    mock_delay_seconds: float = 0.0
    tile_size: int = 256
    overlap: int = 16
    scale: int = 3  # 10m→3.33m
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    model_name: str = "real_esrgan_4ch"
    dropout_p: float = 0.2
    mc_passes: int = 10
    def ensure_dirs(self): ...
    def is_geotiff(self, name: str) -> bool: return name.lower().endswith((".tif",".tiff"))
```

#### 2.2 `GeoReadResult` (`kepler/io.py`)

* See SDD §4.1 — add `count:int` and change `band: np.ndarray` shape `C×H×W` (if tifffile planar) or `H×W×C` normalized to `C×H×W` internally.

#### 2.3 `TileManager` (`kepler/patch.py` new)

```python
@dataclass
class Tile:
    data: np.ndarray  # C×256×256 uint8
    coords: tuple[int,int]  # (x,y) in input
    weight: np.ndarray  # 256×256 float Gaussian

class TileManager:
    def __init__(self, tile_size=256, overlap=16): ...
    def tile(self, img: np.ndarray) -> list[Tile]:  # img C×H×W
        # stride = tile_size-overlap, create weight map exp(-d²/(2*(overlap/2)²))
    def stitch(self, tiles: list[np.ndarray], out_h, out_w, weight_map) -> np.ndarray:
        # acc + weight_sum, divide, return C×H'×W'
```

#### 2.4 `SRModel` (`kepler/transforms.py` modified)

```python
class SRModel:
    def __init__(self, in_ch: int, out_ch: int, scale=3, arch="real_esrgan"):
        self.model = RRDBNet(in_nc=in_ch, out_nc=out_ch, nf=64, nb=23, scale=scale)
        # load state_dict, replace first conv if channel mismatch: init new channel = mean old
        self.model.eval().to(device)
    def __call__(self, x: torch.Tensor) -> torch.Tensor:  # x: 1×C×H×W float 0-1
        with torch.no_grad():
            return self.model(x).clamp(0,1)

# functional wrapper for Pipeline backward compat
def super_resolve(img: np.ndarray, model: SRModel) -> np.ndarray: ...
def uncertainty(img: np.ndarray, model: SRModel, T=10) -> np.ndarray:  # H×W std 0-255
```

#### 2.5 `Pipeline` (`kepler/pipeline.py` modifications)

```python
class Pipeline:
    def __init__(self, settings: Settings):
        self.settings=settings; self.settings.ensure_dirs()
        self.sr_model = SRModel(in_ch=4, out_ch=4)  # lazy per first call channel
        self.tile_mgr = TileManager(settings.tile_size, settings.overlap)
    def run(self, input_path: Path, job_id:str|None=None) -> InferenceResult:
        # is_geo branch, now tiling loop:
        # gray = normalize -> tiles = tile_mgr.tile(gray)
        # sr_tiles = [super_resolve(t.data) for t in tiles]
        # sr_gray = tile_mgr.stitch(sr_tiles, new_h, new_w)
        # heatmap = uncertainty(gray)
        # metrics = Metrics.compute(sr_gray, ref) if ref else {}
        # write_png/write_geotiff (N-band planar)
```

### 3. API Contracts (Low Level)

#### 3.1 `POST /api/infer`

**Request:** `Content-Type: multipart/form-data; boundary=...`
```
file: <binary> name="sentinel_10m.tif"
```
Validation: `if file.content_length > settings.max_bytes: 413` ; `if not is_geotiff and not image: 415`.

**Response 200:**
```json
{
  "success": true,
  "images": {
    "input": "data:image/png;base64,iVBOR...",
    "sr": "data:image/png;base64,iVBOR...",
    "heatmap": "data:image/png;base64,iVBOR..."
  },
  "download": "/api/download/abc123_colorized.png",
  "download_tif": "/api/download/abc123_sr.tif",
  "download_heatmap": "/api/download/abc123_heatmap.tif",
  "meta": {
    "job_id": "abc123...",
    "input_size": "1024×1024×4",
    "output_size": "3072×3072×4",
    "crs": "EPSG:32643",
    "elapsed": "12.3",
    "file_type": "GeoTIFF"
  },
  "metrics": {
    "psnr": 29.2, "ssim": 0.84, "sam_mean_deg": 2.1, "ergas": 2.0, "ndvi_delta": 0.01
  }
}
```
**Error 400:**
```json
{"success": false, "error": "Invalid file format. Please upload a .tif, .tiff, .png, .jpg, or .jpeg file."}
```

#### 3.2 `GET /api/download/<filename>`

* Header `Content-Disposition: attachment; filename="<filename>"`
* Lookup under `results_dir`, 404 if missing/purged.

### 4. DB Schemas

* **No DB for MVP.** Filesystem only. Optional future `jobs` SQLite:
```sql
CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  input_name TEXT,
  crs TEXT,
  input_size TEXT,
  output_size TEXT,
  elapsed REAL,
  psnr REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Algorithm Pseudocode

#### 5.1 Synthetic Degradation (`kepler/datasets.py`)

```python
def degrade(hr_path: Path, out_lr: Path, scale=3):
    hr = rasterio.open(hr_path).read()  # C×H×W 0.5m
    # Gaussian PSF sigma ~0.8, then downsample via INTER_AREA
    lr = cv2.GaussianBlur(hr.transpose(1,2,0), (7,7), 0.8)
    lr = cv2.resize(lr, (W//scale, H//scale), interpolation=cv2.INTER_AREA)
    # Add Sentinel-2-like noise 1% + clip
    lr = np.clip(lr + np.random.randn(*lr.shape)*2, 0, 255).astype(np.uint8)
    write_geotiff(out_lr, lr, transform_scaled, crs)
```

#### 5.2 Per-Band Normalize (`kepler/io.py`)

```python
def normalize_to_uint8_per_band(arr: np.ndarray) -> np.ndarray:
    # arr C×H×W float DN
    out = np.empty((C,H,W), dtype=np.uint8)
    for c in range(C):
        band = arr[c]
        valid = band[np.isfinite(band)]
        low, high = np.percentile(valid, [2,98])
        if high<=low: low,high = valid.min(), valid.max()
        out[c] = np.clip((band-low)/(high-low),0,1)*255
    return out
```

#### 5.3 SAM Metric (`kepler/metrics.py`)

```python
def sam(pred: np.ndarray, gt: np.ndarray) -> float:
    # pred,gt C×H×W uint8 -> float 0-1
    pred_f = pred.astype(float)/255; gt_f = gt.astype(float)/255
    dot = np.sum(pred_f*gt_f, axis=0)
    norm = np.linalg.norm(pred_f,axis=0)*np.linalg.norm(gt_f,axis=0)
    angle = np.arccos(np.clip(dot/(norm+1e-8), -1,1)) * 180/np.pi
    return float(np.mean(angle))
```

### 6. File Structure & Key Paths

* `app.py:9` launcher → `kepler/app.py:create_app` → `kepler/routes.py` → `kepler/pipeline.py:run`.
* `static/results/<job_id>_input.png` etc. data URI avoids Vercel (`kepler/pipeline.py:190-193`).
* `weights/real_esrgan_4ch.pth` lazy load on first `super_resolve`.

### 7. Sequence: Tiled SR (LLD)

```
loop over tiles:
  tile_tensor = torch.from_numpy(tile.data).float()/255 → 1×C×256×256 .to(device)
  sr_tile = model(tile_tensor) → 1×C×768×768
  sr_tile_uint8 = (sr_tile.squeeze().cpu().numpy()*255).astype(uint8)
  place into acc at coords*scale with weight
```

### 8. Testing (LLD)

* `tests/test_io_ndim.py`: Assert 4-band read/write roundtrip CRS equal, transform scaled correctly `new_transform = old * Affine.scale(w/new_w, h/new_h)`.
* `tests/test_patch.py`: Create checkerboard 512×512, tile/stitch, assert RMSE <1.
* `tests/test_sam.py`: Same image SAM ≈0°, random image SAM >10°.
```

