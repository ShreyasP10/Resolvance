# MASTER PROMPT — Go Through All Files & Start Working on SIH26142 Sentinel-SRM
## Copy-paste this into a new AI / Developer session to bootstrap implementation

---

### SYSTEM: You are a Senior Full-Stack + Geospatial + Deep Learning Engineer

**Mission:** Read **EVERY** file listed below **in order**, then start implementing **SIH26142 NTRO — Deep Learning Based Super Resolution Mapping 10m Sentinel-2 → <4m (3×)** as a fork of the existing `Kepler-404/` prototype. Do not skip files. Do not hallucinate specs — all specs are in the files.

---

### PHASE 0 — READ ALL FILES (Read-Only, In Exact Order)

**Step 0.1 — SIH Knowledge Base (Context):**

1. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\README.md` — Master hub (226 PS, 18 themes, deadlines)
2. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_About_SIH.md` — SIH process flow + 5-step adoption
3. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_All_226_Problem_Statements.md` — Verify SIH26142 entry (Space Technology, Software, NTRO)
4. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_AI_ML_Problem_Statements.md` — Confirm SIH26142 in CV cluster
5. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\prompt.txt` — **CRITICAL** 10-point hackathon breakdown for PS142 (pain, feasibility, uncertainty injection, SAM, synthetic degradation, judge Q&A)
6. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_Theme_And_Organization_Breakdown.md` — MoES/NTRO/ISRO org distribution
7. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_Difficulty_Levels.md` — Why SIH26142 is Medium-Hard (yellow)
8. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_RESEARCH_AND_ANALYSIS.md` — Competition: no sovereign SR product (status yellow, Overall 67)

**Step 0.2 — Existing Prototype (Audit, Do Not Modify Yet):**

9. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\README.md` — Kepler-404 200m→100m TIR pipeline, mock ESRGAN/SwinIR, CRS preservation
10. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\kepler\pipeline.py` — Pipeline.run() orchestration, Affine.scale logic
11. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\kepler\io.py` — GeoReadResult, tifffile CRS tags, normalize 2-98% clip
12. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\kepler\transforms.py` — Mock super_resolve (cv2.resize) + colorize (Inferno) — to be replaced N-channel
13. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\kepler\config.py` — Settings host/port/debug, is_geotiff()
14. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\kepler\app.py` + `app.py` — Flask create_app
15. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\Kepler-404\requirements.txt` — Current deps (add torch/rasterio later)
16. `https://kepler-404.vercel.app/` — Live demo (200m→100m, 3-way slider) — inspect for UI parity

**Step 0.3 — SIH Submission Format (Compliance):**

17. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2024_IDEA_Presentation_Format.pptx` — Official 6+1 template extract (7 slides, last is instructions)
18. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\sih py ppt.txt` — Exact visual code (HDR #1F4E79, GREEN #15803D, CREAM #FFF2CC, 13.333×7.5) — for final PDF
19. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH ppt 3.txt` — Reference winning ORBITGUARD deck structure (ignore content, keep 6-slide blueprint idea)
20. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_PPT_Submission_Template.md` — Official 6-slide pointers (Slide1 Title → Slide6 References)
21. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\SIH2026_Idea_Research_Prompt_Template.md` — Deep-research template (11 sections)

**Step 0.4 — Full Requirements Suite (Your Source of Truth, Read All 12):**

22. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\00_INDEX.md` — Master index + traceability
23. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\01_PRD.md` — What to build (PR-01→09, KPIs PSNR≥28 SAM<3°)
24. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\02_BRD.md` — Business need (save $1000s/scene, on-prem sovereignty)
25. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\03_MRD.md` — Market positioning vs Topaz/KSAT
26. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\04_FRD.md` — Functional requirements (FR-01→12, 4-layer viewer)
27. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\05_SRS.md` — IEEE 830 spec, API contracts
28. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\06_TRD.md` — Constraints (50MB, 3× scale, tiling 256+16, GPU mandatory)
29. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\07_DRD.md` — Design system (glassmorphism, colors, slider)
30. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\08_TDD.md` — How to implement (new patch.py/metrics.py/datasets.py, modify io/transforms)
31. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\09_SDD.md` — Detailed modules, loss L1+Perceptual+SAM, TileManager
32. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\10_HLD.md` — High-level architecture & deployment Docker/Vercel
33. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\11_LLD.md` — Low-level classes, API JSON, pseudocode, DB schema
34. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\flow.md` — 10 flows (user, system, data, training, inference sequence)
35. `C:\Users\Dinesh B Pawar\OneDrive\Desktop\SIH-2026\docs\SIH26142\development_cycle.md` — Agile 3-sprint working cycle (M1→M3, daily loop, CI/CD)

**After reading all 35 items, you must be able to answer:**

* What is the exact SIH26142 expected solution (`prompt.txt:47-52`)?
* Why must you NOT use JPG/PNG (`prompt.txt:55`)?
* What is the synthetic degradation trick (`prompt.txt:103`) and why is it needed (`prompt.txt:101`)?
* How does Kepler-404 preserve CRS (`kepler/io.py:104-142` + `pipeline.py:87-89`)?
* What is the loss formula (`prompt.txt:88`)?
* What are the 3 judge Q&A answers (`prompt.txt:106-115`)?

If you cannot, re-read the listed files — do not proceed.

---

### PHASE 1 — VERIFY ENVIRONMENT (Before Coding)

1. Confirm `python --version` 3.9+, `pip list` shows `flask, tifffile, affine, opencv`, install missing `torch, rasterio, scikit-image, lpips` per `06_TRD.md` §5.
2. Run existing Kepler-404: `cd C:\...\Kepler-404 && python app.py` → hit `http://127.0.0.1:5000` → upload `sample.tiff` → verify 200→100m + CRS `EPSG:32643` in JSON.
3. Run `pytest` → all green (`Kepler-404/.pytest_cache`).
4. Create branch: `git checkout -b sih26142-sentinel` from `Kepler-404/`.

---

### PHASE 2 — IMPLEMENT IN ORDER (Strict Sequence, No Skipping)

**Sprint M1 (Days 5-7) — I/O + Tiling + Synthetic Data:**

* Task M1.1: Fix `kepler/io.py` — modify `read_geotiff()` to keep ALL bands (`raw[:,:,0]` bug → keep `C×H×W`), add `count` to `GeoReadResult`, per-band `normalize_to_uint8_per_band()` (see `09_SDD.md` §5.2).
* Task M1.2: Create `kepler/patch.py` — `TileManager` 256×256 stride 240 Gaussian weight (`09_SDD.md` §4.1/6.3).
* Task M1.3: Create `kepler/datasets.py` — `degrade()` SpaceNet 0.5m → synthetic 10m (Gaussian blur + INTER_AREA 6×) (`11_LLD.md` §5.1).
* Task M1.4: Patch `kepler/pipeline.py` — branch tiling loop, compute `new_affine = old * Affine.scale(w/new_w, h/new_h)`, test seam RMSE <1 DN.
* **Exit M1:** `pytest tests/test_io_nch tests/test_patch` green, 10k synthetic tiles generated.

**Sprint M2 (Days 8-14) — Model + Loss + Metrics:**

* Task M2.1: Modify `kepler/transforms.py` — `SRModel` factory `in_ch=N out_ch=N` 1×1 conv mean init, `super_resolve()` torch forward (`11_LLD.md` §2.4), keep `colorize` only for `--mode=tir` flag.
* Task M2.2: Train EDSR baseline (fast) then Real-ESRGAN/SwinIR on synthetic pairs, loss `L1 +0.1 Perceptual +0.05 SAM` (`09_SDD.md` §6.2), mixed precision, log PSNR/SSIM/SAM.
* Task M2.3: Create `kepler/metrics.py` — `sam()`, `psnr`, `ssim`, `ergas`, `ndvi_delta` (`11_LLD.md` §5.3).
* **Exit M2:** Holdout PSNR≥28 SSIM≥0.80 SAM<3° (`01_PRD.md` §8).

**Sprint M3 (Days 15-17) — Uncertainty + Viewer + Export:**

* Task M3.1: Add `uncertainty()` MC-Dropout T=10 std → heatmap 0-1 viridis (`09_SDD.md` §6.4).
* Task M3.2: Extend `kepler/models.py` `ImageSet` to `input/sr/heatmap`, update `routes.py` JSON contract (`11_LLD.md` §3.1).
* Task M3.3: Update `templates/index.html` + `static/js/script.js` — 4th heatmap layer slider, metrics card Mono `Consolas` (`07_DRD.md` §4-5), keep glassmorphism.
* Task M3.4: Modify `kepler/io.py:write_geotiff` to write N-band planar COG (`tifffile.imwrite` `C×H×W`), verify QGIS overlay RMSE <0.3px.
* **Exit M3:** E2E `POST /api/infer` 1024×1024×4 finishes ≤30s CPU, download_tif is valid COG.

---

### PHASE 3 — TEST, INTEGRATE, DEPLOY

* **Test (D18-19):** Run full `pytest` + manual `sample.tiff` + synthetic 4-band + 8-band on-spot (`prompt.txt:98`) → no crash.
* **Integrate (D20):** Merge `develop` → `main`, tag `v1.0-sih`, Docker build `python:3.9-slim + gdal`.
* **Deploy (D21):** `vercel.json` deploy for demo + on-prem image for NTRO air-gapped.
* **Docs (D22):** Generate 6-slide PPT text per previous Slide 1-6 blueprint (use image prompts in `flow.md` §9 for diagrams), export PDF (PDF only, no PPT per `SIH2024_IDEA:Slide7`), fill `SIH2026_Idea_Research_Prompt_Template.md` 11 sections.

---

### PHASE 4 — VALIDATION GATES (Must Pass Before Claiming Done)

* [ ] N-channel roundtrip CRS preserved: input EPSG == output EPSG, affine scaled correctly
* [ ] SAM <3°, NDVI r>0.98 (`prompt.txt:68` judge will test NDVI)
* [ ] 8-band file does not crash (dynamic channel)
* [ ] GB scene via tiled inference no OOM, no seam lines
* [ ] Uncertainty Pearson std vs error >0.6
* [ ] SIH 6-slide PDF compliant (points not paragraphs, 6 max, real flowchart)

---

### RULES

* Do not change API shape beyond adding `heatmap`/`metrics` — keep `success, images, download, meta` contract (`Kepler-404/README.md:178-197`).
* Do not invent datasets/metrics — only use verifiable sources (Copernicus, SpaceNet, SAM).
* Every edit must keep `kepler/pipeline.py:59-63` error wrapping and 24h purge (`Kepler-404/README.md:284`).
* Quote file:line when referencing code (e.g., `kepler/io.py:60-61`).

---

### OUTPUT EXPECTED AFTER THIS PROMPT

1. Confirmation you read all 35 files (list them).
2. Branch `sih26142-sentinel` created.
3. M1 tasks completed with `pytest` logs + 1 synthetic pair visualized.
4. Daily demo at 17:00 on real Sentinel-2 tile.

**Now start: Read files 1→35 in order and begin M1.1. Show your first `read_geotiff` N-band fix diff.**
