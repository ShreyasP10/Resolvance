"""Routes per UPDATED_SIH26142_FULL_v2.md:12 LLD POST /api/infer"""
from __future__ import annotations
from pathlib import Path
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from core.exceptions import DecodingError, ProcessingError

bp=Blueprint("api", __name__)

@bp.route("/api/infer", methods=["POST"])
def infer():
    settings=current_app.config["SENTINEL_SETTINGS"]
    pipeline=current_app.config["SENTINEL_PIPELINE"]
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    f=request.files["file"]
    if f.filename=="": return jsonify({"success": False, "error": "No selected file"}), 400
    if not settings.is_allowed(f.filename):
        return jsonify({"success": False, "error": "Invalid file format. Please upload a .tif, .tiff, .png, .jpg, or .jpeg file."}), 415
    job_id=uuid.uuid4().hex
    ext=Path(f.filename).suffix.lower()
    up_path=settings.upload_dir / f"{job_id}{ext}"
    f.save(str(up_path))
    try:
        result=pipeline.run(up_path, job_id=job_id)
        return jsonify(result.to_dict()), 200
    except DecodingError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except ProcessingError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Pipeline failure: {e}"}), 500

@bp.route("/api/download/<path:filename>", methods=["GET"])
def download(filename: str):
    settings=current_app.config["SENTINEL_SETTINGS"]
    return send_from_directory(settings.results_dir, filename, as_attachment=True)

@bp.route("/api/health", methods=["GET"])
def health(): return jsonify({"status":"ok", "project":"Resolvance"}), 200
