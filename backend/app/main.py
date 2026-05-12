import sys
import logging
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 确保能找到 app 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.config import settings, setup_logging

setup_logging()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router

app = FastAPI(title="智能旅行助手 API", version="1.0.0")
logger = logging.getLogger("uvicorn")

@app.on_event("startup")
async def startup_event():
    masked_key = None
    if settings.LLM_API_KEY:
        masked_key = "***" + settings.LLM_API_KEY[-4:]
    logger.info(f"LLM_MODEL_ID={settings.LLM_MODEL_ID}")
    logger.info(f"LLM_BASE_URL={settings.LLM_BASE_URL}")
    logger.info(f"LLM_API_KEY={masked_key}")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "智能旅行助手后端服务正在运行", "version": "1.0.0"}

@app.get("/health", tags=["健康检查"])
async def health_check():
    return {
        "status": "healthy",
        "service": "智能旅行助手 API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True, log_level=settings.LOG_LEVEL.lower())
