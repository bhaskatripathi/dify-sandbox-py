from fastapi import FastAPI, Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware  
from pydantic import BaseModel
from typing import Optional
import asyncio
from .executor import CodeExecutor
import os


# Configuration
API_KEY = os.getenv("API_KEY", "dify-sandbox")
MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", "100"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
WORKER_TIMEOUT = int(os.getenv("MAX_WORKERS", "15"))

app = FastAPI()
executor = CodeExecutor(timeout=WORKER_TIMEOUT, max_workers=MAX_WORKERS)

# Request Model
class CodeRequest(BaseModel):
    language: str
    code: str
    preload: Optional[str] = ""
    enable_network: Optional[bool] = False

# Authentication Middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/v1/sandbox"):
            api_key = request.headers.get("X-Api-Key")
            if not api_key or api_key != API_KEY:
                # Modified: Return JSONResponse instead of directly returning HTTPException
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={
                        "code": -401,
                        "message": "Unauthorized",
                        "data": None
                    }
                )
        return await call_next(request)

# Concurrency Control Middleware
class ConcurrencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.semaphore = asyncio.Semaphore(MAX_WORKERS)
        self.current_requests = 0

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/v1/sandbox/run"):
            if self.current_requests >= MAX_REQUESTS:
                return {
                    "code": -503,
                    "message": "Too many requests",
                    "data": None
                }
            
            self.current_requests += 1
            try:
                async with self.semaphore:
                    response = await call_next(request)
                return response
            finally:
                self.current_requests -= 1
        return await call_next(request)

# Add Middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(ConcurrencyMiddleware)

@app.get("/health")
async def health_check():
    return "ok"

@app.post("/v1/sandbox/run")
async def execute_code(request: CodeRequest):
    if request.language not in ["python3", "nodejs"]:
        return {
            "code": -400,
            "message": "unsupported language",
            "data": None
        }

    result = await executor.execute(request.code, request.language)
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "error": result["error"] or "",
            "stdout": result["output"] or "",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8194)