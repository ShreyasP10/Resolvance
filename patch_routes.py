import re

with open('api/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

header_imports = """
from __future__ import annotations
from pathlib import Path
import uuid
import threading
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from core.exceptions import DecodingError, ProcessingError

bp=Blueprint("api", __name__)

# In-memory job store for async polling
# Format: { "job_id": {"status": "processing" | "complete" | "error", "result": dict, "error": str} }
jobs = {}

def run_job_async(pipeline, up_path, job_id):
    try:
        result = pipeline.run(up_path, job_id=job_id)
        jobs[job_id] = {"status": "complete", "result": result.to_dict()}
    except DecodingError as e:
        jobs[job_id] = {"status": "error", "error": str(e)}
    except ProcessingError as e:
        jobs[job_id] = {"status": "error", "error": str(e)}
    except Exception as e:
        jobs[job_id] = {"status": "error", "error": f"Pipeline failure: {e}"}

@bp.route("/api/status/<job_id>", methods=["GET"])
def job_status(job_id: str):
    if job_id not in jobs:
        return jsonify({"success": False, "error": "Job not found"}), 404
    job = jobs[job_id]
    if job["status"] == "complete":
        return jsonify(job["result"]), 200
    elif job["status"] == "error":
        return jsonify({"success": False, "error": job["error"]}), 500
    else:
        # Processing
        return jsonify({"success": True, "status": "processing", "job_id": job_id}), 202
"""

# Replace top part
code = re.sub(r'from __future__.*?bp=Blueprint\("api", __name__\)', header_imports.strip(), code, flags=re.DOTALL)

# Replace the try/except block in infer()
old_infer_try = """    try:
        result=pipeline.run(up_path, job_id=job_id)
        return jsonify(result.to_dict()), 200
    except DecodingError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except ProcessingError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Pipeline failure: {e}"}), 500"""

new_infer_try = """    jobs[job_id] = {"status": "processing"}
    thread = threading.Thread(target=run_job_async, args=(pipeline, up_path, job_id))
    thread.start()
    return jsonify({"success": True, "status": "processing", "job_id": job_id}), 202"""

code = code.replace(old_infer_try, new_infer_try)

with open('api/routes.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Backend Async Queue Implemented!")
