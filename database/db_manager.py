import os
import sqlite3
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from models.schemas import JobPosting, JobEvaluation, TailoredMaterials, ApplicationRecord

DB_PATH = Path(__file__).resolve().parent / "jobsearch.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

    def url_exists(self, url: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM jobs WHERE url = ?", (url,))
            return cursor.fetchone() is not None

    def save_job_and_evaluation(
        self,
        job: JobPosting,
        eval_result: JobEvaluation,
        materials: TailoredMaterials
    ):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Insert or Replace into jobs
            cursor.execute("""
                INSERT OR REPLACE INTO jobs (
                    id, title, company, location, url, source, jd_text,
                    total_score, tech_score, experience_score, astro_score,
                    score_reasoning, recommendation, date_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id, job.title, job.company, job.location, job.url, job.source, job.jd_text,
                eval_result.total_score,
                eval_result.score_breakdown.tech_match_score,
                eval_result.score_breakdown.experience_match_score,
                eval_result.score_breakdown.astrological_fit_score,
                json.dumps(eval_result.score_breakdown.model_dump()),
                eval_result.recommendation,
                job.date_found
            ))

            # 2. Insert or Replace into tailored_materials
            from datetime import datetime
            cursor.execute("""
                INSERT OR REPLACE INTO tailored_materials (
                    job_id, latex_code, cover_letter, astrological_notes, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                job.id,
                materials.latex_code,
                materials.cover_letter,
                materials.astrological_notes,
                datetime.utcnow().isoformat()
            ))

            # 3. Ensure record in application_status if not existing
            cursor.execute("""
                INSERT OR IGNORE INTO application_status (
                    job_id, status, notes, updated_at
                ) VALUES (?, 'new', '', ?)
            """, (job.id, datetime.utcnow().isoformat()))

            conn.commit()

    def update_application_status(self, job_id: str, status: str, notes: str = "") -> bool:
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            applied_date = datetime.utcnow().strftime("%Y-%m-%d") if status == "applied" else None
            cursor.execute("""
                UPDATE application_status
                SET status = ?, applied_date = COALESCE(?, applied_date), notes = ?, updated_at = ?
                WHERE job_id = ?
            """, (status, applied_date, notes, datetime.utcnow().isoformat(), job_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_dashboard_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    j.id, j.title, j.company, j.location, j.url, j.source, j.jd_text,
                    j.total_score, j.tech_score, j.experience_score, j.astro_score,
                    j.score_reasoning, j.recommendation, j.date_found,
                    tm.latex_code, tm.cover_letter, tm.astrological_notes,
                    app.status, app.applied_date, app.notes
                FROM jobs j
                LEFT JOIN tailored_materials tm ON j.id = tm.job_id
                LEFT JOIN application_status app ON j.id = app.job_id
                ORDER BY j.date_found DESC, j.total_score DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                if item.get("score_reasoning"):
                    try:
                        item["score_reasoning"] = json.loads(item["score_reasoning"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def export_to_static_json(self, output_path: Path):
        data = self.get_all_dashboard_jobs(limit=100)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
