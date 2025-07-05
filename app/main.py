from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

from app.collectors.http_fetcher import fetch_html, FetchResult
from app.parsers.html_parser import parse_html, ParsedPage

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


class ParseInfo(BaseModel):
    title: str | None
    description_present: bool
    h1_count: int
    h2_count: int
    h3_count: int
    forms: int


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

    return AuditResponse(
        message="Аудит выполнен. Дополнительные проверки будут добавлены позже.",
        fetch=fetch_info,
        parse=parse_info,
    )

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в LP Screening API!"} 