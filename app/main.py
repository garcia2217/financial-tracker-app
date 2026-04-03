from contextlib import asynccontextmanager
from sqlalchemy import text

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import ResourceNotFoundError, AppDomainError
from app.routers import telegram_router, financial_overview_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Successfully connected to the database!")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        raise e
        
    yield
    
    await engine.dispose()
    print("🛑 Database connection closed.")

app = FastAPI(
    title="Financial Tracker App",
    debug=settings.DEBUG,
    lifespan=lifespan,
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

import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Print the error out to the console so we can see why it's failing!
    print(f"Global Exception caught on {request.url.path}:")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(telegram_router)
app.include_router(financial_overview_router)