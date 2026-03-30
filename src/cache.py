"""File cache with TTL for kc_job_radar."""

import hashlib
import json
import time
from pathlib import Path
from dataclasses import asdict

from .models import Job

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_TTL = 12 * 60 * 60  # 12 hours (half day)

FETCH_CACHE = CACHE_DIR / "fetched_jobs.json"
FILTER_CACHE = CACHE_DIR / "filtered_jobs.json"


def _config_hash(config_section: dict) -> str:
    """Hash a config section to detect changes."""
    raw = json.dumps(config_section, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _is_fresh(path: Path, config_hash: str | None = None) -> bool:
    """Check if cache file exists, is within TTL, and config hasn't changed."""
    if not path.exists():
        return False

    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

    # Check structure
    if not isinstance(wrapper, dict) or "timestamp" not in wrapper:
        return False

    # Check TTL
    age = time.time() - wrapper["timestamp"]
    if age >= CACHE_TTL:
        return False

    # Check config hash (if provided)
    if config_hash and wrapper.get("config_hash") != config_hash:
        return False

    return True


def _save(path: Path, jobs: list[Job], config_hash: str | None = None) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    wrapper = {
        "timestamp": time.time(),
        "config_hash": config_hash,
        "count": len(jobs),
        "data": [asdict(j) for j in jobs],
    }
    path.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")


def _load(path: Path) -> tuple[list[Job], float]:
    """Load cache. Returns (jobs, timestamp)."""
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    jobs = [Job(**d) for d in wrapper["data"]]
    return jobs, wrapper["timestamp"]


def load_fetch_cache(search_config: dict) -> list[Job] | None:
    h = _config_hash(search_config)
    if _is_fresh(FETCH_CACHE, config_hash=h):
        jobs, ts = _load(FETCH_CACHE)
        age_min = int((time.time() - ts) / 60)
        print(f"  📦 使用 fetch 快取（{len(jobs)} 筆，{age_min} 分鐘前）")
        return jobs
    return None


def save_fetch_cache(jobs: list[Job], search_config: dict) -> None:
    _save(FETCH_CACHE, jobs, config_hash=_config_hash(search_config))


def load_filter_cache(filter_config: dict) -> list[Job] | None:
    h = _config_hash(filter_config)
    if _is_fresh(FILTER_CACHE, config_hash=h):
        jobs, ts = _load(FILTER_CACHE)
        age_min = int((time.time() - ts) / 60)
        print(f"  📦 使用 filter 快取（{len(jobs)} 筆，{age_min} 分鐘前）")
        return jobs
    return None


def save_filter_cache(jobs: list[Job], filter_config: dict) -> None:
    _save(FILTER_CACHE, jobs, config_hash=_config_hash(filter_config))
