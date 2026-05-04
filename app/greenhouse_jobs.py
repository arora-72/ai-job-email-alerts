from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime
from typing import Any

from .config import (
    ARCHIVED_SHEETS_TAB,
    FIT_SCORE_MINIMUM,
    GREENHOUSE_COMPANIES,
    MAX_JOBS_PER_DAY,
    OLLAMA_APPROVED_MAX_PER_RUN,
    OLLAMA_MIN_FIT_SCORE,
    OLLAMA_SHORTLIST_SIZE,
)
from .job_identity import build_job_identity_signatures
from .jobspy_jobs import (
    get_remaining_daily_slots,
    is_allowed_title,
    log,
    normalize_text,
    print_jobspy_jobs,
    save_partitioned_jobspy_jobs_to_google_sheets,
    score_job_fit,
)
from .ollama_fit import ollama_is_configured, split_jobs_with_ollama

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    return " ".join(text.split())


def fetch_greenhouse_jobs(slug: str) -> list[dict[str, Any]]:
    url = f"{GREENHOUSE_API_BASE}/{slug}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("jobs", [])
    except Exception as exc:
        log(f"Greenhouse fetch failed for '{slug}': {exc}")
        return []


def normalize_greenhouse_job(
    raw: dict[str, Any], company_name: str, slug: str
) -> dict[str, str] | None:
    title = normalize_text(raw.get("title"))
    link = normalize_text(raw.get("absolute_url"))
    location = normalize_text(raw.get("location", {}).get("name") or "")

    if not title or not link:
        return None

    description = strip_html(raw.get("content") or "")

    updated_at = normalize_text(raw.get("updated_at"))
    try:
        posted_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        posted_at = posted_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        posted_at = updated_at

    return {
        "title": title,
        "company": company_name,
        "location": location or "Unknown location",
        "link": link,
        "company_link": f"https://boards.greenhouse.io/{slug}",
        "source": "greenhouse",
        "posted_at": posted_at,
        "company_num_employees": "",
        "description": description,
    }


def search_greenhouse_jobs(
    companies: dict[str, str] | None = None,
    minimum_fit_score: int = FIT_SCORE_MINIMUM,
) -> list[dict[str, str]]:
    targets = companies or GREENHOUSE_COMPANIES
    collected: list[dict[str, str]] = []
    seen_keys: set[tuple[str, ...]] = set()

    for company_name, slug in targets.items():
        log(f"Fetching Greenhouse jobs for {company_name} ({slug})")
        raw_jobs = fetch_greenhouse_jobs(slug)

        for raw in raw_jobs:
            if not is_allowed_title(raw.get("title")):
                continue

            normalized = normalize_greenhouse_job(raw, company_name, slug)
            if normalized is None:
                continue

            fit_score = score_job_fit(normalized)
            if fit_score < minimum_fit_score:
                continue
            normalized["fit_score"] = str(fit_score)

            signatures = build_job_identity_signatures(
                company_name=normalized["company"],
                role_name=normalized["title"],
                location=normalized["location"],
                job_application_link=normalized["link"],
            )
            if any(sig in seen_keys for sig in signatures):
                continue

            seen_keys.update(signatures)
            collected.append(normalized)
            log(
                f"Extracted Greenhouse job: {normalized['title']} at {normalized['company']} "
                f"in {normalized['location']} (fit {fit_score})"
            )

    collected.sort(
        key=lambda job: (
            -int(job.get("fit_score", "0") or 0),
            job.get("posted_at") == "",
            job.get("posted_at", ""),
            job.get("company", "").lower(),
        ),
    )
    return collected


def run_greenhouse_job_search(
    max_results: int = 8,
    max_jobs_per_day: int = MAX_JOBS_PER_DAY,
    save_to_sheets: bool = False,
    sheets_credentials_path: str = "",
    sheets_spreadsheet_ref: str = "",
    sheets_tab_name: str = "Jobs",
    archived_sheets_tab_name: str = ARCHIVED_SHEETS_TAB,
    companies: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    remaining_daily_slots = max_jobs_per_day

    if save_to_sheets:
        remaining_daily_slots = get_remaining_daily_slots(
            credentials_path=sheets_credentials_path,
            spreadsheet_ref=sheets_spreadsheet_ref,
            worksheet_name=sheets_tab_name,
            max_jobs_per_day=max_jobs_per_day,
        )
        if remaining_daily_slots <= 0:
            log(f"Daily cap reached for {sheets_tab_name}. Skipping Greenhouse search.")
            return []

    jobs = search_greenhouse_jobs(companies=companies)
    approved_jobs = jobs[:max_results]
    archived_jobs: list[dict[str, str]] = []

    if ollama_is_configured():
        approved_jobs, archived_jobs = split_jobs_with_ollama(
            job_list=jobs,
            shortlist_size=max(max_results, OLLAMA_SHORTLIST_SIZE),
            minimum_fit_score=OLLAMA_MIN_FIT_SCORE,
        )
        approved_jobs = approved_jobs[: min(max_results, OLLAMA_APPROVED_MAX_PER_RUN, remaining_daily_slots)]
    else:
        approved_jobs = approved_jobs[: min(max_results, OLLAMA_APPROVED_MAX_PER_RUN, remaining_daily_slots)]

    print_jobspy_jobs(approved_jobs)
    if archived_jobs:
        log(f"Archived {len(archived_jobs)} Greenhouse jobs rejected by AI.")

    if save_to_sheets:
        save_partitioned_jobspy_jobs_to_google_sheets(
            approved_jobs=approved_jobs,
            archived_jobs=archived_jobs,
            credentials_path=sheets_credentials_path,
            spreadsheet_ref=sheets_spreadsheet_ref,
            approved_worksheet_name=sheets_tab_name,
            archived_worksheet_name=archived_sheets_tab_name,
            max_jobs_per_day=max_jobs_per_day,
        )

    return approved_jobs
