# DRD — Design Requirements Document
## SIH26142 Sentinel-SRM Viewer & System Design

### 1. Design Goals

* **Mission Control** glassmorphism retains Kepler-404 identity (`Kepler-404/README.md:43`) but adds 4th heatmap layer.
* **Scientific trust:** Show uncertainty, metrics, CRS truth — not just pretty RGB.
* **SIH compliance:** 2-box side-by-side per `sih py ppt.txt:8-10`.

### 2. Visual Design System (from `sih py ppt.txt:22-36` + `Kepler-404/static/css`)

* **Palette:** `HDR #1F4E79` diamond headers, `GREEN #15803D` subheads, `RED #A32B20` warnings, `CREAM #FFF2CC` flow nodes, `CREAM2 #DEEBF7`, `GREY #F2F2F2` methodology, `BLACK #000000` borders, `WHITE #FFFFFF` boxes.
* **Typography:** Serif `Times New Roman` titles 23pt, Body `Calibri` 10-11pt, Mono `Consolas` for API/metrics.
* **Layout:** 13.333×7.5 inches, LB 0.3/RB 6.95 boxes 6.4/6.05W (as `sih py ppt.txt:192-196`).

### 3. UX Requirements

| Requirement | Spec |
|---|---|
| Design System | CSS custom properties for light/dark themes, `localStorage` persist (`Kepler-404/README.md:43`) |
| Cursor | Dot+lerp outline, disabled on touch |
| Hero | Particle network canvas + mouse repulsion |
| Upload | Drag-drop + browse + sample chips (Urban/Ocean/Volcanic/Desert as `kepler-404.vercel.app`), 50MB limit, progress via actual response |
| Comparison | 4-way slider: drag handles reveal Input(10m) / SR(<4m) / Heatmap / Diff; keyboard accessible (`Kepler-404/README.md:43`) |
| Telemetry | Live job ID, input/output dims, CRS EPSG, elapsed (`Kepler-404/README.md:47` JobMeta) |
| Export | One-click PNG + COG GeoTIFF download |
| Accessibility | ARIA, keyboard nav, `prefers-reduced-motion` (`Kepler-404/README.md:50`) |
| Responsive | Fluid desktop/tablet/mobile, slide-in nav drawer + ESC close |

### 4. Information Architecture

* **Header:** `SIH26142 | Kepler-404 Sentinel-SRM` + nav Pipeline/Demo/FAQ
* **Pipeline Section:** 4 nodes (Ingest → SR → Uncertainty → Export) as `Kepler-404/README.md:56-63` but N-channel variant.
* **Demo Section:** Upload card → results grid (3 PNG previews base64) → metrics card → download row.
* **FAQ:** Adapt `kepler-404.vercel.app/FAQ` — TIR Qs → Sentinel SAM/NDVI/uncertainty Qs.

### 5. Interaction Design

* Upload → `POST /api/infer` → loader (mock 2.5s removed prod `Kepler-404/README.md:287`) → render data URIs + metrics.
* Slider: pointer + keyboard, `pointerEvents` + `keydown` ArrowLeft/Right.
* Toast: auto-dismiss success/error, offline fallback preview mode.

### 6. Component Spec

| Component | Behavior | Visual |
|---|---|---|
| `compare-slider` | 3 handles, `clip-path` per layer | Handles `HDR` dot, track `GREY` |
| `metrics-card` | Table PSNR/SSIM/SAM/ERGAS | Mono font, GREEN header |
| `heatmap-legend` | 0-1 gradient viridis | Legend bar + % ticks |
| `download-row` | Two buttons | Primary `HDR` PNG, secondary `GREEN` TIF |

### 7. Design Validation

* Purge stale visuals still viewable until reload.
* Empty state: show sample scene thumbnails.
* Error state: `DecodingError` → toast "Invalid file format" (`Kepler-404/README.md:204`).

### 8. Deliverables

* Figma/HTML `templates/index.html`, `static/css/style.css`, `static/js/script.js` — update 4th layer + metrics card.
* Image prompts for PPT flowcharts (as PRD §7).
