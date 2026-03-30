"""Job scoring engine for kc_job_radar."""

import re
from dataclasses import dataclass

from .config import ScoutConfig
from .detail import JobDetail


@dataclass
class ScoreResult:
    salary_score: int       # 1-5
    company_score: int      # 1-5
    match_score: int        # 1-5
    redflag_score: int      # 1-5
    total: float            # weighted average
    light: str              # 🟢 🟡 🔴
    summary: str            # one-line summary


# Weights
W_SALARY = 0.30
W_COMPANY = 0.20
W_MATCH = 0.30
W_REDFLAG = 0.20


def _parse_annual(salary_desc: str) -> int | None:
    """Parse salary string to annual estimate."""
    if not salary_desc:
        return None
    s = salary_desc.replace(",", "").replace(" ", "")
    numbers = re.findall(r"\d+", s)
    if not numbers:
        return None
    val = int(numbers[0])
    if "年薪" in s:
        return val
    elif val > 200000:
        return val
    elif val > 0:
        return val * 12
    return None


def _score_salary(salary_desc: str) -> int:
    annual = _parse_annual(salary_desc)
    if annual is None:
        return 3  # 面議，中間值
    if annual >= 1200000:
        return 5
    if annual >= 1000000:
        return 4
    if annual >= 800000:
        return 2
    return 1


def _score_company(detail: JobDetail) -> int:
    emp = detail.employees.strip()

    # Check for listed company markers in industry
    if any(kw in detail.industry for kw in ["上市", "上櫃"]):
        return 5

    # Parse employee count
    if not emp or emp == "暫不提供":
        return 2  # unknown, conservative

    numbers = re.findall(r"\d+", emp)
    if numbers:
        count = int(numbers[0])
        if count >= 500:
            return 5
        if count >= 100:
            return 4
        if count >= 30:
            return 3
        if count >= 10:
            return 2
    return 1


def _score_match(detail: JobDetail, my_skills: list[str]) -> int:
    """Count how many of my_skills appear in JD text."""
    text = f"{detail.description} {' '.join(detail.specialties)} {' '.join(detail.skills)}".lower()
    hits = sum(1 for skill in my_skills if skill.lower() in text)
    if hits >= 5:
        return 5
    if hits >= 3:
        return 4
    if hits >= 2:
        return 3
    if hits >= 1:
        return 2
    return 1


def _score_redflags(detail: JobDetail, red_flags: list[str]) -> int:
    """Check for red flags in JD. Start at 5, deduct 1 per flag."""
    text = f"{detail.description} {detail.welfare}".lower()
    hits = sum(1 for flag in red_flags if flag.lower() in text)
    return max(1, 5 - hits)


def _make_summary(detail: JobDetail, match_hits: int, redflag_hits: int) -> str:
    """Generate one-line summary."""
    parts = []

    # Industry
    if detail.industry:
        parts.append(detail.industry)

    # Company size
    emp = detail.employees.strip()
    if emp and emp != "暫不提供":
        parts.append(f"{emp}" if emp.endswith("人") else f"{emp}人")

    # Key skills from JD (first 3 specialties)
    if detail.specialties:
        parts.append("要" + "/".join(detail.specialties[:3]))

    # Salary
    if detail.salary_desc:
        parts.append(detail.salary_desc)
    else:
        parts.append("薪資面議")

    # Red flags
    if redflag_hits > 0:
        parts.append(f"⚠️{redflag_hits}紅旗")

    return "、".join(parts)


def score_job(detail: JobDetail, config: ScoutConfig) -> ScoreResult:
    """Score a job across 4 dimensions."""
    s_salary = _score_salary(detail.salary_desc)
    s_company = _score_company(detail)
    s_match = _score_match(detail, config.my_skills)
    s_redflag = _score_redflags(detail, config.red_flags)

    total = round(
        s_salary * W_SALARY
        + s_company * W_COMPANY
        + s_match * W_MATCH
        + s_redflag * W_REDFLAG,
        1,
    )

    if total >= 3.5:
        light = "🟢"
    elif total >= 2.0:
        light = "🟡"
    else:
        light = "🔴"

    # Count hits for summary
    text = f"{detail.description} {' '.join(detail.specialties)} {' '.join(detail.skills)}".lower()
    match_hits = sum(1 for s in config.my_skills if s.lower() in text)
    redflag_text = f"{detail.description} {detail.welfare}".lower()
    redflag_hits = sum(1 for f in config.red_flags if f.lower() in redflag_text)

    summary = _make_summary(detail, match_hits, redflag_hits)

    return ScoreResult(
        salary_score=s_salary,
        company_score=s_company,
        match_score=s_match,
        redflag_score=s_redflag,
        total=total,
        light=light,
        summary=summary,
    )
