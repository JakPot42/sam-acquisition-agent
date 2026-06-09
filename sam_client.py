"""
sam_client.py — SAM.gov Opportunities API wrapper.

Fetches contract opportunities from the US government's public procurement
database. All data returned is publicly available; no authentication beyond
the free api.data.gov key is required.
"""

from __future__ import annotations

import datetime as _dt

import httpx
from config import SAM_API_KEY, SAM_BASE_URL, SAM_DEFAULT_LIMIT


class SAMAPIError(Exception):
    pass


def _date_range(days_back: int = 90) -> tuple[str, str]:
    """Return (postedFrom, postedTo) strings in MM/dd/yyyy format.
    Both are required by the SAM.gov API; max span is 1 year."""
    today = _dt.date.today()
    start = today - _dt.timedelta(days=days_back)
    fmt = "%m/%d/%Y"
    return start.strftime(fmt), today.strftime(fmt)


def search_opportunities(
    query: str,
    limit: int = SAM_DEFAULT_LIMIT,
    offset: int = 0,
    active_only: bool = True,
) -> dict:
    """Search SAM.gov for contract opportunities matching a keyword query."""
    posted_from, posted_to = _date_range(90)
    params: dict = {
        "api_key": SAM_API_KEY,
        "q": query,
        "limit": limit,
        "offset": offset,
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    if active_only:
        params["status"] = "active"

    try:
        response = httpx.get(SAM_BASE_URL, params=params, timeout=45)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            raise SAMAPIError(
                "SAM.gov daily API quota reached. The free tier allows a limited number of "
                "requests per day. Quota resets at midnight UTC — try again tomorrow, or "
                "use the demo data below to explore the app in the meantime."
            ) from exc
        if status == 403:
            raise SAMAPIError(
                "SAM.gov API key rejected (403). Check that your SAM_API_KEY in .env matches "
                "the Public API Key from your SAM.gov Account Details page."
            ) from exc
        raise SAMAPIError(f"SAM.gov API error {status} — try again in a moment.") from exc
    except httpx.TimeoutException as exc:
        raise SAMAPIError(
            "SAM.gov API timed out (the public API can be slow). Try your search again."
        ) from exc
    except httpx.RequestError as exc:
        raise SAMAPIError(f"Could not reach SAM.gov: {exc}") from exc


def get_opportunity(notice_id: str) -> dict | None:
    """Fetch a single opportunity by its notice ID."""
    posted_from, posted_to = _date_range(90)
    params = {
        "api_key": SAM_API_KEY,
        "noticeid": notice_id,
        "limit": 1,
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    try:
        response = httpx.get(SAM_BASE_URL, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        hits = data.get("opportunitiesData", [])
        return hits[0] if hits else None
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise SAMAPIError(f"SAM.gov API error: {exc}") from exc


def build_opportunity_text(opp: dict) -> str:
    """Flatten a SAM.gov opportunity dict into a text block for Claude to analyze."""
    parts = [
        f"TITLE: {opp.get('title', 'N/A')}",
        f"SOLICITATION NUMBER: {opp.get('solicitationNumber', 'N/A')}",
        f"AGENCY: {opp.get('fullParentPathName', opp.get('organizationHierarchy', 'N/A'))}",
        f"NAICS CODE: {opp.get('naicsCode', 'N/A')}",
        f"SET-ASIDE TYPE: {opp.get('typeOfSetAside', 'N/A')}",
        f"POSTED DATE: {opp.get('postedDate', 'N/A')}",
        f"RESPONSE DEADLINE: {opp.get('responseDeadLine', 'N/A')}",
        f"PLACE OF PERFORMANCE: {opp.get('placeOfPerformance', {}).get('city', {}).get('name', 'N/A')}",
        "",
        "DESCRIPTION:",
        opp.get("description", "No description available."),
    ]
    return "\n".join(parts)
