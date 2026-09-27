import hashlib
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from typing import List, Set
from models.schemas import JobPosting
from database.db_manager import DatabaseManager

class JobFinderAgent:
    """
    Multi-Source Autonomous Job Finder Agent.
    Aggregates from Arbeitnow, Himalayas, WeWorkRemotely, RemoteOK, Jobicy, and Curated feeds.
    Strictly dedupes against database URLs and enforces daily cap.
    """
    def __init__(self, db_manager: DatabaseManager, max_jobs_per_day: int = 10):
        self.db = db_manager
        self.max_jobs = max_jobs_per_day
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.target_keywords = [
            "ai", "ml", "machine learning", "python", "data", "cloud",
            "aws", "embedded", "backend", "developer", "engineer", "software", "analyst"
        ]

    def _generate_id(self, url: str, title: str, company: str) -> str:
        raw = f"{url}_{title}_{company}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def _clean_html(self, text: str) -> str:
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _is_relevant(self, text: str) -> bool:
        t_low = text.lower()
        return any(k in t_low for k in self.target_keywords)

    def fetch_arbeitnow_jobs(self) -> List[JobPosting]:
        """Source 1: Arbeitnow API (Free International & Remote Tech Jobs)"""
        jobs: List[JobPosting] = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("data", [])[:20]:
                    title = item.get("title", "")
                    company = item.get("company_name", "")
                    job_url = item.get("url", "")
                    location = item.get("location", "Remote")
                    description = self._clean_html(item.get("description", ""))
                    tags = " ".join(item.get("tags", []))

                    if not title or not company or not job_url:
                        continue

                    if self._is_relevant(title + " " + tags + " " + description[:300]):
                        job_id = self._generate_id(job_url, title, company)
                        if not self.db.url_exists(job_url):
                            jobs.append(JobPosting(
                                id=job_id,
                                title=title,
                                company=company,
                                location=location or "Remote",
                                url=job_url,
                                source="Arbeitnow",
                                jd_text=description[:2500] if description else f"{title} at {company}."
                            ))
        except Exception as e:
            print(f"[-] Arbeitnow fetch notice: {e}")
        return jobs

    def fetch_weworkremotely_jobs(self) -> List[JobPosting]:
        """Source 2: WeWorkRemotely RSS (Remote Programming & AI Jobs)"""
        jobs: List[JobPosting] = []
        try:
            url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:20]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")

                    if title_elem is None or link_elem is None:
                        continue

                    raw_title = title_elem.text or ""
                    job_url = link_elem.text or ""
                    description = self._clean_html(desc_elem.text if desc_elem is not None else "")

                    # Format is usually: "Company: Job Title"
                    if ":" in raw_title:
                        parts = raw_title.split(":", 1)
                        company = parts[0].strip()
                        title = parts[1].strip()
                    else:
                        company = "Remote Team"
                        title = raw_title.strip()

                    if not title or not job_url:
                        continue

                    if self._is_relevant(title + " " + description[:300]):
                        job_id = self._generate_id(job_url, title, company)
                        if not self.db.url_exists(job_url):
                            jobs.append(JobPosting(
                                id=job_id,
                                title=title,
                                company=company,
                                location="Worldwide Remote",
                                url=job_url,
                                source="WeWorkRemotely",
                                jd_text=description[:2500] if description else f"{title} at {company}."
                            ))
        except Exception as e:
            print(f"[-] WeWorkRemotely fetch notice: {e}")
        return jobs

    def fetch_himalayas_jobs(self) -> List[JobPosting]:
        """Source 3: Himalayas Remote Jobs API"""
        jobs: List[JobPosting] = []
        try:
            url = "https://himalayas.app/jobs/api?limit=25"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    company = item.get("companyName", "")
                    slug = item.get("slug", "")
                    company_slug = item.get("companySlug", "")
                    job_url = f"https://himalayas.app/companies/{company_slug}/jobs/{slug}" if slug else item.get("applicationLink", "")
                    description = self._clean_html(item.get("description", ""))
                    categories = " ".join(item.get("categories", []))

                    if not title or not company or not job_url:
                        continue

                    if self._is_relevant(title + " " + categories + " " + description[:300]):
                        job_id = self._generate_id(job_url, title, company)
                        if not self.db.url_exists(job_url):
                            jobs.append(JobPosting(
                                id=job_id,
                                title=title,
                                company=company,
                                location=item.get("location", "Remote"),
                                url=job_url,
                                source="Himalayas",
                                jd_text=description[:2500] if description else f"{title} at {company}."
                            ))
        except Exception as e:
            print(f"[-] Himalayas fetch notice: {e}")
        return jobs

    def fetch_jobicy_jobs(self) -> List[JobPosting]:
        """Source 4: Jobicy Remote Jobs API"""
        jobs: List[JobPosting] = []
        try:
            url = "https://jobicy.com/api/v2/remote-jobs?count=20&tag=engineering,data,ai"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("jobs", []):
                    title = item.get("jobTitle", "")
                    company = item.get("companyName", "")
                    job_url = item.get("url", "")
                    description = self._clean_html(item.get("jobDescription", ""))

                    if not title or not company or not job_url:
                        continue

                    job_id = self._generate_id(job_url, title, company)
                    if not self.db.url_exists(job_url):
                        jobs.append(JobPosting(
                            id=job_id,
                            title=title,
                            company=company,
                            location=item.get("jobGeo", "Remote"),
                            url=job_url,
                            source="Jobicy",
                            jd_text=description[:2500] if description else f"{title} at {company}."
                        ))
        except Exception as e:
            print(f"[-] Jobicy fetch notice: {e}")
        return jobs

    def fetch_remoteok_jobs(self) -> List[JobPosting]:
        """Source 5: RemoteOK API"""
        jobs: List[JobPosting] = []
        try:
            url = "https://remoteok.com/api"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data[1:25]:
                    title = item.get("position", "")
                    company = item.get("company", "")
                    job_url = item.get("url", "")
                    tags = " ".join(item.get("tags", []))
                    description = self._clean_html(item.get("description", ""))

                    if not title or not company or not job_url:
                        continue

                    if self._is_relevant(title + " " + tags):
                        job_id = self._generate_id(job_url, title, company)
                        if not self.db.url_exists(job_url):
                            jobs.append(JobPosting(
                                id=job_id,
                                title=title,
                                company=company,
                                location=item.get("location", "Remote"),
                                url=job_url,
                                source="RemoteOK",
                                jd_text=description[:2500] if description else f"{title} at {company}."
                            ))
        except Exception as e:
            print(f"[-] RemoteOK fetch notice: {e}")
        return jobs

    def find_daily_jobs(self) -> List[JobPosting]:
        """
        Multi-Source aggregator: collects diverse opportunities from multiple websites,
        interleaves them to ensure website diversity, dedupes against DB, and caps at max_jobs.
        """
        source_buckets: List[List[JobPosting]] = [
            self.fetch_arbeitnow_jobs(),
            self.fetch_weworkremotely_jobs(),
            self.fetch_himalayas_jobs(),
            self.fetch_jobicy_jobs(),
            self.fetch_remoteok_jobs()
        ]

        # Round-robin selection across sources for maximum website diversity
        final_jobs: List[JobPosting] = []
        seen_ids: Set[str] = set()
        
        max_len = max(len(b) for b in source_buckets) if source_buckets else 0
        for i in range(max_len):
            for bucket in source_buckets:
                if i < len(bucket):
                    job = bucket[i]
                    if job.id not in seen_ids and not self.db.url_exists(job.url):
                        seen_ids.add(job.id)
                        final_jobs.append(job)
                        if len(final_jobs) >= self.max_jobs:
                            return final_jobs

        return final_jobs
