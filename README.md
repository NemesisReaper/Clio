# Siri Bhoovalaya Agentic Decipherment Platform — Days 1, 2 & 3

**Siri Bhoovalaya** (ಸಿರಿಭೂವಲಯ) is a monumental 9th-century CE work by Digambara Jain monk and poet **Kumudendu Muni**. The manuscript encodes multilayered poetic works across multiple languages using 27 × 27 numerical matrices (Chakras) with 729 cells per matrix.

This repository implements **Days 1, 2, and 3** of a seven-day agentic decipherment platform:
- **Day 1**: PDF Intelligence, 27x27 Matrix Extraction, Halegannada Shloka Extraction, and Provenance Knowledge Graph.
- **Day 2**: Core Decipherment Engine, Bandha Traversals, 1953 Ankaphala Substitution, Sandhi-Aware Needleman-Wunsch Alignment, and Orchestrator.
- **Day 3**: Historical Validation, Source-Level Provenance, Decoupled Multi-Dimensional Confidence, and Real-Data Integration.

---

## Architecture Overview

```
                            ┌─────────────────────────────────────────┐
                            │            PDF Ingestion Pipeline       │
                            │  - SHA-256 Content-Addressed Hash       │
                            │  - Scanned vs Native Embedded Detection │
                            │  - Page Classification & 300 DPI Render │
                            └────────────────────┬────────────────────┘
                                                 │
                      ┌──────────────────────────┼──────────────────────────┐
                      ▼                          ▼                          ▼
            ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
            │  27x27 Chakra     │      │   Halegannada     │      │  Historical       │
            │  Matrix Extractor │      │  Shloka Extractor │      │  Knowledge Graph  │
            │  - 729 Cells      │      │  - Verbatim Text  │      │  - 13 Node Types  │
            │  - Kannada/Arabic │      │  - Separate NFC   │      │  - 11 Rel Types   │
            │  - [1, 64] Domain │      │  - Meter & Dandas │      │  - Middle-Out     │
            │  - No Silent Fill │      │  - No Modernizing │      │  - Hypotheses     │
            └─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
                      │                          │                          │
                      └──────────────────────────┼──────────────────────────┘
                                                 │
                                                 ▼
            ┌─────────────────────────────────────────────────────────────────────────┐
            │               DECIPHERMENT ENGINE WITH PROVENANCE GUARDRAILS            │
            │                                                                         │
            │  Chakra ID ──▶ Matrix Retrieval ──▶ Bandha Traversal ──▶ Number Stream  │
            │       │                                                       │         │
            │       ▼                                                       ▼         │
            │  Provenance Registry                                  Ankaphala Engine  │
            │  (Verified / Partial / Experimental)                 (Raw Table Tier 1) │
            │       │                                                       │         │
            │       │                                                       ▼         │
            │       │                                               Ligature Synthesis│
            │       │                                               (Candidate Tier 2)│
            │       │                                                       │         │
            │       ▼                                                       ▼         │
            │  Bilingual Explainer ◀── Halegannada Aligner ◀── Phonetic Stream        │
            │  (Tiers 4 & 5 Interp)    (Candidate Alignment Tier 3)                   │
            │       │                                                                 │
            │       ▼                                                                 │
            │  Decoupled Confidence Breakdown (Evidence & Hypothesis Nodes in Graph)  │
            └─────────────────────────────────────────────────────────────────────────┘
```

---

## Subsystems

### 1. Document Ingestion & Classification (`clio.ingestion`)
- **PyMuPDF & OpenCV**: High-resolution 300 DPI rasterization and image-level morphology grid detection.
- **SHA-256 Deduplication**: Documents are content-addressed; duplicate uploads return existing records.
- **Page Classifier**: Categorizes pages into `NUMERICAL_MATRIX`, `SHLOKA`, `COMMENTARY`, or `MIXED_CONTENT`.

### 2. 27 × 27 Chakra Matrix Extractor (`clio.extractors.matrix_extractor`)
- **Strict 729-cell Geometry**: Enforces 27 rows × 27 columns; rejects malformed grids.
- **Bilingual Numerals**: Supports Kannada numerals (೦, ೧, ೨, ೩, ೪, ೫, ೬, ೭, ೮, ೯) and Arabic digits (0–9).
- **Domain Validation**: Siri Bhoovalaya's primary 64-akshara domain ($1 \le x \le 64$) and extended domain ($1 \le x \le 729$).
- **No Silent Infill**: Missing, illegible, or out-of-domain cells are flagged for manual correction. Cell crops preserved.

### 3. Halegannada Shloka Extractor (`clio.extractors.shloka_extractor`)
- **Fidelity Guarantee**: Preserves raw extracted script and historical vocabulary without modernization.
- **Separate Unicode Normalization**: Verbatim raw text and Unicode NFC normalized forms stored independently.
- **Verse & Danda Segmentation**: Preserves single danda (`|`, `।`), double danda (`||`, `॥`), and stanza markers.

### 4. Provenance-Aware Knowledge Graph (`clio.graph` & `clio.storage.graph_store`)
- **13 Node Types**: `Document`, `Page`, `Chakra`, `Shloka`, `Passage`, `Term`, `Concept`, `Person`, `Work`, `Language`, `Source`, `Evidence`, `Hypothesis`.
- **11 Relationship Types**: `CONTAINS_PAGE`, `CONTAINS_CHAKRA`, `CONTAINS_SHLOKA`, `HAS_PASSAGE`, `CONTAINS_TERM`, `REFERS_TO`, `DISCUSSES`, `HAS_VARIANT`, `ASSOCIATED_WITH`, `SUPPORTED_BY`, `DERIVED_FROM`.
- **Middle-Out Traversal**: Bidirectional expansion from anchor entity with depth limit (default 3, bounds 1–5), relationship filtering, date bounds, and cycle prevention.

### 5. Audited Bandha Traversal Engine (`clio.decipherment.bandhas`)
- **Sarvatobhadra**: Omnidirectional symmetrical traversal (`CONCENTRIC_SPIRAL` with 729 cells and 100% coverage, `SERPENTINE_SYMMETRIC`, `RADIAL_OUTWARD`). Tagged `PARTIALLY_VERIFIED`.
- **Padmabandha**: 8-petal (Ashtadala) lotus petal loops radiating from center pericarp $(13, 13)$. Tagged `PARTIALLY_VERIFIED`.
- **Gomutrika**: Meandering zigzag wave trajectory across adjacent row pairs with period 2 and amplitude 1. Tagged `PARTIALLY_VERIFIED`.
- **Chakrabandha**: Concentric circular wheel rim and 8-radial spokes connecting center $(13, 13)$ to the perimeter. Tagged `PARTIALLY_VERIFIED`.
- **Authenticity Disclaimer**: Coverage statistics reflect geometric completeness only; they do not imply or prove historical correctness.

### 6. Audited Ankaphala Substitution Engine (`clio.decipherment.ankaphala`)
- **Raw Historical Table**: Strictly uncomposed 1-to-1 table from the 1953 Bangalore publication by K. Yellappa Shastri and K. Srikantaiah (`RAW_HISTORICAL_ANKAPHALA_V1`), preserving archaic ಱ (51) and ೞ (52).
- **Independent Normalized Lookup**: `HISTORICAL_ANKAPHALA_V1` provides phonetic descriptions and matra annotations.
- **Substitution Modes**:
  - `substitute_raw()`: Extracts literal unmerged graphemes (Tier 1: `DIRECTLY_EXTRACTED_TEXT`).
  - `substitute()`: Applies algorithmic Indic ligature composition (Tier 2: `ALGORITHMICALLY_GENERATED_CANDIDATE_TEXT`).

### 7. Historical Validation & Source Integration (`clio.validation`)
- **Matrix Dataset Auditing**: Audits dimensions, cell count, missing cells, and frequency distribution across $[1, 64]$.
- **Reference Shloka Auditing**: Validates verse markers, archaic characters, and explicit source associations.
- **Non-Association Guardrail**: Strictly prohibits automatically associating a shloka with a Chakra based on alignment scores alone.
- **Real-Data Availability Inspection**: Checks whether authentic digitized manuscript PDFs are deposited; reports `PENDING_PRIMARY_SOURCE_DEPOSIT` without fabricating synthetic evidence.

### 8. Decoupled Confidence & 5-Tier Output Reporting (`clio.decipherment.explainer`)
- **Decoupled Evidential Dimensions**: Reports matrix completeness, bandha rule verification, ankaphala table verification, reproducibility, alignment quality, historical evidence coverage, and human verification status independently.
- **5 Output Tiers**:
  1. `DIRECTLY_EXTRACTED_TEXT`
  2. `ALGORITHMICALLY_GENERATED_CANDIDATE_TEXT`
  3. `CANDIDATE_ALIGNMENT_WITH_SHLOKA`
  4. `HISTORICALLY_SUPPORTED_INTERPRETATION`
  5. `SPECULATIVE_INTERPRETATION`

---

## REST API Endpoints

### Ingestion & Graph (Day 1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health and connected storage status |
| `POST` | `/api/v1/documents/upload` | Upload PDF (`multipart/form-data`), initiates background job |
| `GET` | `/api/v1/jobs/{job_id}` | Inspect async processing status, progress percentage, errors |
| `GET` | `/api/v1/documents/{document_id}` | Retrieve document metadata and SHA-256 hash |
| `GET` | `/api/v1/documents/{document_id}/pages` | List pages, classifications, and text coordinates |
| `GET` | `/api/v1/documents/{document_id}/chakras` | Retrieve extracted 27×27 matrices and cell grids |
| `GET` | `/api/v1/documents/{document_id}/shlokas` | Retrieve extracted Halegannada shlokas |
| `POST` | `/api/v1/graph/traverse` | Middle-out knowledge graph traversal from anchor entity |

### Decipherment & Provenance (Days 2 & 3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/decipher/bandhas` | List supported Bandhas, mathematical rules, and coverage |
| `GET` | `/api/v1/decipher/tables` | List versioned Ankaphala tables and audit provenance |
| `GET` | `/api/v1/decipher/rules` | List all decipherment rules and verification states |
| `GET` | `/api/v1/decipher/rules/{rule_id}/provenance` | Retrieve bibliographic citations and audit records for a rule |
| `GET` | `/api/v1/sources` | List canonical historical sources and critical editions |
| `GET` | `/api/v1/sources/{source_id}` | Retrieve bibliographic details for a specific historical source |
| `GET` | `/api/v1/validation/real-data-status` | Inspect availability of user-provided primary manuscripts |
| `GET` | `/api/v1/validation/{result_id}` | Retrieve stored validation audit result |
| `POST` | `/api/v1/validation/run` | Execute formal validation check on a rule or stored Chakra |
| `POST` | `/api/v1/decipher` | Run full decipherment orchestrator returning 5-tier bilingual report |

---

## Quickstart

### Option 1: Docker Compose (Full Stack)
```bash
docker compose up --build
```
Services:
- FastAPI Application: `http://localhost:8000`
- PostgreSQL 16: port `5432`
- Neo4j 5 with APOC: ports `7474` (browser) and `7687` (bolt)
- Qdrant Vector DB: port `6333`
- MinIO Object Storage: ports `9000` and `9001` (console)

### Option 2: Local Python Execution
```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate

# 2. Start the FastAPI server
uvicorn clio.api.app:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running the Verification Test Suite

All 47 tests execute in ~9 seconds with 100% pass rate:

```bash
$env:PYTHONPATH = "."
.\.venv\Scripts\pytest.exe -v
```

### Test Suite Breakdown:
- `tests/test_historical_validation.py`: Provenance flagging, experimental bandhas, raw Ankaphala table independence, missing cells rejection, false positive alignment detection, verbatim text preservation, uncertain association guardrails, reproducibility across runs, real-data status reporting, decoupled confidence breakdown, and REST API endpoints.
- `tests/test_ankaphala_engine.py`: 64-akshara table integrity, archaic ಱ and ೞ, substitution, ligature composition, reverse lookup.
- `tests/test_bandha_engine.py`: Sarvatobhadra spiral, Padmabandha 8-petal loops, Gomutrika zigzag, Chakrabandha wheel, registry, coverage calculation.
- `tests/test_reference_alignment.py`: Akshara tokenization, prosodic weights, Sandhi sound-shift equivalence, Needleman-Wunsch alignment with character diffs.
- `tests/test_decipherment_orchestrator.py`: Full end-to-end integration test against published historical Chakra 1 Mangalacharana data.
- `tests/test_decipherment_api.py`: FastAPI routes for listing Bandhas, listing tables, and executing decipherment.
- `tests/test_matrix_extractor.py`: 27×27 matrix geometry, 729 cells, Kannada/Arabic numeral parsing, domain validation, refusal of silent infill.
- `tests/test_shloka_extractor.py`: Halegannada verse segmentation, danda markers, archaic vocabulary preservation, NFC vs raw text separation.
- `tests/test_graph.py`: 13 node types, 11 relationship types, idempotent upsert, hypothesis guardrails, middle-out bidirectional traversal with depth and cycle prevention.
- `tests/test_ingestion.py`: PDF upload, SHA-256 deduplication, 300 DPI rendering, layout classification, end-to-end pipeline.
- `tests/test_api.py`: End-of-day acceptance workflow for ingestion and graph traversal.
