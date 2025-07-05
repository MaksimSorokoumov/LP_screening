from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.collectors.http_fetcher import fetch_html, FetchResult
from app.parsers.html_parser import parse_html, ParsedPage
from app.analyzers.basic import evaluate_basic, RuleResult, RuleStatus
from app.ai.gpt_client import analyze_with_gpt, AIResult
from app.reports.renderer import render_report

app = FastAPI(
    title="LP Screening API",
    description="API для экспресс-аудита посадочных страниц.",
    version="0.1.0",
)


class AuditRequest(BaseModel):
    url: HttpUrl


# -----------------------------
#   Response Models
# -----------------------------


class FetchInfo(BaseModel):
    success: bool
    ssl_ok: bool
    status_code: int | None = None
    error: str | None = None


class AuditResponse(BaseModel):
    message: str
    fetch: FetchInfo
    parse: "ParseInfo | None" = None
    rules: list["RuleResponse"] | None = None
    ai: "AIResponse | None" = None


class ParseInfo(BaseModel):
    title: str | None
    description_present: bool
    h1_count: int
    h2_count: int
    h3_count: int
    forms: int
    rules: list["RuleResponse"] | None = None


class RuleResponse(BaseModel):
    name: str
    status: RuleStatus
    message: str


class AIResponse(BaseModel):
    readability: str
    recommendations: list[str]


@app.post("/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """
    Запускает аудит для указанного URL.
    """
    # Шаг 1. Забираем HTML и проверяем SSL
    fetch_result: FetchResult = fetch_html(request.url)

    fetch_info = FetchInfo(
        success=fetch_result.success,
        ssl_ok=fetch_result.ssl_ok,
        status_code=fetch_result.status_code,
        error=fetch_result.error,
    )

    parse_info: ParseInfo | None = None
    if fetch_result.success and fetch_result.html:
        parsed: ParsedPage = parse_html(fetch_result.html, request.url)
        parse_info = ParseInfo(
            title=parsed.title,
            description_present=bool(parsed.meta_description),
            h1_count=len(parsed.headings.get(1, [])),
            h2_count=len(parsed.headings.get(2, [])),
            h3_count=len(parsed.headings.get(3, [])),
            forms=parsed.forms_count,
        )

    rules_resp: list[RuleResponse] | None = None
    if parse_info and fetch_result.success:
        rule_results: list[RuleResult] = evaluate_basic(parsed, fetch_result)
        rules_resp = [RuleResponse(name=r.name, status=r.status, message=r.message) for r in rule_results]

    ai_resp: AIResponse | None = None
    if parse_info and fetch_result.success:
        ai_result: AIResult | None = analyze_with_gpt(parsed)
        if ai_result:
            ai_resp = AIResponse(
                readability=ai_result.readability,
                recommendations=ai_result.recommendations,
            )

    return AuditResponse(
        message="Аудит выполнен.",
        fetch=fetch_info,
        parse=parse_info,
        rules=rules_resp,
        ai=ai_resp,
    )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Serve UI


@app.get("/", response_class=HTMLResponse)
def read_root():
    return FileResponse("app/static/index.html")


# -------------------------------------------------
#   HTML report endpoint
# -------------------------------------------------


@app.get("/audit/html", response_class=HTMLResponse)
async def audit_html(url: HttpUrl):
    """Возвращает HTML-отчёт для заданного URL."""
    # Повторяем те же шаги, что и в /audit
    fetch_result: FetchResult = fetch_html(str(url))

    parsed: ParsedPage | None = None
    if fetch_result.success and fetch_result.html:
        parsed = parse_html(fetch_result.html, str(url))

    rule_results: list[RuleResult] | None = None
    if parsed:
        rule_results = evaluate_basic(parsed, fetch_result)

    ai_result: AIResult | None = None
    if parsed:
        ai_result = analyze_with_gpt(parsed)

    # Build dataclass instances we already defined for renderer.
    fetch_info = FetchInfo(
        success=fetch_result.success,
        ssl_ok=fetch_result.ssl_ok,
        status_code=fetch_result.status_code,
        error=fetch_result.error,
    )

    parse_info: ParseInfo | None = None
    if parsed:
        parse_info = ParseInfo(
            title=parsed.title,
            description_present=bool(parsed.meta_description),
            h1_count=len(parsed.headings.get(1, [])),
            h2_count=len(parsed.headings.get(2, [])),
            h3_count=len(parsed.headings.get(3, [])),
            forms=parsed.forms_count,
        )

    ai_resp: AIResponse | None = None
    if ai_result:
        ai_resp = AIResponse(
            readability=ai_result.readability,
            recommendations=ai_result.recommendations,
        )

    html = render_report(
        url=str(url),
        fetch=fetch_info,
        parse=parse_info,
        rules=rule_results,
        ai=ai_resp,
    )

    return HTMLResponse(content=html) 