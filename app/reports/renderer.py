"""HTML report renderer for LP Screening."""
from __future__ import annotations

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.analyzers.basic import RuleResult, RuleStatus
from app.main import FetchInfo, ParseInfo, AIResponse  # type: ignore circular

# Template directory is relative to this file's location
_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_report(
    url: str,
    fetch: FetchInfo,
    parse: ParseInfo | None,
    rules: List[RuleResult] | None,
    ai: AIResponse | None,
) -> str:
    """Render HTML report using Jinja2 template."""
    tmpl = _ENV.get_template("report.html")
    return tmpl.render(url=url, fetch=fetch, parse=parse, rules=rules, ai=ai, RuleStatus=RuleStatus) 