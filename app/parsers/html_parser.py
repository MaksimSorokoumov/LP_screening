"""HTML parsing utilities for LP Screening.

Extracts key information from the landing page HTML for subsequent rule-based analysis.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

__all__ = ["ParsedPage", "parse_html"]


@dataclass
class ParsedPage:
    """Structured representation of the parsed landing page."""

    title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]

    headings: dict[int, list[str]]  # level -> list of texts
    images_total: int
    images_without_alt: int

    forms_count: int
    external_links: int
    external_nofollow: int

    analytics: List[str] = field(default_factory=list)

    text_content: str = ""

    @property
    def word_count(self) -> int:
        return len(self.text_content.split())


# Patterns to detect popular analytics scripts
_ANALYTICS_PATTERNS: dict[str, str] = {
    "googletagmanager": "Google Tag Manager",
    "analytics.js": "Google Analytics",
    "gtag/js": "Google Analytics (gtag)",
    "mc.yandex": "Yandex Metrika",
    "metrika": "Yandex Metrika",
}


def _detect_analytics(soup: BeautifulSoup) -> List[str]:
    found: set[str] = set()
    for script in soup.find_all("script"):
        src = script.get("src", "").lower()
        inline_content = script.string or ""
        for pattern, name in _ANALYTICS_PATTERNS.items():
            if pattern in src or pattern in inline_content.lower():
                found.add(name)
    return sorted(found)


def parse_html(html: str, page_url: str | None = None) -> ParsedPage:
    """Parse HTML and extract structured information."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style to simplify text extraction
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    title_tag = soup.title
    title = title_tag.string.strip() if title_tag and title_tag.string else None

    def _meta(name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    meta_description = _meta("description")
    meta_keywords = _meta("keywords")

    headings: dict[int, list[str]] = defaultdict(list)
    for level in (1, 2, 3):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            if text:
                headings[level].append(text)

    imgs = soup.find_all("img")
    images_total = len(imgs)
    images_without_alt = sum(1 for img in imgs if not img.get("alt"))

    forms_count = len(soup.find_all("form"))

    # External links (absolute URLs pointing outside current domain)
    external_links = 0
    external_nofollow = 0
    domain = urlparse(page_url).netloc if page_url else ""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        parsed = urlparse(href)
        if not parsed.netloc:  # relative URL => internal
            continue
        if domain and parsed.netloc.endswith(domain):
            continue  # internal link within same domain
        external_links += 1
        rel_vals = {val.lower() for val in a.get("rel", [])}
        if "nofollow" in rel_vals:
            external_nofollow += 1

    analytics = _detect_analytics(soup)

    text_content = soup.get_text(" ", strip=True)

    return ParsedPage(
        title=title,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        headings=dict(headings),
        images_total=images_total,
        images_without_alt=images_without_alt,
        forms_count=forms_count,
        external_links=external_links,
        external_nofollow=external_nofollow,
        analytics=analytics,
        text_content=text_content,
    ) 