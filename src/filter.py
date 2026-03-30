"""Filter engine for kc_job_radar."""

import re

from .config import FilterConfig
from .models import Job


def _parse_annual_salary(salary_str: str) -> int | None:
    """Parse salary string to estimated annual amount. Returns None if unparseable (treated as negotiable)."""
    if not salary_str or salary_str == "面議":
        return None

    # Remove commas and spaces
    s = salary_str.replace(",", "").replace(" ", "")

    # Try to find numbers
    numbers = re.findall(r"[\d,]+", s)
    if not numbers:
        return None

    numbers = [int(n.replace(",", "")) for n in numbers]

    # Detect monthly vs annual
    if "年薪" in s:
        # Use the lower bound of annual salary
        return numbers[0]
    elif "月薪" in s or "元/月" in s:
        return numbers[0] * 12
    else:
        # Heuristic: if number > 200000, likely annual; otherwise monthly
        val = numbers[0]
        if val > 200000:
            return val
        elif val > 0:
            return val * 12

    return None


def filter_jobs(jobs: list[Job], config: FilterConfig) -> list[Job]:
    """Filter jobs by salary and exclude keywords."""
    result = []

    for job in jobs:
        # Exclude keywords check (title + company)
        text = f"{job.title} {job.company}".lower()
        if any(kw.lower() in text for kw in config.exclude_keywords):
            continue

        # Location check
        if config.allowed_locations:
            if not any(loc in job.location for loc in config.allowed_locations):
                continue

        # Salary check
        annual = _parse_annual_salary(job.salary)
        if annual is None:
            # Negotiable / unparseable
            if config.accept_negotiable:
                result.append(job)
        elif annual >= config.min_salary_annual:
            result.append(job)

    return result
