# MRD — Market Requirements Document
## SIH26142 Sentinel Super Resolution

### 1. Market Overview

* **EO Data Market:** Global EO analytics $8B+ (2024), India EO ~$1B with Sentinel-2 as free backbone. 10-30m medium-res dominates due to revisit but lacks fine detail for cadastral/urban/disaster (`prompt.txt:5`).
* **Gap:** Medium→High SR is research (ESRGAN/SwinIR) but no metadata-preserving, spectral-consistent product for Indian EO stack.

### 2. Customer Segments

| Segment | Need | Willingness |
|---|---|---|
| **Primary: Intelligence/Defence (NTRO)** | See 3m buildings/roads without foreign buy | High — mission critical |
| **Secondary: Government (ISRO, NDMA, Urban)** | Panchayat-level flood/urban mapping | High — sovereign |
| **Tertiary: AgTech/Insurance** | Field boundary, damage assessment | Medium — cost saving |
| **Quaternary: Research/GIS firms** | Publishable, QGIS-ready SR | Medium |

### 3. Customer Needs (Validated via PS)

* Must be **physically consistent** (blackbody/NIR truth) not pretty RGB hallucinations (`prompt.txt:38-40`).
* Must handle **multi-band GeoTIFF** (not JPG) or it fails instantly (`prompt.txt:55`).
* Needs **uncertainty** to manage liability (`prompt.txt:42`).

### 4. Competitive Landscape

| Competitor | Type | Price | Gap vs Sentinel-SRM |
|---|---|---|---|
| Topaz Photo AI | Photography upscaler | $199 | Strips CRS+ NIR, not geospatial |
| Intertek HoneyTrace / Pix4D | Vertical SaaS | Enterprise | Not EO SR |
| Chainalysis etc (crypto cluster) | N/A | — | Irrelevant but shows SIH crowding `SIH2026_RESEARCH_AND_ANALYSIS.md:44-53` |
| KSAT Oil Spill (SAR) | Niche foreign | Enterprise | Few players, not India sovereign |
| Research ESRGAN on SpaceNet | Paper/code | Free | Hallucinates, no SAM/uncertainty |

**Positioning:** Only open, sovereign, spectral+uncertainty-aware SR for Sentinel-2 → India airspace.

### 5. Market Requirements

| ID | Market Requirement | Priority |
|---|---|---|
| MR-01 | Open-data trained, no commercial licence per scene | P0 |
| MR-02 | QGIS/ArcGIS compatible COG output | P0 |
| MR-03 | Sub-4m with quantified uncertainty for risk-averse buyers | P0 |
| MR-04 | On-prem deployable (air-gapped ministries) | P0 |
| MR-05 | Web demo for non-GIS users (Kepler Vercel parity) | P1 |

### 6. Market Sizing (Conservative)

* India 3.2M km² × Sentinel-2 revisit 5d = 230M km²/year processed. Even 1% adoption (planners) = 2.3M km² SR demand. At ₹5/km² saved vs commercial, TAM ~₹11Cr/year India Gov alone.

### 7. Go-to-Market (Post-SIH)

* **Phase 1:** SIH win → NTRO internship → beta on one state (Maharashtra) (`SIH2026_About_SIH.md:43-48`).
* **Phase 2:** STAC catalog + Bhuvan integration.
* **Phase 3:** Offer as paid API for private AgTech (freemium 10 tiles/day).

### 8. Differentiation

* Spectral loss + dynamic N-channel (vs RGB-only papers).
* Synthetic degradation solves data moat (SpaceNet 0.5m→10m).
* Uncertainty heatmap is unique selling proposition for defence.

### 9. Customer Validation Plan

* Interview 3 NTRO/ISRO contacts via SIH mentoring (`SIH2026_About_SIH.md:59`).
* Demo on real Sentinel-2 tile, ask: "Would you run NDVI on this?" — yes = pass.
