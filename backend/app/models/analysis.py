"""Persisted sketch interpretation and deterministic solver runs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.extensions import db


class SketchAnalysis(db.Model):
    __tablename__ = "sketch_analyses"

    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)
    analysis_type = db.Column(db.String(24), nullable=False, default="sketch")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    status = db.Column(db.String(32), nullable=False, default="pending_review", index=True)
    review_status = db.Column(db.String(24), nullable=False, default="pending_review")

    original_filename = db.Column(db.String(255))
    mime_type = db.Column(db.String(64))
    image_width = db.Column(db.Integer)
    image_height = db.Column(db.Integer)
    image_storage_name = db.Column(db.String(80), unique=True)

    provider = db.Column(db.String(16))
    model_id = db.Column(db.String(128))
    perception_json = db.Column(db.JSON)
    proposal_json = db.Column(db.JSON)
    validation_json = db.Column(db.JSON)
    diagnostics_json = db.Column(db.JSON)
    solver_results_json = db.Column(db.JSON)
    human_geometry_json = db.Column(db.JSON)

    error_code = db.Column(db.String(64))
    error_message = db.Column(db.String(512))

    def to_list_item(self) -> dict:
        return {
            "analysis_id": self.id,
            "created_at": _iso(self.created_at),
            "analysis_type": self.analysis_type,
            "status": self.status,
            "review_status": self.review_status,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "provider": self.provider,
            "model_id": self.model_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "image_url": f"/api/analyses/{self.id}/image" if self.image_storage_name else None,
        }

    def to_detail(self) -> dict:
        return {
            **self.to_list_item(),
            "sketch": {
                "original_filename": self.original_filename,
                "mime_type": self.mime_type,
                "image_width": self.image_width,
                "image_height": self.image_height,
                "image_url": f"/api/analyses/{self.id}/image" if self.image_storage_name else None,
            },
            "perception": self.perception_json,
            "interpretation_proposal": self.proposal_json,
            "validation": self.validation_json,
            "diagnostics": self.diagnostics_json,
            "human_review": {
                "status": self.review_status,
                "geometry": self.human_geometry_json,
            },
            "solver_results": self.solver_results_json,
        }


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
