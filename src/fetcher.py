"""104 job search API client."""

import random
import time

import httpx

from .config import Config
from .models import Job

SEARCH_URL = "https://www.104.com.tw/jobs/search/api/jobs"
SEARCH_REFERER = "https://www.104.com.tw/jobs/search/"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


def _parse_job(raw: dict) -> Job | None:
    """Parse a single job entry from 104 search API response."""
    link = raw.get("link", {})
    job_url = link.get("job", "")

    # Extract job_id from jobNo field or URL
    job_id = str(raw.get("jobNo", ""))
    if not job_id and job_url:
        # Fallback: parse from URL like "https://www.104.com.tw/job/8zcio"
        job_id = job_url.rstrip("/").split("/")[-1]

    if not job_id:
        return None

    return Job(
        job_id=job_id,
        title=raw.get("jobName", "").strip(),
        company=raw.get("custName", "").strip(),
        location=raw.get("jobAddrNoDesc", "").strip(),
        salary=raw.get("salaryDesc", "").strip() or _format_salary(raw),
        url=job_url if job_url.startswith("http") else f"https://www.104.com.tw/job/{job_id}",
    )


def _format_salary(raw: dict) -> str:
    """Format salary from salaryLow/salaryHigh when salaryDesc is empty."""
    low = raw.get("salaryLow", 0)
    high = raw.get("salaryHigh", 0)
    if low and high:
        return f"{low:,}~{high:,}"
    if low:
        return f"{low:,} 以上"
    return "面議"


def _search_page(
    client: httpx.Client,
    keyword: str,
    area: str,
    page: int,
) -> tuple[list[dict], int]:
    """Fetch one page of search results. Returns (job list, last page number)."""
    params = {
        "keyword": keyword,
        "page": page,
        "ro": 0,
        "order": 15,
        "asc": 0,
    }
    if area:
        params["area"] = area

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": SEARCH_REFERER,
        "Accept": "application/json, text/plain, */*",
    }

    resp = client.get(SEARCH_URL, params=params, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    job_list = result.get("data", [])
    pagination = result.get("metadata", {}).get("pagination", {})
    last_page = pagination.get("lastPage", 0)

    return job_list, last_page


def fetch_jobs(config: Config) -> list[Job]:
    """Fetch jobs from 104 based on config. Returns deduplicated Job list."""
    seen_ids: set[str] = set()
    all_jobs: list[Job] = []
    rate = config.rate_limit

    with httpx.Client(timeout=30) as client:
        for keyword in config.search.keywords:
            for area in config.search.areas:
                for page in range(1, config.search.max_pages + 1):
                    area_label = area if area else "全區"
                    print(f"  搜尋: {keyword} | {area_label} | page={page}")

                    try:
                        raw_list, last_page = _search_page(
                            client, keyword, area, page
                        )
                    except httpx.HTTPStatusError as e:
                        print(f"  ⚠️ HTTP {e.response.status_code}，跳過")
                        break
                    except Exception as e:
                        print(f"  ⚠️ 請求失敗: {e}，跳過")
                        break

                    if not raw_list:
                        print(f"  空頁，停止此組合")
                        break

                    for raw in raw_list:
                        job = _parse_job(raw)
                        if job and job.job_id not in seen_ids:
                            seen_ids.add(job.job_id)
                            all_jobs.append(job)

                    if page >= last_page:
                        break

                    # Rate limit
                    sleep_time = random.uniform(rate.min_sleep, rate.max_sleep)
                    time.sleep(sleep_time)

    return all_jobs
