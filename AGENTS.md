# Agent Architecture & Operational Rules

## 1. Grounding & Anti-Hallucination Constraints
- **Strict Fact Verification**: The Resume Tailoring Agent must ONLY use skills, experiences, and dates present in `skills-lock.json`. Never invent companies, certifications, or technologies.
- **Structured Outputs (Pydantic)**: All LLM outputs must adhere to strict Pydantic schemas (JSON mode) with validation checks.
- **Score Transparency**: The Job Matcher Agent must provide a score breakdown (0-100) with explicit rubric items (e.g., Tech Match 40%, Experience Match 30%, Astrological/Intuitive Fit 30%).

## 2. Multi-Agent Pipeline
- **Job Finder Agent**:
  - Daily limit: Max 10 fresh jobs/day.
  - Deduping: Filter against already stored job URLs in the database.
- **Scoring & Alignment Agent**:
  - Compares JD against Candidate Profile + Astrological inputs.
  - Computes match score and generates custom cover letter & tailored LaTeX diff.
- **LaTeX Compilation Agent**:
  - Outputs standard compliant LaTeX syntax that compiles without missing packages.

## 3. Database Schema Contract
- Tables: `jobs` (id, title, company, url, jd_text, score, date_found), `tailored_materials` (job_id, latex_code, cover_letter, astrological_notes), `application_status` (job_id, status: ['new', 'applied', 'rejected', 'interview']).

## 4. UI Dashboard Contract
- Fully responsive (Mobile + Desktop).
- Features: Kanban/List view of 10 daily jobs, fit score badges, raw LaTeX copy/download, and 1-click "Mark as Applied" toggle.


please use the skills mentioned below for making JobSearch(AI_Agents) project.
1. pydantic/skills: npx skills add https://github.com/pydantic/skills --skill pydantic
2. cloudflare/skills: npx skills add https://github.com/cloudflare/skills --skill cloudflare
3. playwright-cli : npx skills add https://github.com/microsoft/playwright-cli --skill playwright-cli
4. npx skills add https://github.com/bahayonghang/academic-writing-skills --skill latex-paper-en
5. npx skills add https://github.com/github/awesome-copilot --skill create-github-action-workflow-specification
6. npx skills add https://github.com/googlechrome/modern-web-guidance --skill modern-web-guidance
7. npx skills add https://github.com/aws/agent-toolkit-for-aws --skill deploying-custom-domain-rest-api