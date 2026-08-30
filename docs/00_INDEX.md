# SIH26142 Full Documentation Suite — Index

**Product:** Sentinel-SRM (Kepler-404 Fork) — Deep Learning Based Super Resolution Mapping 10m Sentinel-2 → <4m (3.3m)  
**PS ID:** SIH26142 | **Org:** NTRO | **Theme:** Space Technology (Software) | **Date:** 2026-08-29  
**Base:** `Kepler-404/` Flask+Rasterio 200m→100m TIR mock → extended to N-channel Sentinel-2

| # | Doc | Full Form | Purpose | File |
|---|---|---|---|---|
| 01 | PRD | Product Requirements Document | What to build | `01_PRD.md` |
| 02 | BRD | Business Requirements Document | Business needs & value | `02_BRD.md` |
| 03 | MRD | Market Requirements Document | Market/customer needs | `03_MRD.md` |
| 04 | FRD | Functional Requirements Document | What system must do | `04_FRD.md` |
| 05 | SRS | Software Requirements Specification | Detailed software spec (IEEE 830) | `05_SRS.md` |
| 06 | TRD | Technical Requirements Document | Technical constraints | `06_TRD.md` |
| 07 | DRD | Design Requirements Document | Design/UX requirements | `07_DRD.md` |
| 08 | TDD | Technical Design Document | How to implement | `08_TDD.md` |
| 09 | SDD | Software Design Document | Detailed architecture | `09_SDD.md` |
| 10 | HLD | High-Level Design | Overall system architecture | `10_HLD.md` |
| 11 | LLD | Low-Level Design | Classes/APIs/DB/algorithms | `11_LLD.md` |

### Reading Order

* **Product/Business:** PRD → BRD → MRD
* **Functional:** FRD → SRS
* **Design/Tech:** DRD → TRD → TDD → SDD → HLD → LLD

### Quick Traceability

* Pain/PS: `prompt.txt:4-52` → PRD §1-5, BRD §1-2
* Mock pipeline: `kepler/pipeline.py:32-91`, `transforms.py:34-45`, `io.py:55-142` → TDD/SDD/HLD
* Visual rules: `sih py ppt.txt:8-36` + `SIH2024_IDEA_Presentation_Format.pptx` → DRD §2-4
* Metrics: `prompt.txt:62-66` → PRD §8, SRS §3.6, SDD §6.5

### Status

All 11 docs generated at `docs/SIH26142/`. Next: implement Phase M1 (multi-band I/O + tiling) per TDD §4.

### PPT Blueprint

For 6-slide SIH deck text+image prompts, see previous plan message (Slide 1-6 perfect text). That blueprint aligns 1:1 with PRD/DRD visual system.
