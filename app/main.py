from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, AppDomainError

app = FastAPI(
    title="Financial Tracker App",
    debug=settings.DEBUG,
)

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

@app.exception_handler(AppDomainError)
async def app_domain_error_handler(request: Request, exc: AppDomainError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # In a real app we would log the full traceback here using a logger
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
