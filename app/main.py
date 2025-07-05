from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="LP Screening API",
    description="API для экспресс-аудита посадочных страниц.",
    version="0.1.0",
)


class AuditRequest(BaseModel):
    url: HttpUrl


class AuditResponse(BaseModel):
    message: str
    # Здесь будут результаты аудита
    # audit_results: dict


@app.post("/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """
    Запускает аудит для указанного URL.
    """
    # TODO: Реализовать логику аудита
    return AuditResponse(message=f"Аудит для {request.url} запущен. Результаты скоро будут здесь.")

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в LP Screening API!"} 