# PRD — Product Requirements Document
## SIH26142: Deep Learning Based Super Resolution Mapping from Medium Resolution Satellite Imagery

**Product:** Sentinel-SRM (Kepler-404 Fork) | **Org:** NTRO — Space Technology (Software) | **PS ID:** SIH26142  
**Version:** 1.0 | **Date:** 2026-08-29 | **Author:** Shreyas Pawar (Kepler-404) | **Status:** Draft → Implementation

---

### 1. Purpose
Transform free 10m Sentinel-2 L2A imagery into scientifically-reliable `<4m` (target 3.3m, 3×) super-resolved GeoTIFFs while preserving geospatial (CRS/affine) and spectral (SAM) consistency, with per-pixel uncertainty for intelligence/decision use. Built as fork of `Kepler-404` (200m→100m TIR pipeline, Flask+Rasterio) to meet NTRO SRM spec (`prompt.txt:47-52`).

### 2. Goals & Non-Goals

| Goals (Must Deliver) | Non-Goals (Out of Scope for SIH Internal) |
|---|---|
| N-channel (4-band RGB+NIR, dynamic up to 8) GeoTIFF in → COG GeoTIFF out with identical CRS | Full 13-band Sentinel-2 or hyperspectral at submission (future) |
| PSNR/SSIM + SAM + ERGAS + NDVI-delta validation vs high-res ref | Pan-India real-time streaming pipeline (future) |
| Uncertainty heatmap (MC-Dropout/ensemble) per pixel | TIR→RGB colorization branch (kept as optional flag, not primary) |
| Patch-based seamless processing for GB scenes | Classification/change-detection downstream (nice-to-have only) |

### 3. Stakeholders

| Stakeholder | Role | Need |
|---|---|---|
| NTRO analysts | Primary user | Reliable sub-pixel detail without hallucination (`prompt.txt:106` bridge Q) |
| Urban planners / Disaster units | Secondary | Road/building/field boundary visibility (`prompt.txt:6`) |
| ISRO/SAC evaluators | Judge | Geospatial fidelity (overlay on Google Earth) + spectral truth (`prompt.txt:64-66`) |
| AgTech / Research | Tertiary | NDVI-compatible output (`prompt.txt:68`) |

### 4. User Personas

**Analyst Arjun (NTRO):** Needs to overlay SR output on Bhuvan/QGIS, run NDVI, distrusts GAN hallucinations — requires uncertainty mask.  
**Planner Priya (Urban):** Uploads district Sentinel-2 clip, expects 3× sharper roads/buildings in <30s for planning.

### 5. Scope

**In-Scope:** Ingest, tiling, N-channel ESRGAN/SwinIR 3×, SAM-regularized loss, stitch + COG export, viewer with 3-way slider + 4th uncertainty layer, metrics dashboard.  
**Out-of-Scope:** Satellite tasking, real-time downlink, SAR fusion, mobile app.

### 6. User Stories (Prioritized)

1. As Arjun, I upload a 10m 4-band `.tif` (50MB) → get `<4m` GeoTIFF + heatmap so I can verify reliability per pixel.
2. As Priya, I see side-by-side 10m / SR / heatmap with DN stats so I can decide to trust.
3. As evaluator, I download COG and validate PSNR/SSIM/SAM in report.
4. As developer, I train on synthetic 0.5m→10m pairs (SpaceNet) when real pairs unavailable (`prompt.txt:103`).

### 7. Product Requirements

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| PR-01 | Accept `.tif/.tiff` 1/3/4/8-band, ≤50MB, preserve CRS/transform (`kepler/io.py:55-66`) | P0 | Round-trip `Affine.scale` test passes |
| PR-02 | Auto-detect channel count, dynamic 1×1 conv in/out | P0 | 4-band & 8-band on-spot file works (`prompt.txt:98`) |
| PR-03 | 3× upscale (10m→3.3m) via tiled inference 256×256+16 overlap, Gaussian blend | P0 | No seam lines, <8GB RAM on 1GB input |
| PR-04 | Loss `L1 + Perceptual + λ·SAM` (`prompt.txt:88`) | P0 | SAM <3° on validation |
| PR-05 | Uncertainty heatmap (MC-Dropout T=10 or 3-model ensemble) | P0 | Pearson>0.6 between uncertainty and error |
| PR-06 | Metrics panel: PSNR, SSIM, LPIPS, SAM, ERGAS, NDVI-delta | P0 | Rendered on result page |
| PR-07 | COG GeoTIFF + PNG download, `/api/infer` contract unchanged (`Kepler-404/README.md:167`) | P0 | QGIS overlay pixel-perfect |
| PR-08 | Viewer 4-layer (input/SR/heatmap/comparison) | P1 | Interactive slider, mobile responsive |
| PR-09 | Batch API for folder of tiles | P2 | Future |

### 8. Success Metrics

* PSNR ≥28dB, SSIM ≥0.80 on synthetic holdout; SAM <3°, ERGAS <2.5
* Geospatial RMSE <0.3 pixel after overlay
* Demo latency: ≤30s for 1024×1024 4-band on CPU; ≤10s on GPU
* SIH internal: 6-slide deck compliant (see PRD §7 → PPT blueprint)

### 9. Constraints & Assumptions

* Paired real 10m↔3m same-day data unavailable → assume synthetic degradation (`prompt.txt:101-103`).
* GPU for training (Colab Pro/AWS `prompt.txt:18`); inference CPU-able.
* Max file 50MB (`Kepler-404/README.md:281`) — larger via tiling/pagination.

### 10. Roadmap

* **M1 (Wk1):** Multi-band I/O + tiling + synthetic dataset 10k tiles
* **M2 (Wk2):** EDSR baseline → SwinIR N-ch + SAM training, metrics harness
* **M3 (Wk3):** Uncertainty head, viewer 4-layer, COG export, SIH deck + demo deploy

### 11. Open Decisions

* 4-band MVP vs 13-band — default 4-band for submission.
* Keep TIR branch as `--mode=tir` flag or remove — default remove.

---
*Traceability: PRD derives from `prompt.txt:4-52`, `Kepler-404/kepler/pipeline.py:32-91`, `SIH2026_PPT_Submission_Template.md:22-52`.*
