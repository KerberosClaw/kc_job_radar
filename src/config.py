"""Config loader for kc_job_radar."""

import sys
from pathlib import Path
from dataclasses import dataclass, field

import yaml


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
SAMPLE_PATH = Path(__file__).parent.parent / "config.sample.yaml"


@dataclass
class SearchConfig:
    keywords: list[str]
    areas: list[str]
    max_pages: int = 3


@dataclass
class FilterConfig:
    min_salary_annual: int = 1000000
    accept_negotiable: bool = True
    exclude_keywords: list[str] = field(default_factory=list)
    allowed_locations: list[str] = field(default_factory=list)
    max_experience_years: int | None = None


@dataclass
class RateLimitConfig:
    min_sleep: int = 3
    max_sleep: int = 8


@dataclass
class GoogleSheetConfig:
    sheet_id: str
    credentials_path: str
    radar_tab: str = "雷達"
    active_tab: str = "追蹤中"
    archive_tab: str = "封存"


@dataclass
class ScoutConfig:
    my_skills: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str


@dataclass
class GmailConfig:
    client_secret_path: str
    token_path: str
    watch_sender: str = "104news@ms1.104.com.tw"


@dataclass
class Config:
    search: SearchConfig
    filter: FilterConfig
    rate_limit: RateLimitConfig
    google_sheet: GoogleSheetConfig | None = None
    scout: ScoutConfig | None = None
    telegram: TelegramConfig | None = None
    gmail: GmailConfig | None = None


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        print(f"❌ 找不到 config.yaml")
        print(f"   請複製 config.sample.yaml 並填入你的設定：")
        print(f"   cp {SAMPLE_PATH} {CONFIG_PATH}")
        sys.exit(1)

    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    search_raw = raw.get("search")
    if not search_raw or not search_raw.get("keywords"):
        print("❌ config.yaml 缺少 search.keywords")
        sys.exit(1)

    search = SearchConfig(
        keywords=search_raw["keywords"],
        areas=search_raw.get("areas", ["6001001000"]),
        max_pages=search_raw.get("max_pages", 3),
    )

    filter_raw = raw.get("filter", {})
    filter_cfg = FilterConfig(
        min_salary_annual=filter_raw.get("min_salary_annual", 1000000),
        accept_negotiable=filter_raw.get("accept_negotiable", True),
        exclude_keywords=filter_raw.get("exclude_keywords", []),
        allowed_locations=filter_raw.get("allowed_locations", []),
        max_experience_years=filter_raw.get("max_experience_years"),
    )

    rate_raw = raw.get("rate_limit", {})
    rate_limit = RateLimitConfig(
        min_sleep=rate_raw.get("min_sleep", 3),
        max_sleep=rate_raw.get("max_sleep", 8),
    )

    gs_raw = raw.get("google_sheet")
    google_sheet = None
    if gs_raw and gs_raw.get("sheet_id"):
        google_sheet = GoogleSheetConfig(
            sheet_id=gs_raw["sheet_id"],
            credentials_path=gs_raw.get("credentials_path", "credentials.json"),
            radar_tab=gs_raw.get("radar_tab", "雷達"),
            active_tab=gs_raw.get("active_tab", "追蹤中"),
            archive_tab=gs_raw.get("archive_tab", "封存"),
        )

    scout_raw = raw.get("scout")
    scout = None
    if scout_raw:
        scout = ScoutConfig(
            my_skills=scout_raw.get("my_skills", []),
            red_flags=scout_raw.get("red_flags", []),
        )

    tg_raw = raw.get("telegram")
    telegram = None
    if tg_raw and tg_raw.get("bot_token"):
        telegram = TelegramConfig(
            bot_token=tg_raw["bot_token"],
            chat_id=tg_raw["chat_id"],
        )

    gmail_raw = raw.get("gmail")
    gmail = None
    if gmail_raw and gmail_raw.get("client_secret_path"):
        gmail = GmailConfig(
            client_secret_path=gmail_raw["client_secret_path"],
            token_path=gmail_raw.get("token_path", "gmail_token.json"),
            watch_sender=gmail_raw.get("watch_sender", "104news@ms1.104.com.tw"),
        )

    return Config(
        search=search,
        filter=filter_cfg,
        rate_limit=rate_limit,
        google_sheet=google_sheet,
        scout=scout,
        telegram=telegram,
        gmail=gmail,
    )
