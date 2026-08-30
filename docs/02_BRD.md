# BRD — Business Requirements Document
## SIH26142 NTRO Super Resolution Mapping

**Business Owner:** NTRO (National Technical Research Organisation) | **Product:** Sentinel-SRM | **Theme:** Space Technology (Software)

### 1. Business Need
India’s Earth Observation free data (Sentinel-2 10m, frequent revisit) is under-utilized for fine-scale analysis (roads, buildings, field boundaries, localized damage) because structural detail is insufficient (`prompt.txt:5-7`). Procuring commercial <1m imagery (Maxar/Planet) costs thousands per scene and has low revisit. NTRO, ISRO, disaster authorities need a sovereign, cost-free method to extract `<4m` value from existing EO assets.

### 2. Business Objectives

| Objective | KPI | Target |
|---|---|---|
| Reduce dependency on commercial high-res procurement | Cost per analyzed km² | ↓70% vs Maxar scene price |
| Enable sub-pixel decision confidence | Hallucination rate | <2% false structures (via uncertainty) |
| Preserve scientific utility | NDVI correlation (post-SR vs pre-SR) | r >0.98 |
| Deployment sovereignty | On-prem inference (air-gapped) | Works offline, no foreign API |

### 3. Business Scope

**In Scope:** Business case for SIH internal hackathon → NTRO on-prem pipeline for Sentinel-2 over Indian airspace (`prompt.txt:33` national pipeline).  
**Out of Scope:** Satellite manufacturing, direct tasking, raw downlink infrastructure.

### 4. Stakeholders & Value

| Stakeholder | Business Value |
|---|---|
| NTRO / MHA | Intelligence advantage, faster disaster assessment |
| ISRO/SAC | Maximizes ROI on open EO data |
| Ministry of Rural Development / Urban | Panchayat-level mapping without new surveys |
| AgTech (Ecozen, DeHaat adjacency) | Field-boundary pricing without drone flights |
| Business (Product Team) | SIH win → internship → ministry deployment (`SIH2026_About_SIH.md:43-48` 5-step adoption) |

### 5. Business Requirements

| ID | Business Requirement | Priority |
|---|---|---|
| BR-01 | Provide 10m→<4m enhancement that is scientifically reliable (spectral + georeference truth) | P0 |
| BR-02 | Must quantify uncertainty per pixel to avoid fatal tactical errors (`prompt.txt:106`) | P0 |
| BR-03 | Operate on open data (Sentinel-2, SpaceNet synthetic) — no proprietary data dependency | P0 |
| BR-04 | Support QGIS/ArcGIS workflows (COG GeoTIFF + affine preservation `kepler/pipeline.py:87-91`) | P0 |
| BR-05 | Cost model: free at inference, training via academic GPU (Colab Pro) | P1 |
| BR-06 | Compliance: No data exfiltration, on-prem deployable (mirrors `Kepler-404` local Flask) | P0 |

### 6. Business Rules

* BR-R1: No hallucinated structures without high uncertainty flag — verifier veto (`prompt.txt:108` answer).
* BR-R2: Spectral signature (SAM) must remain within 3° to keep agriculture/disaster indices valid.
* BR-R3: File output must retain EPSG and be overlay-accurate (`SIH2026_RESEARCH_AND_ANALYSIS.md:65` geospatial fidelity).

### 7. Market & Competitive Context (BRD Lens)

* Direct: None sovereign for Sentinel-2→<4m in India (SR research exists but no operational NTRO-grade product `SIH2026_RESEARCH_AND_ANALYSIS.md:354`).
* Adjacent: Topaz Labs (photography, strips metadata `prompt.txt:38`), Pix4D (drone), KSAT/EMSA (oil spill, not SR).
* Advantage: Sovereign + spectral-aware + uncertainty — enterprise incumbents are foreign/expensive.

### 8. Cost-Benefit (High Level)

* **Cost:** Training 1× ~40 GPU-hours (Colab Pro ~₹2k), infra Flask+Rasterio open-source.
* **Benefit:** Per 10k km², saves ~₹5-10L vs commercial procurement; reuse across ministries (DRDO, MoES).

### 9. Risks (Business)

| Risk | Mitigation |
|---|---|
| Model hallucinates → wrong intel | Uncertainty heatmap + human-in-loop |
| No real paired data | Synthetic degradation business-approved (`prompt.txt:103`) |
| Judge tests NIR/NDVI and fails | N-channel + SAM loss (`prompt.txt:112`) |

### 10. Acceptance Criteria (Business)

* NTRO evaluator can run NDVI on output and get comparable result to input.
* Demo on real Sentinel-2 tile completes and overlay matches Google Earth within 1 pixel.
