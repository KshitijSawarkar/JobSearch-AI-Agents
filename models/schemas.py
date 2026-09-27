from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, Field, HttpUrl, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class JobPosting(BaseModel):
    id: str = Field(description="Unique hash or ID of the job posting")
    title: NonEmptyStr = Field(description="Job title (e.g., AI Engineer, Python Backend Developer)")
    company: NonEmptyStr = Field(description="Company or organization name")
    location: str = Field(default="Remote / Hybrid", description="Job location")
    url: str = Field(description="Direct link to job description or application page")
    source: str = Field(default="Job Board", description="Source where job was found")
    jd_text: NonEmptyStr = Field(description="Full or summarized job description text")
    date_found: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"), description="Date discovered")

class ScoreRubricBreakdown(BaseModel):
    tech_match_score: Annotated[int, Field(ge=0, le=40, description="Technical skill and tool match (0-40)")]
    experience_match_score: Annotated[int, Field(ge=0, le=30, description="Domain and problem statement match (0-30)")]
    astrological_fit_score: Annotated[int, Field(ge=0, le=30, description="Chart synergy, timing, and growth house alignment (0-30)")]
    tech_match_reasoning: str = Field(description="Rationale for technical alignment")
    experience_reasoning: str = Field(description="Rationale for experience/project alignment")
    astrological_reasoning: str = Field(description="Insight on astrological alignment (e.g. 11th house Jupiter gains, 10th house Saturn rigor)")

class JobEvaluation(BaseModel):
    job_id: str
    total_score: Annotated[int, Field(ge=0, le=100, description="Overall match score (0-100)")]
    score_breakdown: ScoreRubricBreakdown
    recommendation: Literal["High Priority", "Strong Fit", "Moderate Fit", "Skip"]
    tailored_pitch_summary: str = Field(description="2-line executive summary tailored to this position")

class TailoredMaterials(BaseModel):
    job_id: str
    latex_code: str = Field(description="Complete, standard-compliant LaTeX resume code grounded ONLY in candidate facts")
    cover_letter: str = Field(description="Compelling, personalized cover letter highlighting relevant projects")
    astrological_notes: str = Field(description="Astrological strategic advice for interview / application timing")

class ApplicationRecord(BaseModel):
    job_id: str
    status: Literal["new", "applied", "interview", "rejected"] = "new"
    applied_date: str | None = None
    notes: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
