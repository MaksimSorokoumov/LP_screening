"""Basic rule-based analyzer for LP Screening.

Implements simple heuristic checks based on the parsed HTML data.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from app.collectors.http_fetcher import FetchResult
from app.parsers.html_parser import ParsedPage

__all__ = ["RuleStatus", "RuleResult", "evaluate_basic"]


class RuleStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class RuleResult:
    name: str
    status: RuleStatus
    message: str


# Helper functions -----------------------------------------------------------

def _range_status(value: int, low: int, high: int) -> RuleStatus:
    if low <= value <= high:
        return RuleStatus.OK
    return RuleStatus.WARNING


# Main evaluation -----------------------------------------------------------

def evaluate_basic(parsed: ParsedPage, fetch: FetchResult) -> List[RuleResult]:
    """Evaluate basic marketing/SEO rules and return list of results."""
    results: list[RuleResult] = []

    # SSL check
    if fetch.ssl_ok:
        results.append(RuleResult("SSL", RuleStatus.OK, "SSL-сертификат корректен."))
    else:
        results.append(
            RuleResult("SSL", RuleStatus.ERROR, "Сайт не использует корректный SSL-сертификат.")
        )

    # Title tag
    if parsed.title:
        if 20 <= len(parsed.title) <= 70:
            status = RuleStatus.OK
            msg = "Title присутствует и имеет оптимальную длину."
        else:
            status = RuleStatus.WARNING
            msg = f"Title длиной {len(parsed.title)} символов — рекомендуется 20–70."
    else:
        status = RuleStatus.ERROR
        msg = "Title отсутствует."
    results.append(RuleResult("Title", status, msg))

    # Meta description
    if parsed.meta_description:
        status = RuleStatus.OK if 50 <= len(parsed.meta_description) <= 160 else RuleStatus.WARNING
        msg = "Meta description присутствует." if status == RuleStatus.OK else "Meta description слишком короткий/длинный."
    else:
        status = RuleStatus.WARNING
        msg = "Meta description отсутствует."
    results.append(RuleResult("Meta description", status, msg))

    # Headings
    h1_count = len(parsed.headings.get(1, []))
    if h1_count == 1:
        status = RuleStatus.OK
        msg = "На странице ровно один H1."
    elif h1_count == 0:
        status = RuleStatus.ERROR
        msg = "H1 отсутствует."
    else:
        status = RuleStatus.WARNING
        msg = f"На странице {h1_count} тегов H1 — рекомендуется один."
    results.append(RuleResult("H1", status, msg))

    # Word count
    if parsed.word_count < 200:
        status = RuleStatus.WARNING
        msg = f"Текст слишком короткий ({parsed.word_count} слов). Рекомендуется ≥ 200."
    elif parsed.word_count > 2000:
        status = RuleStatus.WARNING
        msg = (
            f"Текст слишком длинный ({parsed.word_count} слов). Рекомендуется ≤ 2000 для лендинга."
        )
    else:
        status = RuleStatus.OK
        msg = "Длина текста оптимальна."
    results.append(RuleResult("Длина текста", status, msg))

    # Images alt
    if parsed.images_total == 0:
        results.append(RuleResult("Alt-тексты", RuleStatus.WARNING, "На странице нет изображений."))
    else:
        percent_missing = parsed.images_without_alt / parsed.images_total * 100
        if percent_missing == 0:
            status = RuleStatus.OK
            msg = "Все изображения имеют alt-текст."
        else:
            status = RuleStatus.WARNING if percent_missing < 50 else RuleStatus.ERROR
            msg = f"{percent_missing:.0f}% изображений без alt-текста."
        results.append(RuleResult("Alt-тексты", status, msg))

    # Forms
    if parsed.forms_count > 0:
        results.append(RuleResult("Формы", RuleStatus.OK, "На странице обнаружены формы."))
    else:
        results.append(RuleResult("Формы", RuleStatus.WARNING, "Формы для сбора лидов не найдены."))

    # Analytics
    if parsed.analytics:
        msg = "; ".join(parsed.analytics)
        results.append(RuleResult("Аналитика", RuleStatus.OK, f"Найдены скрипты: {msg}"))
    else:
        results.append(RuleResult("Аналитика", RuleStatus.WARNING, "Скрипты аналитики не обнаружены."))

    return results 