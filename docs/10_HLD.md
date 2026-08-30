# HLD — High-Level Design
## SIH26142 Sentinel-SRM Overall System Architecture

### 1. Purpose
Overall system architecture, external view for evaluators and NTRO deployment.

### 2. System Context Diagram

```
                ┌─────────────────────┐
                │  Copernicus / GEE   │
                │  Sentinel-2 L2A 10m │
                └─────────┬───────────┘
                          │ 10m 4-band GeoTIFF
                          v
┌──────────┐    ┌──────────────────────┐    ┌──────────────┐    ┌─────────┐
│  Analyst │───▶│  Sentinel-SRM Web    │───▶│  QGIS/ArcGIS │───▶│  NTRO   │
│  Browser │◀───│  Service (Flask)     │    │  COG Viewer  │    │ Decision│
└──────────┘    └──────────────────────┘    └──────────────┘    └─────────┘
                    │           │
                    │           └─▶ metrics/log
                    └─▶ weights/ (ESRGAN/SwinIR)
```

### 3. High-Level Components

| Component | Responsibility | Tech |
|---|---|---|
| **Web UI** | Upload, 4-layer viewer, download | Vanilla JS + Leaflet + GeoTIFF.js, glassmorphism `Kepler-404/README.md:43` |
| **API Gateway** | `POST /api/infer`, `GET /api/download`, CORS, validation | Flask `kepler/app.py` |
| **Pipeline Orchestrator** | Single entry `Pipeline.run()` | `kepler/pipeline.py:42` |
| **Geospatial I/O** | CRS/transform preserve, N-band read/write | Rasterio/tifffile + Affine |
| **ML Engine** | N-ch SR + uncertainty | PyTorch ESRGAN/SwinIR on GPU/CPU |
| **Tiling Service** | Split/stitch GB scenes | `kepler/patch.py` |
| **Metrics Service** | PSNR/SSIM/SAM/ERGAS/NDVI | `kepler/metrics.py` → scikit-image |
| **Storage** | Ephemeral 24h | `uploads/`, `static/results/` |
| **Dataset Builder** | Offline synthetic pairs | `kepler/datasets.py` + SpaceNet |

### 4. Deployment Architecture

```
[Browser] ──HTTP──> [Flask Gunicorn :5000 Docker]
                        │
                        ├─ /tmp/kepler/uploads (emptyDir)
                        ├─ /tmp/kepler/results (emptyDir) 24h
                        ├─ /app/weights/*.pth (readOnly)
                        └─ GPU optional (nvidia-docker)
[Vercel Edge] for demo mirror (data URI avoids /tmp cross-instance [kepler/pipeline.py:190])
[On-Prem NTRO] same image, air-gapped, no Vercel
```

### 5. External Interfaces

| Interface | Protocol | Format | Spec |
|---|---|---|---|
| `POST /api/infer` | HTTP multipart | GeoTIFF | `Kepler-404/README.md:167` + heatmap extension |
| `GET /api/download/<f>` | HTTP | Binary | `Content-Disposition: attachment` |
| COG output | File | GeoTIFF tags 33550/33922/34735 | `kepler/io.py:104-142` |
| SIH Portal | PDF upload | 6 slides | `SIH2024_IDEA_Presentation_Format.pptx:Slide7` |

### 6. Data Flow (High Level)

```
Input 10m N×H×W ──normalize──> Tiled 256 ──SR 3×──> Tiled 768 ──stitch+blend──> SR N×H'×W' + Heatmap ──metrics──> JSON+COG
```

### 7. Non-Functional (HLD)

* **Stateless:** No session, job_id UUID hex (`kepler/pipeline.py:45`).
* **Scalability:** Horizontal replicas; tiling keeps per-job RAM <8GB.
* **Reliability:** Wrap exc → 500, log with short_id 8 chars (`kepler/pipeline.py:48`).
* **Security:** 50MB limit, extension check, no exec.

### 8. Technology Roadmap

* HLD v1: 4-band MVP 3× (SIH).
* HLD v2: 13-band + STAC catalog + Bhuvan.
* HLD v3: Multi-temporal fusion + diffusion SR.

### 9. Diagram Prompt (for PPT Slide 3 Right Box)

*As PRD Slide 3 prompt — generate HLD block diagram with 3 tiers (Ingest/Tile, ML Core N-ch, Export/Metrics) using colors #F7FBFF, #FFF2CC, #EDEBF8.*

