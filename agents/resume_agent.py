import os
import json
from pathlib import Path
from models.schemas import JobPosting, JobEvaluation, TailoredMaterials

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

class ResumeTailoringAgent:
    def __init__(self):
        with open(CONFIG_DIR / "candidate_profile.json", "r", encoding="utf-8") as f:
            self.profile = json.load(f)
        with open(CONFIG_DIR / "astrological_chart.json", "r", encoding="utf-8") as f:
            self.astro = json.load(f)

    def generate_latex_resume(self, job: JobPosting, eval_res: JobEvaluation) -> str:
        """Generates standard-compliant LaTeX resume strictly grounded in candidate facts."""
        info = self.profile["personal_info"]
        edu = self.profile["education"]
        exp = self.profile["experience"]
        projects = self.profile["projects"]
        skills = self.profile["skills"]

        # Prioritize relevant projects based on job title / description
        jd_lower = (job.title + " " + job.jd_text).lower()
        scored_projects = []
        for p in projects:
            relevance = sum(1 for tool in p["tools"] if tool.lower() in jd_lower)
            if any(k in jd_lower for k in ["ml", "ai", "llm", "agent"]) and p["category"] == "Generative AI & LLM Systems":
                relevance += 3
            if any(k in jd_lower for k in ["cloud", "aws", "data", "pipeline"]) and "AI" in p["name"]:
                relevance += 2
            scored_projects.append((relevance, p))
        
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        top_projects = [p for _, p in scored_projects[:4]]

        # Header and Executive Summary
        full_name = info["full_name"]
        email = info["email"]
        location = info["location"]
        ai_link = info["links"]["ai_mentor"]
        cleaner_link = info["links"]["smart_data_cleaner"]
        pitch = eval_res.tailored_pitch_summary

        lines = [
            r"\documentclass[letterpaper,10pt]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[margin=0.6in]{geometry}",
            r"\usepackage{hyperref}",
            r"\usepackage{enumitem}",
            r"\usepackage{titlesec}",
            r"\usepackage{xcolor}",
            r"\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}",
            r"\titleformat{\section}{\large\bfseries\color{black}}{}{0em}{\hrulefill\\[-0.5em]}",
            r"\newcommand{\datedsection}[2]{\noindent\textbf{#1} \hfill \textit{#2}\\}",
            r"\newcommand{\datedsubsection}[2]{\noindent\textbf{#1} \hfill \textit{#2}\\}",
            r"\begin{document}",
            r"\pagestyle{empty}",
            r"\begin{center}",
            rf"    {{\huge \textbf{{{full_name}}}}}\\[0.3em]",
            rf"    \href{{mailto:{email}}}{{{email}}} $|$ {location} $|$ \href{{{ai_link}}}{{AI Mentor System}} $|$ \href{{{cleaner_link}}}{{Smart Data Cleaner}}",
            r"\end{center}",
            r"\vspace{-0.8em}",
            r"\section*{Executive Summary}",
            rf"{pitch} Candidate with proven background in machine learning operations, cloud automation, and high-performance quantitative/embedded systems.",
            r"\vspace{-0.8em}",
            r"\section*{Education}"
        ]

        for ed in edu:
            lines.append(rf"\datedsection{{{ed['degree']} --- {ed['institution']}}}{{{ed['duration']}}}")
            lines.append(rf"Status: {ed['status']}\\[0.2em]")

        lines.extend([
            r"\vspace{-0.8em}",
            r"\section*{Technical Skills}",
            r"\begin{itemize}[leftmargin=*, noitemsep, topsep=0pt]",
            rf"    \item \textbf{{Programming Languages:}} {', '.join(skills['languages'])}",
            rf"    \item \textbf{{AI / ML \& Operations:}} {', '.join(skills['machine_learning_and_ai'])}",
            rf"    \item \textbf{{Cloud \& DevOps:}} {', '.join(skills['cloud_and_devops'])}",
            rf"    \item \textbf{{Hardware \& Embedded:}} {', '.join(skills['hardware_and_embedded'])}",
            rf"    \item \textbf{{Networking \& Analytics:}} {', '.join(skills['networking_and_data'])}",
            r"\end{itemize}",
            r"\vspace{-0.8em}",
            r"\section*{Professional Experience}"
        ])

        for e in exp:
            tools_str = ", ".join(e["tools_concepts"])
            lines.append(rf"\datedsubsection{{{e['role']} --- {e['company']}}}{{{e['duration']}}}")
            lines.append(rf"\textit{{Domain: {e['domain']}}} $|$ \textbf{{Tech:}} {tools_str}")
            lines.append(r"\begin{itemize}[leftmargin=*, noitemsep, topsep=2pt]")
            for algo in e["algorithms_logic"]:
                cleaned_algo = algo.replace("&", r"\&").replace("%", r"\%")
                lines.append(rf"    \item {cleaned_algo}")
            lines.append(r"\end{itemize}")
            lines.append(r"\vspace{0.3em}")

        lines.extend([
            r"\vspace{-0.8em}",
            r"\section*{Selected Projects}"
        ])

        for p in top_projects:
            tools_str = ", ".join(p["tools"])
            cleaned_desc = p["description"].replace("&", r"\&").replace("%", r"\%")
            lines.append(rf"\textbf{{{p['name']}}} ($|$\textit{{{p['category']}}}) \hfill \textbf{{{tools_str}}}")
            lines.append(r"\begin{itemize}[leftmargin=*, noitemsep, topsep=2pt]")
            lines.append(rf"    \item {cleaned_desc}")
            lines.append(r"\end{itemize}")
            lines.append(r"\vspace{0.2em}")

        lines.append(r"\end{document}")
        return "\n".join(lines)

    def generate_cover_letter(self, job: JobPosting, eval_res: JobEvaluation) -> str:
        """Generates a high-converting, strictly fact-verified cover letter."""
        name = self.profile["personal_info"]["full_name"]
        
        return f"""Dear Hiring Team at {job.company},

I am writing to express my strong enthusiasm for the {job.title} position at {job.company}. With a rigorous foundation in Control and Instrumentation (MNNIT Allahabad) and Electronics & Communication (RCOEM Nagpur), combined with practical expertise in cloud infrastructure, machine learning pipelines, and agentic AI architectures, I am excited about the opportunity to contribute immediately to your team.

During my virtual internship with AICTE as an AWS Cloud Intern / AI Developer, I engineered scalable cloud and ML-Ops pipelines utilizing AWS Lambda, EC2, and SageMaker. I developed automated triggers for S3 data ingestion and deployed predictive models using containerized and serverless environments.

Furthermore, my independent engineering initiatives directly address high-impact technical problems:
- Designed and launched "AI Mentor", an agentic AI assistant with strict contextual optimization and retrieval guardrails.
- Built "TrendGuard-200", a multi-asset quantitative risk framework achieving 90% latency reduction via NumPy vectorized computing.
- Deployed "Smart Data Cleaner", an automated data transformation and preprocessing web utility.

{eval_res.score_breakdown.tech_match_reasoning} My analytical background and drive for systematic execution make me well-suited to tackle the technical roadmap at {job.company}.

I look forward to the possibility of discussing how my experience and technical capabilities align with your strategic goals.

Sincerely,
{name}
Location: {self.profile["personal_info"]["location"]}
Portfolio: {self.profile["personal_info"]["links"]["smart_data_cleaner"]}
"""

    def generate_astrological_strategy(self, job: JobPosting, eval_res: JobEvaluation) -> str:
        """Provides tactical alignment notes based on the native's chart."""
        return (
            f"🪐 Astrological Strategic Alignment for {job.company}:\n"
            f"• Synergy Index: {eval_res.score_breakdown.astrological_fit_score}/30\n"
            f"• 11th House Exalted Jupiter (Power 22): Prime window for career gains, high-impact mentorship, and expanding professional network.\n"
            f"• 1st House Mars (Power 17) + Moon (Power 19): Emphasize decisive problem solving, initiative, and proactive technical execution in interview interactions.\n"
            f"• 10th House Saturn (Power 4, Retrograde): Focus communication on long-term stability, disciplined code quality, and structured systems architecture."
        )

    def tailor_materials(self, job: JobPosting, eval_res: JobEvaluation) -> TailoredMaterials:
        latex = self.generate_latex_resume(job, eval_res)
        cover = self.generate_cover_letter(job, eval_res)
        astro_notes = self.generate_astrological_strategy(job, eval_res)

        return TailoredMaterials(
            job_id=job.id,
            latex_code=latex,
            cover_letter=cover,
            astrological_notes=astro_notes
        )
