"""104 job detail API client."""

import random
import time
from dataclasses import dataclass

import httpx

DETAIL_URL = "https://www.104.com.tw/job/ajax/content/{job_id}"
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


@dataclass
class JobDetail:
    job_name: str
    company: str
    industry: str
    employees: str
    salary_desc: str
    work_exp: str
    description: str
    specialties: list[str]  # tools/skills listed in JD
    skills: list[str]       # work skills
    welfare: str


def fetch_detail(job_id: str) -> JobDetail | None:
    """Fetch job detail from 104 API. Returns None if failed."""
    url = DETAIL_URL.format(job_id=job_id)
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": f"https://www.104.com.tw/job/{job_id}",
    }

    try:
        resp = httpx.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except Exception:
        return None

    header = data.get("header", {})
    condition = data.get("condition", {})
    job_detail = data.get("jobDetail", {})

    specialties = [s["description"] for s in condition.get("specialty", [])]
    skills = [s["description"] for s in condition.get("skill", [])]

    # Salary: try condition.salary first, fallback to header
    salary_desc = ""
    sal = condition.get("salary")
    if sal:
        salary_desc = sal if isinstance(sal, str) else str(sal)

    return JobDetail(
        job_name=header.get("jobName", ""),
        company=header.get("custName", ""),
        industry=data.get("industry", ""),
        employees=str(data.get("employees", "")),
        salary_desc=salary_desc,
        work_exp=condition.get("workExp", ""),
        description=job_detail.get("jobDescription", ""),
        specialties=specialties,
        skills=skills,
        welfare=data.get("welfare", {}).get("welfare", ""),
    )


def extract_job_id_from_url(url: str) -> str | None:
    """Extract job_id from 104 URL like https://www.104.com.tw/job/8zcio"""
    if "/job/" not in url:
        return None
    return url.rstrip("/").split("/job/")[-1].split("?")[0]
