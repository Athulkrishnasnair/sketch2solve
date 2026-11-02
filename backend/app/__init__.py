from dataclasses import asdict
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from app.extensions import db
from app.models.analysis import SketchAnalysis
from app.routes.analyses import analyses_api
from app.services.analysis_persistence import AnalysisPersistenceError, begin_analysis, commit_analysis
from app.services.perception import MAX_IMAGE_BYTES
from app.services.solver import (
    SolverAssemblyError,
    assemble_equilibrium_system,
    diagnose_equilibrium_system,
    solve_equilibrium_system,
)
from app.services.validation import validate_truss_request


def create_app(test_config=None):
    app = Flask(__name__)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    os.chmod(app.instance_path, 0o700)
    default_database = Path(app.instance_path) / "sketch2solve.sqlite"
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{default_database}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(Path(app.instance_path) / "uploads"),
        MAX_ANALYSIS_IMAGE_BYTES=MAX_IMAGE_BYTES,
        MAX_CONTENT_LENGTH=MAX_IMAGE_BYTES + 256 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    # Cors config
    configured_origins = os.environ.get("CORS_ORIGINS")
    allowed_origins = (
        [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
        if configured_origins
        else [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}}
    )
    app.register_blueprint(analyses_api)

    # create_all is additive: it creates this table when absent and leaves
    # existing tables/rows intact. No automatic drop, reset, or migration runs.
    with app.app_context():
        db.create_all()

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "application": "Sketch2Solve",
        }

    @app.post("/api/analyze")
    def analyze():
        try:
            record = begin_analysis("solver")
        except AnalysisPersistenceError:
            return _history_unavailable()

        if not request.is_json:
            return _analysis_failure(record, {
                "status": "FAILED",
                "error_code": "INVALID_JSON",
                "message": "Request must contain a JSON body.",
            }, 400)
        try:
            payload = request.get_json()
        except BadRequest:
            return _analysis_failure(record, {
                "status": "FAILED",
                "error_code": "MALFORMED_JSON",
                "message": "Request body contains malformed JSON.",
            }, 400)

        validation = validate_truss_request(payload)
        if not validation.is_valid:
            record.validation_json = {
                "status": "invalid",
                "issues": [asdict(issue) for issue in validation.errors],
            }
            return _analysis_failure(record, {
                "status": "FAILED",
                "error_code": "VALIDATION_FAILED",
                "message": "Truss request failed validation.",
                "validation_issues": [asdict(issue) for issue in validation.errors],
            }, 422)

        record.validation_json = {"status": "valid", "issues": []}
        model = validation.model
        try:
            system = assemble_equilibrium_system(model)
        except SolverAssemblyError as error:
            return _analysis_failure(record, {
                "status": "FAILED",
                "error_code": error.code,
                "message": error.message,
                "diagnostics": None,
            }, 422)

        diagnostics = diagnose_equilibrium_system(system)
        diagnostic_data = _diagnostics_json(diagnostics)
        record.diagnostics_json = diagnostic_data
        solution = solve_equilibrium_system(system)
        if solution.status != "SOLVED":
            return _analysis_failure(record, {
                "status": "FAILED",
                "error_code": solution.error_code or "ANALYSIS_FAILED",
                "message": solution.message or "The equilibrium system could not be solved.",
                "diagnostics": diagnostic_data,
            }, 422)

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
        record.solver_results_json = result_data
        try:
            commit_analysis()
        except AnalysisPersistenceError:
            return _history_unavailable(record.id)
        return jsonify({
            "analysis_id": record.id,
            "status": "SOLVED",
            "schema_version": model.schema_version,
            "units": {"length": model.units.length, "force": model.units.force},
            "diagnostics": diagnostic_data,
            "results": result_data,
            "warnings": [],
        }), 200

    return app


def _diagnostics_json(diagnostics):
    """Convert diagnostic tuples and NumPy-derived values to JSON primitives."""
    data = asdict(diagnostics)
    if data["matrix_shape"] is not None:
        data["matrix_shape"] = list(data["matrix_shape"])
    return data


def _analysis_failure(record: SketchAnalysis, body: dict, status_code: int):
    record.status = "failed"
    record.error_code = str(body.get("error_code", "ANALYSIS_FAILED"))[:64]
    record.error_message = str(body.get("message", "Analysis failed."))[:512]
    try:
        commit_analysis()
    except AnalysisPersistenceError:
        return _history_unavailable(record.id)
    return jsonify({"analysis_id": record.id, **body}), status_code


def _history_unavailable(analysis_id=None):
    try:
        db.session.rollback()
    except Exception:
        pass
    body = {
        "error_code": "ANALYSIS_HISTORY_UNAVAILABLE",
        "message": "Analysis history is temporarily unavailable.",
    }
    if analysis_id:
        body["analysis_id"] = analysis_id
    return jsonify(body), 503
