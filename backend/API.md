# Sketch2Solve — Backend API Documentation

This document describes the HTTP REST API contracts for Sketch2Solve, covering conversational natural-language structural design, visual sketch perception/interpretation, human-in-the-loop review, deterministic finite-element equilibrium solving, and real-time previews.

---

## 1. Core Conventions & Data Contracts

- **Format**: All payloads and responses use standard JSON (`application/json`) unless uploading multipart image streams.
- **Coordinate System**: 2D Cartesian plane where global positive $x$ extends to the right, and global positive $y$ extends upwards.
- **Physical Units**: Declared explicitly in `metadata.units`:
  - Length: `"m"`, `"mm"`, or `"ft"`
  - Force: `"kN"`, `"N"`, or `"lbf"`
- **Truss Request Schema 1.0**:
  ```json
  {
    "schema_version": "1.0",
    "metadata": {
      "name": "Triangular Truss",
      "source": "conversational_ai",
      "units": { "length": "m", "force": "kN" }
    },
    "model": {
      "nodes": [
        { "id": "J1", "x": 0.0, "y": 0.0 },
        { "id": "J2", "x": 6.0, "y": 0.0 },
        { "id": "J3", "x": 3.0, "y": 3.0 }
      ],
      "members": [
        { "id": "M1", "node_i": "J1", "node_j": "J2" },
        { "id": "M2", "node_i": "J2", "node_j": "J3" },
        { "id": "M3", "node_i": "J3", "node_j": "J1" }
      ],
      "supports": [
        { "id": "S1", "node": "J1", "type": "pin" },
        { "id": "S2", "node": "J2", "type": "roller", "direction": "vertical" }
      ],
      "loads": [
        { "id": "L1", "node": "J3", "fx": 0.0, "fy": -10.0 }
      ]
    }
  }
  ```

---

## 2. Conversational Natural-Language Design API

### `POST /api/ai/design`

Processes natural language requests to create new trusses, modify existing canvas snapshots, or explain structural behavior.

#### Request Headers
- `Content-Type: application/json`

#### Request Body
```json
{
  "intent": "create" | "modify" | "explain" | "auto",
  "message": "Add a diagonal between J1 and J3",
  "context": {
    "analysis_id": "optional-uuid",
    "model_revision": 2,
    "model": { /* Schema 1.0 Truss Model Snapshot */ },
    "units": { "length": "m", "force": "kN" },
    "selected_element": { "type": "member", "id": "M2" },
    "diagnostics": { /* System diagnostics */ },
    "solver_results": { /* Active solver results */ },
    "provider": "meta"
  }
}
```

#### Supported Intents

1. **CREATE (`intent: "create"`)**:
   - Synthesizes a new complete truss proposal matching Schema 1.0 from natural language.
   - Supports parameter extraction (span, height, panel count, support conditions, applied loads, units).
   - Standard topologies: Triangular roof truss, Warren truss, Pratt truss, Howe truss.
   - If essential parameters are missing or ambiguous (e.g. "Create a truss"), returns `status: "needs_clarification"` with structured `clarification_questions`.
   - Never mutates or creates database records automatically.

2. **MODIFY (`intent: "modify"`)**:
   - Takes the active editor canvas snapshot from `context.model`.
   - Modifies **only** what the user requested, preserving all unaffected geometry, loads, and supports.
   - Generates discrete, restricted operations:
     - `add_joint`, `update_joint`, `remove_joint`
     - `add_member`, `update_member`, `remove_member`
     - `add_support`, `update_support`, `remove_support`
     - `add_load`, `update_load`, `remove_load`
   - Validates operations against duplicate IDs, unknown node references, coincident nodes, and self-connected members.
   - Runs deterministic geometry validation and predicts solver status.

3. **EXPLAIN (`intent: "explain"`)**:
   - Formulates concise structural engineering explanations grounded strictly in actual geometry.
   - Explains equilibrium equation balance ($2j$ vs $m + r$), degree of determinacy, connected components, and boundary conditions.
   - When solver results are provided, identifies tension, compression, and zero-force members.
   - When solver results are absent, explicitly disclaims that verified numerical forces are unavailable.

#### Response Body (HTTP 200)
```json
{
  "intent": "modify",
  "status": "proposed",
  "proposal_id": "3b29fcf958f84fa18c504a5e305e9112",
  "base_revision": 2,
  "explanation": "Added member M4 connecting joint J1 and joint J3. All other geometry remains unchanged.",
  "proposed_model": { /* Complete modified Schema 1.0 model */ },
  "operations": [
    {
      "op": "add_member",
      "id": "M4",
      "node_i": "J1",
      "node_j": "J3"
    }
  ],
  "affected_elements": {
    "nodes": ["J1", "J3"],
    "members": ["M4"],
    "supports": [],
    "loads": []
  },
  "clarification_questions": [],
  "validation": {
    "is_valid": true,
    "issues": []
  },
  "predicted_diagnostics": {
    "status": "solvable",
    "category": "SQUARE_FULL_RANK",
    "equation_count": 6,
    "unknown_count": 6,
    "rank": 6
  },
  "warnings": []
}
```

#### Security, Input Sanitization & Guardrails
- **Empty Message**: Rejects whitespace or empty prompts with HTTP 400 `EMPTY_MESSAGE`.
- **Length Caps**: Messages > 2000 characters rejected with HTTP 400 `MESSAGE_TOO_LONG`.
- **Complexity Caps**: Context models with > 500 nodes/members/supports/loads rejected with HTTP 400 `CONTEXT_TOO_LARGE`.
- **Numeric Limits**: Rejects non-finite numbers (`NaN`, `Infinity`) or coordinates $> 10^6$ with HTTP 400 `NON_FINITE_NUMERIC_VALUE`.
- **Domain Guardrails**: Non-structural requests (e.g. code generation, shell execution, prompt injection, hacking attempts) are blocked with HTTP 400:
  ```json
  {
    "error": "OUT_OF_SCOPE",
    "message": "I can help create, modify or explain truss structures. Describe the structural design you want."
  }
  ```

---

### `POST /api/ai/design/apply`

Atomically approves and applies a design proposal with revision conflict checking.

#### Request Body
```json
{
  "proposal_id": "3b29fcf958f84fa18c504a5e305e9112",
  "analysis_id": "optional-analysis-uuid",
  "base_revision": 2,
  "proposed_model": { /* Complete Schema 1.0 Model */ }
}
```

#### Behavior & Revision Gating
1. **Deterministic Geometry Validation**: The proposed model is independently validated. If invalid, returns HTTP 422 `INVALID_PROPOSAL_GEOMETRY`.
2. **Revision Conflict Protection**:
   - If `analysis_id` is supplied: Compares `base_revision` against the database record's current revision.
   - If `base_revision != current_revision`, rejects with HTTP 409 `REVISION_CONFLICT`.
   - On match, updates `record.human_geometry_json = proposed_model`, increments revision to `current_revision + 1`, and sets status to `"draft"`.
   - If the analysis was already submitted to the solver (`review_status == "submitted"`), rejects with HTTP 409 `DRAFT_ALREADY_SUBMITTED`.
3. **Atomic Commit & Rollback**: Persistence failures trigger immediate rollback and return HTTP 503 `ANALYSIS_HISTORY_UNAVAILABLE`.

#### Response Body (HTTP 200)
```json
{
  "status": "applied",
  "proposal_id": "3b29fcf958f84fa18c504a5e305e9112",
  "analysis_id": "analysis-uuid",
  "model_revision": 3,
  "model": { /* Applied Schema 1.0 Model */ },
  "validation": { "status": "valid", "issues": [] },
  "message": "Design proposal applied and saved successfully."
}
```

---

### `POST /api/ai/design/reject`

Acknowledges rejection or cancellation of a design proposal without mutating database or canvas state.

#### Request Body
```json
{
  "proposal_id": "3b29fcf958f84fa18c504a5e305e9112",
  "analysis_id": "optional-analysis-uuid",
  "base_revision": 2
}
```

#### Response Body (HTTP 200)
```json
{
  "status": "rejected",
  "proposal_id": "3b29fcf958f84fa18c504a5e305e9112",
  "message": "Design proposal was rejected. Original geometry was preserved without changes."
}
```

---

## 3. Real-Time Geometry & Calculation Preview

### `POST /api/analyses/preview`
### `POST /api/analyses/<analysis_id>/preview`

Evaluates geometry in real time without persisting state or approving drafts.

#### Request Body
```json
{
  "geometry": { /* Schema 1.0 Truss Model */ }
}
```

#### Response Body (HTTP 200)
```json
{
  "is_valid": true,
  "validation": {
    "status": "valid",
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "solvability": {
    "status": "solvable" | "unsolvable" | "invalid_geometry",
    "category": "SQUARE_FULL_RANK" | "UNDERDETERMINED" | "OVERDETERMINED",
    "message": "Truss is statically determinate and in static equilibrium.",
    "equation_count": 6,
    "unknown_count": 6,
    "rank": 6,
    "condition_number": 20.35
  },
  "solver_results": {
    "status": "SOLVED",
    "member_forces": { "M1": 3.333333, "M2": -6.009252, "M3": -6.009252 },
    "member_states": { "M1": "tension", "M2": "compression", "M3": "compression" },
    "support_reactions": {
      "S1": { "fx": 0.0, "fy": 5.0 },
      "S2": { "fy": 5.0 }
    },
    "max_equilibrium_residual": 4.44e-16,
    "residual_tolerance": 1.0e-9,
    "condition_number": 20.35,
    "force_unit": "kN",
    "length_unit": "m"
  }
}
```

---

## 4. Visual Sketch Perception & Analysis Pipeline

- `POST /api/analyses`: Multipart file upload (`image`), executes OpenCV line detection and Meta Model API interpretation.
- `GET /api/analyses?page=1&per_page=20`: Paginated history of analyses.
- `GET /api/analyses/<analysis_id>`: Returns full analysis detail, sketch metadata, perception candidates, proposal, human draft, and solver results.
- `GET /api/analyses/<analysis_id>/image`: Securely streams the private original sketch image.
- `GET /api/analyses/<analysis_id>/draft`: Retrieves the reviewer's editable draft geometry.
- `PUT /api/analyses/<analysis_id>/draft`: Saves reviewer's corrected geometry with mandatory `coordinates_confirmed: true` attestation.
- `POST /api/analyses/<analysis_id>/review`: Revalidates draft and transitions status to `"reviewed"`.
- `POST /api/analyses/<analysis_id>/solve`: Runs direct numerical NumPy solver on the reviewed draft.

---

## 5. Direct Numerical Solver & Health

- `POST /api/analyze`: Direct JSON API for direct equilibrium solver without sketch persistence.
- `GET /api/health`: Healthcheck endpoint (`{"status": "ok", "application": "Sketch2Solve"}`).

