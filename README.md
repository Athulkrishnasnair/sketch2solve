# Sketch2Solve

**Sketch2Solve** is an engineering sketch-to-truss-analysis application designed to translate hand-drawn structural sketches into validated mathematical models, compute exact internal member forces and support reactions using a deterministic equilibrium solver, and provide transparent engineering diagnostics.

---

## Engineering Philosophy & Architectural Safety Gate

Sketch2Solve is built around a non-negotiable engineering safety principle:
**AI models propose; human engineers review and attest; deterministic mathematics compute.**

```
+---------------------------------------------------------------------------------------------------+
|                                       SKETCH2SOLVE PIPELINE                                       |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ Hand-Drawn Sketch ] (JPEG / PNG / WebP)                                                        |
|           |                                                                                       |
|           +---> [ OpenCV Feature Extraction ] (Adaptive Canny, Probabilistic Hough, Clustering)   |
|           |                                                                                       |
|           +---> [ Multimodal Vision AI ] (Google Gemini / Meta Muse Spark)                         |
|           |                                                                                       |
|           v                                                                                       |
|  [ Candidate Perception Proposal ] (Raw pixel coordinates; STRICTLY UNAPPROVED)                   |
|           |                                                                                       |
|           v                                                                                       |
|  [ Human Geometry Review & Attestation ]                                                          |
|      - Physical unit selection (m, mm, ft / N, kN, lbf)                                           |
|      - Real-world coordinate verification (x-right, y-upward)                                     |
|      - Support and external load definitions                                                      |
|      - Mandatory Reviewer Confirmation (`coordinates_confirmed: true`)                             |
|           |                                                                                       |
|           v                                                                                       |
|  [ Strict Server-Side Schema Validation Gate ] (Version 1.0 JSON Specification)                   |
|           |                                                                                       |
|           v                                                                                       |
|  [ Deterministic NumPy Equilibrium Solver ]                                                       |
|      - Joint equilibrium matrix assembly: [A]{x} = {b}                                            |
|      - SVD condition & rank diagnostics (detects mechanisms, under-/over-determination)           |
|      - Exact direct solution (`numpy.linalg.solve`)                                               |
|      - Equilibrium residual check: ||[A]{x} - {b}||_inf                                           |
|           |                                                                                       |
|           v                                                                                       |
|  [ Analysis Dashboard & Visualizer ] (Tension/Compression color-coding, reaction vectors)          |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

1. **AI Output Is Strictly Advisory**: Multimodal vision models and OpenCV line detectors propose candidate joints, members, supports, and loads in image-pixel space. These proposals are never fed directly to structural analysis.
2. **Mandatory Human-in-the-Loop Review**: A human reviewer must explicitly confirm physical coordinates in chosen units (e.g., meters, millimeters, feet) and define boundary conditions.
3. **Rigid Schema Validation Gate**: All geometry must pass formal schema validation before state transitions to `reviewed`.
4. **Deterministic Structural Mechanics**: Force calculations use pure classical static equilibrium ($\sum F_x = 0$, $\sum F_y = 0$). No neural network or LLM ever calculates structural forces.
5. **Clear Separation of Equilibrium vs. Stability**: An equilibrium solution does not guarantee physical stability, buckling resistance, or structural code compliance.

---

## Quick Start & Installation

### Prerequisites
- **Python**: 3.11, 3.12, or 3.14 (Python 3.11+ recommended)
- **Node.js**: 18+ and **npm**: 9+
- **OS**: Linux, macOS, or Windows (WSL2 recommended)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env` to configure your API keys (optional if only using OpenCV and mock providers):
```ini
INTERPRETATION_PROVIDER=gemini       # Options: gemini or meta
GEMINI_API_KEY=your_gemini_api_key   # Required if provider is gemini
GEMINI_MODEL=gemini-2.5-flash        # Default stable vision model
MODEL_API_KEY=your_meta_api_key      # Required if provider is meta
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174
```

Start the Flask backend server:
```bash
./.venv/bin/python run.py
# Backend runs on http://127.0.0.1:5000
```

### 2. Frontend Setup

In a new terminal window:
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
# Frontend runs on http://localhost:5173
```

Visit `http://localhost:5173` in your browser.

---

## Environment Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `INTERPRETATION_PROVIDER` | Active vision interpretation adapter (`gemini` or `meta`) | `meta` |
| `GEMINI_API_KEY` | Google GenAI API key for Gemini multimodal interpretation | *None* |
| `GEMINI_MODEL` | Gemini vision model identifier | `gemini-2.5-flash` |
| `MODEL_API_KEY` | API key for OpenAI-compatible Meta Muse endpoint | *None* |
| `MODEL_BASE_URL` | Base URL for OpenAI-compatible endpoint | `https://api.openai.com/v1` |
| `DATABASE_URL` | SQLAlchemy connection string for persistent analyses | `sqlite:///<instance>/sketch2solve.sqlite` |
| `CORS_ORIGINS` | Comma-delimited list of allowed frontend origins | `localhost` & `127.0.0.1` on ports 5173, 5174, 4173, 3000 |

*Note: Credentials stay strictly on the backend. The frontend never accesses or receives API keys.*

---

## API Endpoint Reference

### General & Direct Solver
- `GET /api/health`
  - Health check endpoint returning application status.
- `POST /api/analyze`
  - Direct deterministic solver endpoint. Accepts raw Version 1.0 JSON truss schema, executes assembly, SVD diagnostics, and numerical solve. Returns member forces, support reactions, and residual checks.
- `POST /api/analyses/preview` and `POST /api/analyses/<analysis_id>/preview`
  - Non-persistent live calculation and validation preview endpoint. Evaluates draft geometry in real-time without modifying database records or review state. Returns validation issues, structural solvability/diagnostics, and preliminary member forces.

### Sketch Analysis & Lifecycle
- `POST /api/analyses`
  - Multipart upload (`image` file, optional `provider`). Executes OpenCV line detection and multimodal vision AI proposal. Initializes database record in `pending_review` status.
- `GET /api/analyses?page=1&per_page=20`
  - Paginated list of recorded analyses with thumbnail URLs, timestamps, and review statuses.
- `GET /api/analyses/<analysis_id>`
  - Complete analysis record including sketch metadata, OpenCV candidates, AI proposal, human review draft, and solver results.
- `GET /api/analyses/<analysis_id>/image`
  - Streams original sketch image with private, non-caching headers (`Cache-Control: private, no-store`).

### Human Review & Solver Gate
- `GET /api/analyses/<analysis_id>/draft`
  - Returns current human-review geometry draft and original AI proposal.
- `PUT /api/analyses/<analysis_id>/draft`
  - Saves user-corrected geometry draft. Requires `{ geometry: <Version 1.0 Model>, coordinates_confirmed: true }`. Validates schema; updates status to `draft`.
- `POST /api/analyses/<analysis_id>/review`
  - Validates saved draft and advances status to `reviewed`. Prerequisite for solver execution.
- `POST /api/analyses/<analysis_id>/solve`
  - Re-validates reviewed draft and executes deterministic equilibrium solver. On success, transitions record to `submitted` and attaches solver results.

---

## Demonstration Walk-Through

Five representative sketches are included under `backend/evaluation/sketches/`:
- `test1.jpg`: Low-contrast Warren truss pencil sketch.
- `test2.jpg`: Multi-sketch notebook page with 4 candidate trusses.
- `test3.png`: Clean Pratt bridge truss with clear joints and chords.
- `test4.jpg`: Triangular cantilever bracket truss.
- `test5.png`: High-resolution photographed Howe roof truss with dimensions and text.

### Step-by-Step Verification Procedure

1. **Upload Sketch**:
   - Go to `http://localhost:5173` and click **New analysis**.
   - Drag and drop `backend/evaluation/sketches/test4.jpg` (or click to browse).
   - Select your desired vision provider (e.g., Gemini or Meta).
   - Click **Start analysis**.

2. **Inspect Perception & Interpretation**:
   - Once processed, the **Analysis Detail** screen displays the original sketch.
   - Toggle **Detected lines** and **Detected endpoints** to inspect OpenCV candidate features.
   - Inspect the amber **AI interpretation proposal** overlay showing proposed joints, members, supports, and loads. Note that the proposal is marked **UNAPPROVED CANDIDATE**.

3. **Open Human Geometry Review**:
   - Scroll to the **HUMAN-CORRECTED MODEL** section.
   - Click **Correct interpretation** to open the draft editor.
   - Select length unit (`m`) and force unit (`kN`).
   - Replace image-pixel coordinates with verified physical coordinates (e.g. for `test4.jpg`: J1 at `(0, 0)`, J2 at `(0, 2)`, J3 at `(2, 0)`).
   - Configure supports (e.g. Pin at J1, Roller at J2).
   - Configure external loads (e.g. Fx = `0`, Fy = `-10` kN at J3).
   - Check the mandatory confirmation box: *"I confirm these joint coordinates are physical lengths..."*.
   - Click **Save draft**.

4. **Review & Gate**:
   - The editor verifies that the draft conforms to schema version 1.0.
   - The SVG preview independently renders the physical truss geometry, dynamically scaling node radii to the span.
   - Click **Mark as reviewed**. The review status transitions to **REVIEWED**.

5. **Solve Deterministically**:
   - Click **Submit to solver**.
   - Confirm the confirmation dialog.
   - The backend runs `numpy.linalg.solve` on the assembled equilibrium system $\mathbf{A x} = \mathbf{b}$.
   - The **Structural Analysis Results** card displays:
     - Axial forces per member: **Tension** (blue) and **Compression** (red).
     - Support reaction vectors with exact numerical equilibrium.
     - Matrix diagnostics: system dimensions, rank, condition number, and max residual ($||\mathbf{A x} - \mathbf{b}||_\infty < 10^{-12}$).

---

## Running Automated Tests

### Backend Unit & API Tests (109 Tests)
```bash
cd backend
./.venv/bin/python -m unittest discover -s tests -v
# Output: Ran 109 tests in ~1.0s ... OK
```

### Frontend Unit & Contract Tests (3 Tests)
```bash
cd frontend
npm run test:unit
# Output: 3 passed in ~150ms
```

### Frontend Production Build
```bash
cd frontend
npm run build
# Output: vite build passed
```

### Code Hygiene
```bash
git diff --check
# Clean, zero whitespace or conflict warnings
```

---

## Known Limitations

- **Statically Determinate 2D Trusses Only**: The solver computes classical pin-jointed direct equilibrium for square systems ($2j = m + r$). Indeterminate trusses ($2j < m + r$) and mechanisms/unstable trusses ($2j > m + r$) are detected via SVD and rejected with diagnostics.
- **Manual Physical Scaling**: Sketches do not include absolute physical metric references. The human reviewer must enter physical lengths in selected units.
- **Dense/Noisy Sketches**: Hand-drawn sketches with heavy dimensions, title blocks, text, or multiple diagrams can saturate line detection. Dedicated diagram cropping or ROI selection is recommended for dense drawings.
- **Deep Learning Perception (DeepLSD)**: Deep learning wireframe detection was investigated in Phase A. While showing high full-image line recall (62.5% vs OpenCV 18.75%), full VGG-UNet CPU tensor execution caused severe virtual machine memory instability and was frozen for this release.

---

## Engineering Safety & Liability Disclaimer

> [!CAUTION]
> **CRITICAL STRUCTURAL ENGINEERING NOTICE**
> 
> 1. **Equilibrium Does Not Equal Structural Safety**: Numerical convergence of $\mathbf{A x} = \mathbf{b}$ proves only static force balance for an idealized, frictionless, pin-jointed truss under linear elastic assumptions.
> 2. **No Stability or Code Checks**: Sketch2Solve **DOES NOT** perform Euler buckling analysis, member yield checks, connection tear-out calculations, fatigue analysis, dynamic response checks, or structural building code verifications (e.g., AISC 360, Eurocode 3).
> 3. **Not for Construction**: Output from Sketch2Solve must never be used directly for structural fabrication, erection, or building permits without sign-off from a licensed Professional Engineer (PE / SE / Eur Ing).

