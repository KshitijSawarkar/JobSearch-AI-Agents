import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database.db_manager import DatabaseManager
from agents.job_finder import JobFinderAgent
from agents.scoring_agent import ScoringAgent
from agents.resume_agent import ResumeTailoringAgent

def run_daily_pipeline():
    print("==================================================")
    print("[*] Initiating Daily Job Search Multi-Agent Pipeline")
    print("==================================================")

    db = DatabaseManager()
    finder = JobFinderAgent(db_manager=db, max_jobs_per_day=10)
    scorer = ScoringAgent()
    tailorer = ResumeTailoringAgent()

    print("\n[Agent 1: Job Finder] Searching and deduplicating up to 10 fresh jobs...")
    jobs = finder.find_daily_jobs()
    print(f"[+] Found {len(jobs)} eligible new jobs for processing.")

    if not jobs:
        print("[i] No new jobs to process today (or all discovered jobs were already evaluated).")
        web_data_path = Path(__file__).resolve().parent.parent / "web" / "data" / "jobs.json"
        db.export_to_static_json(web_data_path)
        return

    for idx, job in enumerate(jobs, 1):
        print(f"\n[{idx}/{len(jobs)}] Processing: {job.title} at {job.company}")
        
        # 1. Scoring & Alignment Agent
        print("   [Agent 2: Scoring] Computing 0-100 rubric & astrological fit...")
        eval_res = scorer.evaluate_job(job)
        print(f"      Score: {eval_res.total_score}/100 ({eval_res.recommendation}) | Tech: {eval_res.score_breakdown.tech_match_score}/40, Exp: {eval_res.score_breakdown.experience_match_score}/30, Astro: {eval_res.score_breakdown.astrological_fit_score}/30")

        # 2. Resume & LaTeX Tailoring Agent
        print("   [Agent 3: Resume Tailoring] Generating grounded LaTeX & custom Cover Letter...")
        materials = tailorer.tailor_materials(job, eval_res)

        # 3. Database Persistence
        print("   [+] Storing record to database...")
        db.save_job_and_evaluation(job, eval_res, materials)

    # Export to web folder for instant static dashboard viewing
    web_data_path = Path(__file__).resolve().parent.parent / "web" / "data" / "jobs.json"
    db.export_to_static_json(web_data_path)
    print(f"\n[+] Exported latest dashboard snapshot to: {web_data_path}")
    print("[+] Daily Pipeline Completed Successfully!")

if __name__ == "__main__":
    run_daily_pipeline()
