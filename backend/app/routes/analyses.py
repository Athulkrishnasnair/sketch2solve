"""History and upload routes for persisted sketch analyses."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.analysis import SketchAnalysis
from app.services import gemini_interpretation, interpretation_provider, muse_interpretation
from app.services.analysis_persistence import (
    AnalysisPersistenceError,
    begin_analysis,
    commit_analysis,
    private_image_path,
    save_private_image,
)
from app.services.perception import MAX_IMAGE_BYTES, PerceptionInputError, detect_candidate_geometry
from app.services.solver import SolverAssemblyError, assemble_equilibrium_system, diagnose_equilibrium_system, solve_equilibrium_system
from app.services.truss_preview import evaluate_truss_preview
from app.services.validation import validate_truss_request


analyses_api = Blueprint("analyses_api", __name__)
_MIME_BY_SIGNATURE = (
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
)


@analyses_api.post("/api/analyses")
def create_sketch_analysis():
    """Persist and interpret an uploaded image; output remains pending review."""
    try:
        record = begin_analysis("sketch")
    except AnalysisPersistenceError:
        return _history_unavailable()

    try:
        uploaded = request.files.get("image")
    except RequestEntityTooLarge:
        return _fail(record, "IMAGE_TOO_LARGE", "Uploaded image exceeds the configured size limit.", 413)
    if uploaded is None or not uploaded.filename:
        return _fail(record, "MISSING_IMAGE", "Multipart field 'image' is required.", 400)

    try:
        max_image_bytes = current_app.config.get("MAX_ANALYSIS_IMAGE_BYTES", MAX_IMAGE_BYTES)
        content = uploaded.stream.read(max_image_bytes + 1)
    except RequestEntityTooLarge:
        return _fail(record, "IMAGE_TOO_LARGE", "Uploaded image exceeds the configured size limit.", 413)
    if not content:
        return _fail(record, "INVALID_IMAGE", "Uploaded image is empty.", 400)
    if len(content) > current_app.config.get("MAX_ANALYSIS_IMAGE_BYTES", MAX_IMAGE_BYTES):
        return _fail(record, "IMAGE_TOO_LARGE", "Uploaded image exceeds the configured size limit.", 413)

    mime_type = _sniff_image_mime(content)
    if mime_type is None:
        return _fail(record, "UNSUPPORTED_IMAGE_TYPE", "Only valid JPEG, PNG, and WebP images are accepted.", 415)

    # The multipart MIME and filename extension are client supplied metadata.
    # Decode the bytes before storing or sending them to a provider, and use the
    # format identified from the encoded content for persistence and requests.
    try:
        perception = detect_candidate_geometry(content)
    except PerceptionInputError as error:
        return _fail(record, "INVALID_IMAGE", str(error), 422)

    filename = secure_filename(Path(uploaded.filename).name)[:255] or f"sketch{_extension_for_mime(mime_type)}"
    record.original_filename = filename
    record.mime_type = mime_type
    record.image_width = perception.image_width
    record.image_height = perception.image_height
    record.perception_json = perception.to_dict()
    record.validation_json = {
        "status": "not_performed",
        "message": "Candidate interpretations are not converted to a solver model until human review.",
    }

    try:
        provider = interpretation_provider.resolve_provider(request.form.get("provider"))
        model_id = interpretation_provider.model_id_for(provider)
        record.provider = provider
        record.model_id = _safe_model_id(model_id, provider)
        save_private_image(record, content, mime_type)
    except ValueError:
        return _fail(record, "INVALID_PROVIDER", "Configured interpretation provider must be 'meta' or 'gemini'.", 400)
    except (OSError, AnalysisPersistenceError):
        return _fail(record, "IMAGE_STORAGE_FAILED", "Uploaded image could not be stored safely.", 503)

    try:
        commit_analysis()

        proposal = interpretation_provider.interpret_truss_sketch(
            content,
            provider=provider,
            mime_type=mime_type,
        )
        record.proposal_json = proposal.to_dict()
        record.status = "pending_review"
        record.review_status = "pending_review"
        commit_analysis()
    except (gemini_interpretation.GeminiInterpretationError, muse_interpretation.MuseInterpretationError) as error:
        status_code = _provider_http_status(error.code)
        return _fail(record, error.code, str(error), status_code)
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    except Exception:
        return _fail(record, "ANALYSIS_FAILED", "Sketch analysis could not be completed.", 500)

    response = record.to_detail()
    return jsonify(response), 201


@analyses_api.get("/api/analyses")
def list_analyses():
    try:
        page = _positive_int(request.args.get("page", "1"), "page")
        per_page = min(_positive_int(request.args.get("per_page", "20"), "per_page"), 100)
    except ValueError as error:
        return jsonify({"error_code": "INVALID_PAGINATION", "message": str(error)}), 400
    try:
        query = SketchAnalysis.query.order_by(SketchAnalysis.created_at.desc(), SketchAnalysis.id.desc())
        total = query.count()
        records = query.offset((page - 1) * per_page).limit(per_page).all()
    except Exception:
        return _history_unavailable()
    return jsonify({
        "items": [record.to_list_item() for record in records],
        "page": page,
        "per_page": per_page,
        "total": total,
    })


@analyses_api.get("/api/analyses/<analysis_id>")
def get_analysis(analysis_id: str):
    try:
        record = db.session.get(SketchAnalysis, analysis_id)
    except Exception:
        return _history_unavailable()
    if record is None:
        return _not_found()
    return jsonify(record.to_detail())


@analyses_api.get("/api/analyses/<analysis_id>/draft")
def get_analysis_draft(analysis_id: str):
    record, error = _review_record(analysis_id)
    if error:
        return error
    return jsonify({
        "analysis_id": record.id,
        "draft": record.human_geometry_json,
        "original_proposal": record.proposal_json,
        "review_status": record.review_status,
        "validation": record.validation_json,
    })


@analyses_api.post("/api/analyses/preview")
def preview_truss_geometry():
    """Non-persistent preview validation and equilibrium calculations."""
    body, error = _json_body()
    if error:
        return error
    result = evaluate_truss_preview(body)
    return jsonify(result), 200


@analyses_api.post("/api/analyses/<analysis_id>/preview")
def preview_analysis_geometry(analysis_id: str):
    """Non-persistent preview calculation for a specific analysis context."""
    body, error = _json_body()
    if error:
        return error
    result = evaluate_truss_preview(body)
    return jsonify(result), 200


@analyses_api.put("/api/analyses/<analysis_id>/draft")
def save_analysis_draft(analysis_id: str):
    record, error = _review_record(analysis_id)
    if error:
        return error
    if record.review_status == "submitted":
        return jsonify({"error_code": "DRAFT_ALREADY_SUBMITTED", "message": "This reviewed geometry was already submitted to the solver."}), 409
    body, error = _json_body()
    if error:
        return error
    if not isinstance(body, dict) or set(body) != {"geometry", "coordinates_confirmed"}:
        return jsonify({"error_code": "INVALID_DRAFT_REQUEST", "message": "Request must contain geometry and coordinates_confirmed fields."}), 400
    if body["coordinates_confirmed"] is not True:
        return jsonify({"error_code": "COORDINATES_NOT_CONFIRMED", "message": "Confirm that joint coordinates are physical lengths in the selected units before saving."}), 422
    payload = body["geometry"]
    validation = validate_truss_request(payload)
    if not validation.is_valid:
        return _draft_validation_failure(validation.errors)

    record.human_geometry_json = payload
    record.review_status = "draft"
    record.status = "pending_review"
    record.validation_json = {"status": "valid", "issues": []}
    record.diagnostics_json = None
    record.solver_results_json = None
    record.error_code = None
    record.error_message = None
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify({
        "analysis_id": record.id,
        "draft": record.human_geometry_json,
        "review_status": record.review_status,
        "validation": record.validation_json,
    }), 200


@analyses_api.post("/api/analyses/<analysis_id>/review")
def review_analysis_draft(analysis_id: str):
    record, error = _review_record(analysis_id)
    if error:
        return error
    if record.review_status == "submitted":
        return jsonify({"error_code": "DRAFT_ALREADY_SUBMITTED", "message": "This reviewed geometry was already submitted to the solver."}), 409
    if record.human_geometry_json is None:
        return jsonify({"error_code": "DRAFT_REQUIRED", "message": "Save a corrected draft before marking it reviewed."}), 409
    validation = validate_truss_request(record.human_geometry_json)
    if not validation.is_valid:
        record.validation_json = {"status": "invalid", "issues": [asdict(issue) for issue in validation.errors]}
        try:
            commit_analysis()
        except AnalysisPersistenceError:
            return _history_unavailable(record.id)
        return _draft_validation_failure(validation.errors)

    record.review_status = "reviewed"
    record.status = "reviewed"
    record.error_code = None
    record.error_message = None
    record.validation_json = {"status": "valid", "issues": []}
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify(record.to_detail())


@analyses_api.post("/api/analyses/<analysis_id>/solve")
def solve_reviewed_analysis(analysis_id: str):
    record, error = _review_record(analysis_id)
    if error:
        return error
    if record.review_status != "reviewed" or record.human_geometry_json is None:
        return jsonify({"error_code": "REVIEW_REQUIRED", "message": "Save and explicitly mark a valid geometry draft as reviewed before solving."}), 409
    validation = validate_truss_request(record.human_geometry_json)
    if not validation.is_valid:
        record.validation_json = {"status": "invalid", "issues": [asdict(issue) for issue in validation.errors]}
        try:
            commit_analysis()
        except AnalysisPersistenceError:
            return _history_unavailable(record.id)
        return _draft_validation_failure(validation.errors)

    model = validation.model
    try:
        system = assemble_equilibrium_system(model)
    except SolverAssemblyError as solver_error:
        return _solver_failure(record, solver_error.code, solver_error.message)

    diagnostics = diagnose_equilibrium_system(system)
    diagnostic_data = asdict(diagnostics)
    if diagnostic_data["matrix_shape"] is not None:
        diagnostic_data["matrix_shape"] = list(diagnostic_data["matrix_shape"])
    solution = solve_equilibrium_system(system)
    record.diagnostics_json = diagnostic_data
    if solution.status != "SOLVED":
        return _solver_failure(
            record,
            solution.error_code or "ANALYSIS_FAILED",
            solution.message or "The equilibrium system could not be solved.",
            diagnostic_data,
        )

    reactions = {}
    for (support_id, axis), value in solution.support_reactions.items():
        reactions.setdefault(support_id, {})[axis] = value
    result_data = {
        "member_forces": solution.member_forces,
        "support_reactions": reactions,
        "max_equilibrium_residual": solution.max_residual,
        "residual_tolerance": solution.residual_tolerance,
        "force_unit": solution.force_unit,
    }
    record.status = "solved"
    record.review_status = "submitted"
    record.error_code = None
    record.error_message = None
    record.validation_json = {"status": "valid", "issues": []}
    record.solver_results_json = result_data
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify({
        "analysis_id": record.id,
        "status": "SOLVED",
        "diagnostics": diagnostic_data,
        "results": result_data,
        "warning": "A numerical solution does not establish physical stability or engineering suitability.",
    }), 200


@analyses_api.get("/api/analyses/<analysis_id>/image")
def get_analysis_image(analysis_id: str):
    try:
        record = db.session.get(SketchAnalysis, analysis_id)
        path = private_image_path(record) if record is not None else None
    except Exception:
        return _history_unavailable()
    if record is None or path is None:
        return _not_found()
    response = send_file(
        path,
        mimetype=record.mime_type,
        as_attachment=False,
        download_name=f"sketch{_extension_for_mime(record.mime_type)}",
        conditional=True,
        max_age=0,
    )
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _sniff_image_mime(content: bytes) -> str | None:
    for signature, mime_type, _extension in _MIME_BY_SIGNATURE:
        if content.startswith(signature):
            return mime_type
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def _review_record(analysis_id: str):
    try:
        record = db.session.get(SketchAnalysis, analysis_id)
    except Exception:
        return None, _history_unavailable(analysis_id)
    if record is None:
        return None, _not_found()
    if record.analysis_type != "sketch" or record.proposal_json is None:
        return None, (jsonify({
            "error_code": "REVIEW_UNAVAILABLE",
            "message": "This analysis has no saved sketch proposal to review.",
        }), 409)
    return record, None


def _json_body():
    if not request.is_json:
        return None, (jsonify({"error_code": "INVALID_JSON", "message": "Request must contain a JSON body."}), 400)
    try:
        payload = request.get_json()
    except BadRequest:
        return None, (jsonify({"error_code": "MALFORMED_JSON", "message": "Request body contains malformed JSON."}), 400)
    return payload, None


def _draft_validation_failure(issues):
    return jsonify({
        "error_code": "VALIDATION_FAILED",
        "message": "Correct the listed geometry issues before saving or reviewing this draft.",
        "validation_issues": [asdict(issue) for issue in issues],
    }), 422


def _solver_failure(record: SketchAnalysis, code: str, message: str, diagnostics: dict | None = None):
    record.status = "failed"
    record.error_code = str(code)[:64]
    record.error_message = str(message)[:512]
    if diagnostics is not None:
        record.diagnostics_json = diagnostics
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify({
        "analysis_id": record.id,
        "status": "FAILED",
        "error_code": record.error_code,
        "message": record.error_message,
        "diagnostics": record.diagnostics_json,
    }), 422


def _extension_for_mime(mime_type: str | None) -> str:
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(mime_type, ".img")


def _provider_http_status(code: str) -> int:
    if code in {"MISSING_GEMINI_API_KEY", "MISSING_MODEL_API_KEY"}:
        return 503
    if code.endswith("_AUTHENTICATION_FAILED"):
        return 502
    if code.endswith("_RATE_LIMITED"):
        return 429
    if code.endswith("_TIMEOUT"):
        return 504
    if code.endswith("_NETWORK_ERROR"):
        return 503
    if code.endswith("_INVALID_MODEL"):
        return 500
    return 502


def _safe_model_id(value: str, provider: str) -> str:
    # Avoid reflecting arbitrary configuration content through history APIs.
    expected_prefix = "gemini-" if provider == "gemini" else "muse-"
    if (
        len(value) > 128
        or not value.startswith(expected_prefix)
        or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-" for ch in value)
    ):
        return "configured-model"
    return value


def _positive_int(value: str, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be a positive integer.") from error
    if result < 1:
        raise ValueError(f"{field} must be a positive integer.")
    return result


def _fail(record: SketchAnalysis, code: str, message: str, status_code: int):
    record.status = "failed"
    record.error_code = code
    record.error_message = message[:512]
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify({
        "analysis_id": record.id,
        "status": "failed",
        "error_code": code,
        "message": message,
    }), status_code


def _history_unavailable(analysis_id: str | None = None):
    try:
        db.session.rollback()
    except Exception:
        pass
    body = {"error_code": "ANALYSIS_HISTORY_UNAVAILABLE", "message": "Analysis history is temporarily unavailable."}
    if analysis_id:
        body["analysis_id"] = analysis_id
    return jsonify(body), 503


def _not_found():
    return jsonify({"error_code": "ANALYSIS_NOT_FOUND", "message": "Analysis was not found."}), 404
