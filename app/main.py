from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

from app.collectors.http_fetcher import fetch_html, FetchResult

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


@app.post("/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """
    Запускает аудит для указанного URL.
    """
    # Шаг 1. Забираем HTML и проверяем SSL
    fetch_result: FetchResult = fetch_html(request.url)

    # TODO: Передать HTML в последующие модули анализа

    fetch_info = FetchInfo(
        success=fetch_result.success,
        ssl_ok=fetch_result.ssl_ok,
        status_code=fetch_result.status_code,
        error=fetch_result.error,
    )

    return AuditResponse(
        message="Аудит выполнен. Дополнительные проверки будут добавлены позже.",
        fetch=fetch_info,
    )

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в LP Screening API!"} 