"""HTTP fetcher for LP Screening.

Responsible for:
1. Retrieving the raw HTML of a landing page.
2. Basic SSL validation (checks https scheme and catches SSL errors).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.exceptions import SSLError, RequestException

__all__ = ["FetchResult", "fetch_html"]


@dataclass
class FetchResult:
    """Represents the result of fetching a page."""

    html: Optional[str]
    status_code: Optional[int]
    final_url: Optional[str]
    ssl_ok: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.html is not None


# Default headers – helps some sites respond with full HTML.
HEADERS: dict[str, str] = {
    "User-Agent": "LP-Screening/0.1 (+https://github.com/MaksimSorokoumov/LP_screening)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_html(url: str, timeout: int = 10, allow_redirects: bool = True) -> FetchResult:
    """Download the landing page and perform a quick SSL check.

    Args:
        url: Target page URL.
        timeout: Request timeout (seconds).
        allow_redirects: Follow redirects (True by default).

    Returns:
        FetchResult containing HTML (or error message) and SSL status.
    """
    parsed = urlparse(url)
    ssl_expected = parsed.scheme == "https"

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=allow_redirects)
        response.raise_for_status()

        # If we expected HTTPS but were downgraded to HTTP after redirects, mark ssl_ok=False.
        final_scheme = urlparse(response.url).scheme
        ssl_ok = ssl_expected and final_scheme == "https"

        return FetchResult(
            html=response.text,
            status_code=response.status_code,
            final_url=response.url,
            ssl_ok=ssl_ok,
        )

    except SSLError as exc:
        return FetchResult(
            html=None,
            status_code=None,
            final_url=None,
            ssl_ok=False,
            error=f"SSL error: {exc}",
        )
    except RequestException as exc:
        return FetchResult(
            html=None,
            status_code=None,
            final_url=None,
            ssl_ok=ssl_expected,  # Cannot determine; assume expected value
            error=f"Request error: {exc}",
        ) 