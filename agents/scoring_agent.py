import os
import json
import re
from typing import Dict, Any
from pathlib import Path
from models.schemas import JobPosting, JobEvaluation, ScoreRubricBreakdown

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

class ScoringAgent:
    def __init__(self):
        with open(CONFIG_DIR / "candidate_profile.json", "r", encoding="utf-8") as f:
            self.profile = json.load(f)
        with open(CONFIG_DIR / "astrological_chart.json", "r", encoding="utf-8") as f:
            self.astro = json.load(f)
        
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def evaluate_job(self, job: JobPosting) -> JobEvaluation:
        """Evaluates a job posting using strict rubric (0-100 score breakdown)."""
        if self.api_key:
            try:
                return self._evaluate_with_gemini(job)
            except Exception as e:
                print(f"Gemini API error during scoring, falling back to rule-based rubric: {e}")

        return self._evaluate_with_heuristic(job)

    def _evaluate_with_heuristic(self, job: JobPosting) -> JobEvaluation:
        jd_lower = (job.title + " " + job.jd_text).lower()
        
        # 1. Tech Match (0 - 40)
        all_skills = []
        for cat in self.profile.get("skills", {}).values():
            all_skills.extend(cat)
        
        matched_skills = [s for s in all_skills if s.lower() in jd_lower]
        tech_score = min(40, int(len(matched_skills) * 8) + (10 if any(k in jd_lower for k in ["python", "machine learning", "ai"]) else 0))
        if tech_score < 15:
            tech_score = 15  # baseline for domain adjacent roles

        tech_reason = f"Matched core technical competencies: {', '.join(matched_skills) if matched_skills else 'General engineering & Python fundamentals'}."

        # 2. Experience Match (0 - 30)
        exp_score = 10
        if any(w in jd_lower for w in ["aws", "cloud", "lambda", "sagemaker", "ml-ops", "api"]):
            exp_score += 10
        if any(w in jd_lower for w in ["yolo", "cv", "computer vision", "embedded", "control", "quant", "financial"]):
            exp_score += 8
        exp_score = min(30, exp_score)
        
        exp_reason = "Direct project and internship alignment with cloud pipelines, ML model hosting, and automation systems."

        # 3. Astrological Fit (0 - 30)
        # Virgo Lagna / Exalted Jupiter in 11th / Mars-Moon in 1st
        astro_score = 22
        if any(w in jd_lower for w in ["ai", "research", "lead", "architect", "intelligence"]):
            astro_score += 6  # 11th house exalted Jupiter expansion & network gains
        if any(w in jd_lower for w in ["fast-paced", "scale", "performance", "optimization"]):
            astro_score += 2  # 1st house Mars-Moon high drive
        astro_score = min(30, astro_score)

        astro_reason = "Strong 11th House exalted Jupiter (Power 22) synergy favoring collaborative growth and high recognition in data/AI architecture."

        total_score = tech_score + exp_score + astro_score
        
        if total_score >= 80:
            rec = "High Priority"
        elif total_score >= 65:
            rec = "Strong Fit"
        elif total_score >= 50:
            rec = "Moderate Fit"
        else:
            rec = "Skip"

        rubric = ScoreRubricBreakdown(
            tech_match_score=tech_score,
            experience_match_score=exp_score,
            astrological_fit_score=astro_score,
            tech_match_reasoning=tech_reason,
            experience_reasoning=exp_reason,
            astrological_reasoning=astro_reason
        )

        return JobEvaluation(
            job_id=job.id,
            total_score=total_score,
            score_breakdown=rubric,
            recommendation=rec,
            tailored_pitch_summary=f"Strong candidacy leveraging {', '.join(matched_skills[:3]) if matched_skills else 'Python & AI Engineering'} with proven cloud and applied ML project impact."
        )

    def _evaluate_with_gemini(self, job: JobPosting) -> JobEvaluation:
        import urllib.request
        prompt = f"""
You are an expert technical recruiter and alignment analyst.
Evaluate this job strictly against the candidate profile and astrological profile.

Candidate Profile:
{json.dumps(self.profile, indent=2)}

Astrological Profile:
{json.dumps(self.astro, indent=2)}

Job Details:
Title: {job.title}
Company: {job.company}
Description: {job.jd_text}

Rules:
1. tech_match_score: 0 to 40
2. experience_match_score: 0 to 30
3. astrological_fit_score: 0 to 30 (based on 11th house Jupiter gains, 1st house Mars-Moon drive, 10th house Saturn discipline)
4. total_score = tech_match_score + experience_match_score + astrological_fit_score (0 to 100)

Return JSON with exact keys:
{{
  "job_id": "{job.id}",
  "total_score": <int>,
  "score_breakdown": {{
    "tech_match_score": <int>,
    "experience_match_score": <int>,
    "astrological_fit_score": <int>,
    "tech_match_reasoning": "<string>",
    "experience_reasoning": "<string>",
    "astrological_reasoning": "<string>"
  }},
  "recommendation": "High Priority" | "Strong Fit" | "Moderate Fit" | "Skip",
  "tailored_pitch_summary": "<2-sentence pitch>"
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)
            return JobEvaluation.model_validate(parsed)
