# UPDATED FULL DOCUMENT — SIH26142 NTRO Sentinel Super-Resolution (v2 — New Project, Not a Fork)

**PS:** SIH26142 — Deep Learning Based Super Resolution Mapping from Medium Resolution Satellite Imagery | **Org:** NTRO | **Theme:** Space Technology (Software) | **Category:** Software | **Scale:** 10m Sentinel-2 → <4m (3× → 3.33m)  
**Version:** 2.0 (New Project) | **Date:** 2026-08-29 | **Base:** Fresh build (inspired by Kepler-404 ideas, zero code reuse) | **Source Docs:** `docs/00_INDEX` + `prompt.txt:4-52`

> **Change from v1:** v1 assumed `Kepler-404/` fork (single-channel TIR 200→100m mock `transforms.py:38`). **v2 is a completely new project** — fresh `Sentinel-SRM/` scaffold, no file copy, no Kepler debt (no `raw[:,:,0]` bug `io.py:60`, no Inferno colorization). All code written N-channel-first.

---

## 1. EXECUTIVE SUMMARY

**Problem:** Free Sentinel-2 (10m, 5-day revisit) cannot resolve narrow roads/small buildings/field boundaries/water edges (`prompt.txt:5-7`). Commercial <1m costs $1000s/scene with low revisit. Traditional bicubic is blurry; GANs hallucinate bridges that mislead defence analysts (`prompt.txt:106`).

**Solution:** Fresh Python+PyTorch pipeline that reads N-band (4 default RGB+NIR, dynamic to 8/13) GeoTIFF preserving CRS+affine, tiles 256+16 Gaussian blend (`prompt.txt:115`), runs N-channel ESRGAN/SwinIR 3× with loss `L1+0.1·Perceptual+0.05·SAM` (`prompt.txt:88`), produces per-pixel uncertainty via MC-Dropout T=10, validates PSNR/SSIM/SAM/ERGAS/NDVI, exports COG GeoTIFF + heatmap ready for QGIS (`prompt.txt:47-52`).

**Differentiation:** Synthetic degradation (SpaceNet 0.5m → synthetic 10m) solves paired-data impossibility (`prompt.txt:103`), SAM keeps spectral truth (`prompt.txt:64`), uncertainty is the trust layer — Topaz strips metadata (`prompt.txt:38`), papers hallucinate.

**KPI:** PSNR≥28dB SSIM≥0.80 SAM<3° ERGAS<2.5 NDVI r>0.98; QGIS overlay RMSE<0.3px; demo 1024×1024×4 ≤30s CPU / ≤10s GPU; hallucination <2% flagged.

---

## 2. PRD — Product Requirements

**Stakeholders:** NTRO analyst (primary, needs trust), urban/disaster planners (secondary), ISRO judge (geospatial fidelity), AgTech/research (NDVI).

**User Stories:**
1. As analyst, I upload 10m 4-band `.tif` ≤50MB → get `<4m` COG + heatmap to verify per-pixel reliability.
2. As planner, I compare 10m vs SR vs heatmap in viewer with DN stats.
3. As evaluator, I run NDVI on output and it matches input (r>0.98) and overlay is pixel-perfect.

**Requirements (P0 = must for SIH internal):**

| ID | Requirement | Acceptance |
|---|---|---|
| PR-01 | Accept `.tif/.tiff` 1/3/4/8-band ≤50MB, preserve CRS via TIFF tags 33550/33922/34264/34735 | Round-trip `Affine.scale` test |
| PR-02 | Auto-detect channel count, dynamic 1×1 conv in/out — 8-band on-spot `prompt.txt:98` must not crash | 4 & 8 band pass |
| PR-03 | 3× upscale via 256×256+16 overlap Gaussian blend, stitch seamless | Seam RMSE<1 DN, <8GB RAM on 1GB input |
| PR-04 | `Loss = L1 + Perceptual(VGG) + λ·SAM` | SAM<3° val |
| PR-05 | Uncertainty heatmap MC-Dropout T=10 std → viridis 0-1, threshold 0.6 red | Pearson std vs error >0.6 |
| PR-06 | Metrics panel PSNR/SSIM/LPIPS/SAM/ERGAS/NDVI-delta | Rendered |
| PR-07 | COG GeoTIFF planar C×H×W + PNG data URI `POST /api/infer` JSON `{success,images{input,sr,heatmap},download*,meta,metrics}` | QGIS overlay OK |
| PR-08 | 4-layer viewer slider (input/SR/heatmap/diff) | Keyboard+pointer |
| PR-09 | Batch folder (future) | P2 |

---

## 3. BRD — Business Requirements

**Need:** Sovereign, cost-free extraction of <4m value from open EO — reduce Maxar/Planet buy.

**Objectives:** Cost/km² ↓70%, hallucination <2% flagged, NDVI r>0.98, on-prem air-gapped (no foreign API, mirrors Kepler local Flask but fresh).

**Rules:** No hallucinated structure without high uncertainty veto; SAM ≤3°; EPSG retained; 24h purge for demo, on-prem persistent for NTRO.

**Value:** SIH win → internship → ministry beta (`SIH2026_About_SIH.md:43-48` 5-step) → state pilot (Maharashtra) → STAC/Bhuvan → AgTech API freemium.

**Risk→Mitigation:** hallucination→uncertainty veto; no paired data→synthetic degradation business-approved; NIR stripped→N-channel+SAM.

---

## 4. MRD — Market Requirements

**Market:** EO analytics $8B global, India ~$1B; 10-30m medium-res dominates but lacks fine detail.

**Segments:** NTRO/defence (high willingness), ISRO/NDMA/urban (high sovereign), AgTech/insurance (medium cost-save), GIS firms (medium).

**Competition vs Positioning:**
| Competitor | Price | Gap |
|---|---|---|
| Topaz Photo AI | $199 | Strips CRS+NIR, not geospatial |
| Research ESRGAN on SpaceNet | Free | RGB-only, hallucinates, no SAM/uncertainty |
| KSAT SAR | Enterprise | Not SR, foreign |

**Need:** Open-data, QGIS-ready COG, quantified uncertainty, on-prem, web demo.

**TAM:** India 3.2M km² × 230M km²/year; 1% adoption → ₹11Cr/year India Gov saved @₹5/km².

**GTM:** SIH → NTRO beta → STAC → AgTech API.

---

## 5. FRD — Functional

| ID | Function | I/O | Rule |
|---|---|---|---|
| FR-01 | Ingest GeoTIFF | N×H×W + CRS/affine | Keep all bands (not `raw[:,:,0]`) |
| FR-02 | Validate | Header | 400/415 JSON clean |
| FR-03 | Normalize | per-band 2-98% clip → uint8 | Per-band, not global |
| FR-04 | Tile | H×W×C → 256+16 list + weights | Gaussian |
| FR-05 | SR tile | 256×256×C → 768×768×C | N-ch ESRGAN/SwinIR, batched |
| FR-06 | Uncertainty | T passes → H×W heatmap | std 0-1 |
| FR-07 | Stitch | Tiles+weights → N×H'×W' + new affine `*Affine.scale(w/new_w,h/new_h)` | CRS unchanged, pixel ÷3 |
| FR-08 | Metrics | vs ref if synthetic else no-ref NIQE | SAM arccos, ERGAS, NDVI delta |
| FR-09 | Export | COG + PNG + data URI | Tags 33550/33922/34735 planar |
| FR-10 | Viewer | 4-layer slider + stats + downloads | Data URI avoids /tmp |
| FR-11 | Purge | 24h | On start |

**Flows:** UC-01 Upload→SR→Viewer→QGIS; UC-02 synthetic validation table.

---

## 6. SRS — Software Spec (IEEE 830)

**Scope:** Web service + ML pipeline + viewer.

**F-SRS-01:** `POST /api/infer` multipart `file` → `200 {success,images{input,sr,heatmap},download,download_tif,download_heatmap,meta{job_id,input_size,output_size,crs,elapsed,file_type},metrics{psnr,ssim,sam,ergas,ndvi}}` (extends Kepler `README:178-197` add heatmap/metrics).

**F-SRS-02:** CRS preserve via tags 33550/33922/34735 + `Affine.scale`.

**F-SRS-03:** Auto-detect 1/3/4/8 bands, route N-ch without config.

**Perf:** 1024×1024×4 CPU ≤30s GPU ≤10s; 1 concurrent queue; 24h ephemeral.

**Constraints:** Python 3.9+, Flask+CORS, `MAX_CONTENT_LENGTH=50MB`, stateless `Pipeline`, `ProcessingError`→500, `DecodingError`→400.

**Attributes:** Reliable (wrap exc), Usable (ARIA, `prefers-reduced-motion`), Secure (no persist >24h), Portable (Docker+vercel).

**Validation:** PSNR/SSIM/LPIPS SAM ERGAS NDVI; RMSE<0.3px tiepoint.

---

## 7. TRD — Technical Constraints

| ID | Constraint | Value | Src |
|---|---|---|---|
| TR-C01 | Max upload | 50MB 413 else | Kepler `README:281` |
| TR-C02 | Formats | `.tif/.tiff` + `.png/.jpg` | `README:282` |
| TR-C03 | Scale | 3× 10m→3.33m | `prompt.txt:47` |
| TR-C04 | Retention | 24h purge | `README:284` |
| TR-C05 | Port | 5000 `Settings` | — |
| TR-C06 | Python | 3.9+ | — |
| TR-C07 | Tile | 256+16 Gaussian | `prompt.txt:115` |

**Stack:**

```
Backend Flask+Gunicorn+CORS | Geospatial Rasterio/GDAL/Affine/tifffile/Geopandas | Image opencv/numpy/pillow/scikit-image/lpips | ML PyTorch+torchvision ESRGAN/SwinIR albumentations | Frontend Vanilla JS+Leaflet+GeoTIFF.js (React-ready Vite) | Infra Docker python:3.9-slim+gdal Vercel nvidia-docker | Train Colab Pro T4/A100 40 GPU-hrs mixed precision
```

**Deps:**

```
flask, flask-cors, opencv-python-headless, numpy, tifffile, affine, rasterio, geopandas, pyproj, torch, torchvision, scikit-image, lpips, albumentations, pytest, gunicorn
```

**Data:** Sentinel-2 L2A Copernicus/GEE 10m B02/B03/B04/B08; synthetic SpaceNet 0.5m blurred+INTER_AREA 6×→3m→10m +1% noise + CRS manifest; val PlanetScope 3m/Cartosat 1m holdout.

**Perf/Security/Scale:** Tile <200ms GPU, seam RMSE<1, validation `is_geotiff()`+magic, stateless horizontal replicas.

---

## 8. DRD — Design

**System:** `HDR #1F4E79` diamond, `GREEN #15803D` subhead, `RED #A32B20` warning, `CREAM #FFF2CC` flow, `GREY #F2F2F2` method, `BLACK` border, `WHITE` box; Serif 23pt Times title, Calibri 10-11pt body, Consolas mono metrics; 13.333×7.5 LB0.3/RB6.95.

**UX:** Glassmorphism, dot cursor, particle hero, dark/light `localStorage`, drag-drop+sample chips (Urban/Ocean/Volcanic/Desert), 4-way slider drag+keyboard, telemetry job_id/dims/CRS/elapsed, PNG+COG download, toast, offline preview, responsive drawer+ESC, progress via real response.

**IA:** Header SIH26142 | Pipeline 4 nodes (Ingest→SR→Uncertainty→Export) | Demo upload→results grid data URI→metrics→downloads | FAQ TIR→SAM/NDVI.

---

## 9. TDD — How to Build (New Project, No Fork Debt)

**Context:** External Copernicus/GEE, SpaceNet, QGIS, SIH portal PDF; internal Flask `core/app.py` → `Pipeline` → `IO` → `Patch` → `SR` → `Metrics`.

**Components (all fresh, no copy):**

| Comp | File (new) | Responsibility |
|---|---|---|
| Config | `core/config.py` | `tile_size=256 overlap=16 scale=3 device cuda/cpu model_name dropout mc` |
| IO | `core/io.py` | N-band `GeoReadResult{band:C×H×W,transform,crs,w,h,count}`, per-band 2-98% clip, COG planar write tags |
| Patch | `core/patch.py` | `TileManager` Gaussian weight, `tile()`/`stitch()` |
| SR | `core/transforms.py` | `SRModel(in_ch,out_ch)` RRDB 23, PixelShuffle 3×, `super_resolve()`+`uncertainty()` MC |
| Metrics | `core/metrics.py` | sam/psnr/ssim/ergas/ndvi |
| Datasets | `core/datasets.py` | `degrade()` 0.5m→10m synthetic |
| Pipeline | `core/pipeline.py` | `run(path,job_id)` Stateless orchestration |
| Routes | `api/routes.py` | `/api/infer` multipart, `/download` |
| Frontend | `frontend/` | Vanilla JS (React-ready) Leaflet viewer |

**Data Flow:** `TiffFile → GeoReadResult C×H×W → normalize → TileManager → SRModel 1×C×256→1×C×768 → stitch acc/weight → heatmap → metrics → tifffile planar → data URI → JSON`.

**Deployment:** Dev `python app.py` debug reload; Prod `gunicorn core.app:create_app()` Docker GDAL; Vercel demo data URI avoids /tmp; NTRO on-prem systemd.

**Migration note:** No `MODE=tir` flag needed (fresh), Kepler ideas reused logically not code-wise.

---

## 10. SDD — Detailed Architecture

**Modules:**

```
Sentinel-SRM/
 app.py (launcher) | core/{app,config,exceptions,logging,io,patch,transforms,metrics,datasets,models,pipeline} | api/routes | frontend/{templates,static} | weights/ | uploads/ static/results/ | tests/
```

**Data Models:**

```python
GeoReadResult{band: C×H×W uint8, transform:Affine, crs:"EPSG:32643", width,height,count}
InferenceResult{job_id, images{input,sr,heatmap}, download*, meta{input_size,output_size,crs,elapsed,file_type}, metrics{psnr,ssim,sam,ergas,ndvi}}
JobMeta{job_id,input_size,output_size,crs,elapsed,file_type}
```

**Sequences:** Client→Routes `multipart` → Pipeline `is_geo?` → IO `C×H×W` → Patch `tiles` → SR per tile batched → stitch `H'×W'`+`new_affine` → metrics → IO `COG+tifffile tags`+`write_png`×3 → `to_dict()` data URI → 200 JSON.

**Algorithms:**
* SR RRDB `in_nc=N out_nc=N nf64 nb23 scale3` first conv `64×N×3×3` RGB copied NIR=mean RGB; `x/255→model→clip→uint8`.
* Loss `L1+0.1·Perceptual VGG+0.05·SAM`; `SAM=mean(arccos(dot/|pred||gt|))`; optional `|NDVI_sr-NDVI_gt|`.
* Tile 256 stride240 weight `exp(-d²/2σ²)` σ=overlap/2; `acc[C,H',W'] / wsum`.
* Uncertainty MC p0.2 T10 → mean+std → viridis normalized, threshold 0.6 red.
* Metrics PSNR `10log10(255²/MSE)` SSIM skimage LPIPS VGG SAM ERGAS `100·h/l·sqrt(mean((RMSE/B)²))` NDVI `(NIR-Red)/(NIR+Red)`.

**Config `Settings` as TRD §7** with `ensure_dirs()` `is_geotiff()`.

**Tests:** `test_io` N-band CRS roundtrip Affine.scale, `test_patch` checkerboard RMSE<1, `test_transforms` 4&8 shape, `test_pipeline_e2e` JSON contract `sample.tiff`+synthetic 4-band.

---

## 11. HLD — Overall Architecture

```
              Copernicus/GEE 10m 4-band
                        │
Analyst Browser ──► Sentinel-SRM Flask ──► QGIS/ArcGIS COG
                        │                    ▲
                        ├─► weights ESRGAN/SwinIR
                        └─► metrics/log
```

**Components:** Web UI (Leaflet), API Gateway (Flask CORS), Orchestrator (`Pipeline.run`), IO (Rasterio), ML (PyTorch), Tiling, Metrics, Storage 24h, Dataset Builder SpaceNet.

**Deployment:** Browser HTTP→Flask Gunicorn :5000 Docker (uploads/results emptyDir, weights readOnly, GPU optional) → Vercel edge demo, on-prem NTRO.

**Interfaces:** `POST /api/infer` GeoTIFF, `GET /api/download`, COG tags, SIH PDF 6 slides.

**Flow high:** `Input 10m N×H×W ─normalize─► 256 tiles ─SR 3×─► 768 tiles ─stitch─► SR N×H'×W' + heatmap ─metrics─► JSON+COG`.

**NFR:** Stateless UUID, <8GB RAM via tiling, wrap `DecodingError 400`/`ProcessingError 500`, 50MB limit, no exec.

---

## 12. LLD — Classes/APIs/DB/Algorithms (Low Level)

**Classes:** `Settings` (host/port/debug/upload/results/max_bytes/tile/scale/device/dropout/mc), `GeoReadResult` C×H×W, `Tile{data:C×256,coords,weight}`, `TileManager tile()/stitch()`, `SRModel(in_ch,out_ch,scale,arch)` RRDB `__call__(1×C×H×W)`, `Pipeline(run, _process_geotiff, _shared_stages)`.

**APIs:**
* `POST /api/infer` req `multipart file` (50MB) → validate 413/415 → `200 {success,images{input,sr,heatmap: data URI},download,download_tif,download_heatmap,meta{job_id,input_size,output_size,crs,elapsed,file_type},metrics{psnr,ssim,sam,ergas,ndvi}}`
* `GET /api/download/<f>` `Content-Disposition attachment` 404 if purged.

**DB:** No DB MVP; optional SQLite `jobs(job_id, input_name,crs,input_size,output_size,elapsed,psnr,created_at)`.

**Pseudocode:** `degrade()` Gaussian PSF 0.8 INTER_AREA, `normalize_per_band()` 2-98% clip, `sam()` `arccos(dot/norms)`, `TileManager` unfold Gaussian, `Pipeline` tile→`torch.from_numpy/255`→`model`→`clip`→`stitch`→`tifffile planar`.

**File Paths:** `app.py`→`core/app:create_app`→`api/routes`→`core/pipeline:run`; `static/results/<job>_*.png` data URI, `weights/real_esrgan_4ch.pth` lazy.

**Sequence tiled SR loop:** `tile_tensor 1×C×256 → model → 1×C×768 → uint8 → acc*weight / wsum`.

**Tests:** `test_io_ndim` 4-band CRS, `test_patch` seam RMSE<1, `test_sam` same≈0° random>10°.

---

## 13. FLOW — End-to-End Flows (Mermaid)

User Journey (upload→4-layer viewer→QGIS), System (Browser→Flask→Patch→SR→Metrics→QGIS), Data (N×H×W→tile→batch→stitch→COG), Training (SpaceNet 0.5m→blur→synthetic 10m→pair→VGG+SAM→AdamW), Inference sequence (multipart→read→tile→SR→stitch→heatmap→write→JSON), Tiling/Uncertainty/Metrics sub-flows, Decision SAM>3° reject / UQ>0.6 warn, Deployment dev/train/prod/SIH, Failures (8-band, OOM, CRS lost, hallucination).

---

## 14. DEVELOPMENT CYCLE — Agile 3 Sprints

**Overall:** P1 Planning 2d → P2 Design 2d → M1 I/O+Tiling 3d → M2 Train 7d → M3 Viewer+Uncertainty 3d → Test 2d → Integrate 1d → Deploy 1d → Demo 2d → Feedback 1d (21d total `SIH2026_About_SIH:15-24`).

**M1 D5-7:** `core/io.py` all bands, `core/patch.py` Gaussian, `core/datasets.py` synthetic 10k tiles, `pipeline` tiling, seam RMSE<1.

**M2 D8-14:** `core/transforms.py` N-ch 1×1, train EDSR→Real-ESRGAN loss `L1+0.1Perceptual+0.05SAM`, `core/metrics.py` SAM/ERGAS/NDVI.

**M3 D15-17:** `uncertainty()` T10, `models.ImageSet` heatmap, `frontend` 4th layer, N-band COG, E2E ≤30s CPU.

**Daily Loop:** 09:00 standup → `feat/*` branch → code+`pytest watch` → PR 1 approver → CI `ruff/pytest/docker/vercel` → merge `develop` → 17:00 demo `sample.tiff`.

**Branching:** `main (deploy) ← develop ← feat/patch, feat/nch-sr, feat/uncertainty`; tags `v0.1-m1 v0.2-m2 v1.0-sih`.

**CI:** push `develop` → lint → `pytest -k not slow` → docker GDAL → vercel prebuilt → slack metrics.

**DoD SIH:** CRS preserved `Affine.scale`, SAM<3° NDVI r>0.98, 8-band no crash `prompt.txt:98`, GB tiled no OOM no seam, Pearson >0.6, 6-slide PDF points not paragraphs real flowchart.

---

## 15. TECH STACK — Why Fresh

| Layer | Choice | Why Fresh |
|---|---|---|
| Backend | Flask+Gunicorn | Light vs Django, keeps Kepler CORS idea but no copy |
| Geospatial | Rasterio/GDAL/Affine/tifffile | Fresh N-band first (no `raw[:,:,0]` debt) |
| ML | PyTorch ESRGAN/SwinIR | Mandatory `prompt.txt:22`, 1×1 dynamic N-ch from day 1 |
| Frontend | Vanilla JS+Leaflet (React-ready Vite) | No Kepler `model` debt, fresh 4-layer |
| Infra | Docker gdal, Vercel, Colab Pro | Sovereign, stateless, 24h purge |

**Traceability v2:** Every section maps to `prompt.txt:4-52` (pain→SAM→synthetic→Q&A), SIH 6-slide `sih py ppt.txt:8-36`, and `SIH2026_RESEARCH:67`.

---

*End v2 — New Project. Next: `git init` fresh `Sentinel-SRM/` scaffold per SDD §10 when you say “Start M1”.*
