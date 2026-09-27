import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db_manager import DatabaseManager
from agents.pipeline import run_daily_pipeline

app = Flask(__name__, static_folder="web")
db = DatabaseManager()

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("web", path)

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    jobs = db.get_all_dashboard_jobs(limit=100)
    return jsonify(jobs)

@app.route("/api/status", methods=["POST"])
def update_status():
    data = request.get_json() or {}
    job_id = data.get("job_id")
    status = data.get("status")
    notes = data.get("notes", "")
    
    if not job_id or not status:
        return jsonify({"error": "Missing job_id or status"}), 400
        
    success = db.update_application_status(job_id, status, notes)
    # Refresh exported static snapshot
    web_data_path = Path(__file__).resolve().parent / "web" / "data" / "jobs.json"
    db.export_to_static_json(web_data_path)
    return jsonify({"success": success})

@app.route("/api/run_pipeline", methods=["POST"])
def trigger_pipeline():
    try:
        run_daily_pipeline()
        return jsonify({"success": True, "message": "Pipeline completed successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] AuraMatch AI Dashboard starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
