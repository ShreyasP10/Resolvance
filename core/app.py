"""Flask factory per UPDATED_SIH26142_FULL_v2.md:10"""
from __future__ import annotations
import time
from pathlib import Path
from flask import Flask, render_template, send_from_directory, Response
from flask_cors import CORS
from .config import Settings
from .logging_setup import configure_logging, get_logger
from .pipeline import Pipeline

log=get_logger("app")

def purge_stale(directory: Path, hours: int):
    if hours is None or hours<=0: return
    cutoff=time.time()-hours*3600
    rem=0
    for f in directory.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True); rem+=1
        except Exception: pass
    if rem: log.info(f"purged {rem} from {directory}")

def create_app(settings: Settings | None=None) -> Flask:
    if settings is None: settings=Settings.from_env()
    configure_logging()
    app=Flask(__name__, template_folder=str(settings.base_dir / "frontend" / "templates"), static_folder=str(settings.base_dir / "frontend" / "static"))
    app.config["SENTINEL_SETTINGS"]=settings
    app.config["SENTINEL_PIPELINE"]=Pipeline(settings)
    app.config["MAX_CONTENT_LENGTH"]=settings.max_bytes
    CORS(app)
    settings.ensure_dirs()
    if settings.retention_hours:
        purge_stale(settings.upload_dir, settings.retention_hours)
        purge_stale(settings.results_dir, settings.retention_hours)
    from api.routes import bp
    app.register_blueprint(bp)
    @app.route("/")
    def index(): return render_template("index.html")
    @app.route("/static/results/<path:filename>")
    def result_file(filename: str): return send_from_directory(settings.results_dir, filename)
    @app.route("/favicon.ico")
    def favicon():
        svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#0b0d11" stroke="#00ff88" stroke-width="3"/><text x="32" y="42" font-family="monospace" font-size="28" font-weight="bold" fill="#00ff88" text-anchor="middle">R</text></svg>'
        return Response(svg, mimetype="image/svg+xml")
    @app.errorhandler(413)
    def too_large(e): return {"success": False, "error": "File too large. Max 50MB."}, 413
    @app.errorhandler(404)
    def not_found(e): return {"success": False, "error": "Not found"}, 404
    return app
