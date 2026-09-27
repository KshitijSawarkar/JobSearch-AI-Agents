# 🪐 AuraMatch AI — Multi-Agent Job Search & Astrological Resume Tailoring

A 100% free, cloud-automated multi-agent AI system that:
1. **Discovers top jobs daily** (max 10/day) with deduplication against your database.
2. **Evaluates fit scores (0–100)** with transparent rubric breakdowns (Tech Match 40%, Experience 30%, Astrological Fit 30%).
3. **Tailors compilation-ready LaTeX resumes & personalized cover letters** strictly grounded in your verified experience and astrological timing notes.
4. **Interactive Dashboard**: Accessible on both mobile & desktop with 1-click status tracking (*New, Applied, Interviewing, Archived*), raw LaTeX copy & download, and score analysis.

---

## 🏗️ Architecture & Free Cloud Infrastructure

```
                                  [ GitHub Actions Cron ] (Daily 9:00 AM IST)
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      [ Job Finder Agent ]       [ Scoring Agent (Gemini) ]    [ LaTeX Resume Agent ]
   (RemoteOK/Jobicy/Curated)    (Tech/Exp/Astro 0-100 Rubric)  (Grounded LaTeX + Letters)
               │                            │                            │
               └────────────────────────────┬────────────────────────────┘
                                            ▼
                               [ SQLite / Cloudflare D1 ]
                                            │
                                            ▼
                        [ Cloudflare Pages / Static Dashboard ]
                              (Responsive Mobile & Laptop)
```

---

## 🚀 Quick Start (Local Run)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Multi-Agent Pipeline
```bash
# Optional: export GEMINI_API_KEY="your-gemini-api-key"
python agents/pipeline.py
```

### 3. Launch Dashboard UI
```bash
python server.py
```
Open **`http://localhost:5000`** in your browser (desktop or mobile).

---

## ☁️ 100% Free Cloud Deployment

1. **GitHub Actions**: Automated in `.github/workflows/daily_agent_run.yml`. Runs daily on schedule, processes jobs, and commits updated records.
2. **Gemini API Key**: Add `GEMINI_API_KEY` to your GitHub Repository Secrets (`Settings -> Secrets and variables -> Actions`).
3. **Free Hosting**:
   - **Cloudflare Pages**: Connect your GitHub repo, set root build folder to `web/`, and deploy in 1 click.
   - Or **GitHub Pages**: Automatically deployed via the included workflow.

---

## 🛡️ Anti-Hallucination & Grounding Guardrails

- Fact constraints are strictly locked in [`config/candidate_profile.json`](file:///c:/Users/kshit/Desktop/MicroSaas/JobSearch(AI_Agents)/config/candidate_profile.json).
- Astrological parameters are grounded in [`config/astrological_chart.json`](file:///c:/Users/kshit/Desktop/MicroSaas/JobSearch(AI_Agents)/config/astrological_chart.json).
- Pydantic models in [`models/schemas.py`](file:///c:/Users/kshit/Desktop/MicroSaas/JobSearch(AI_Agents)/models/schemas.py) enforce strict schema boundaries on all agent inputs and outputs.
