"""Safe persistence helpers for analysis records and private image uploads."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.analysis import SketchAnalysis


class AnalysisPersistenceError(RuntimeError):
    """Raised when a record cannot be safely committed."""


def begin_analysis(analysis_type: str) -> SketchAnalysis:
    record = SketchAnalysis(analysis_type=analysis_type)
    db.session.add(record)
    commit_analysis()
    return record


def commit_analysis() -> None:
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise AnalysisPersistenceError("Analysis history is temporarily unavailable.") from error


def save_private_image(record: SketchAnalysis, content: bytes, mime_type: str) -> None:
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[mime_type]
    filename = f"{uuid4().hex}{extension}"
    directory = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    path = (directory / filename).resolve()
    if path.parent != directory:
        raise AnalysisPersistenceError("Image storage path is invalid.")
    with path.open("xb") as image_file:
        image_file.write(content)
    os.chmod(path, 0o600)
    record.image_storage_name = filename
    commit_analysis()


def private_image_path(record: SketchAnalysis) -> Path | None:
    if not record.image_storage_name:
        return None
    directory = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (directory / record.image_storage_name).resolve()
    if path.parent != directory or not path.is_file():
        return None
    return path
