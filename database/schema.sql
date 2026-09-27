-- Cloudflare D1 & SQLite Compatible Database Schema

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT DEFAULT 'Remote',
    url TEXT NOT NULL UNIQUE,
    source TEXT DEFAULT 'Web',
    jd_text TEXT NOT NULL,
    total_score INTEGER DEFAULT 0,
    tech_score INTEGER DEFAULT 0,
    experience_score INTEGER DEFAULT 0,
    astro_score INTEGER DEFAULT 0,
    score_reasoning TEXT,
    recommendation TEXT,
    date_found TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tailored_materials (
    job_id TEXT PRIMARY KEY,
    latex_code TEXT NOT NULL,
    cover_letter TEXT NOT NULL,
    astrological_notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS application_status (
    job_id TEXT PRIMARY KEY,
    status TEXT CHECK(status IN ('new', 'applied', 'interview', 'rejected')) DEFAULT 'new',
    applied_date TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date_found DESC);
CREATE INDEX IF NOT EXISTS idx_app_status ON application_status(status);
