from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEY = os.getenv("API_KEY")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if API_KEY is None:
            # If no API key configured, skip auth (for backward compatibility)
            return await call_next(request)
        # Skip auth for health check and root endpoint
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        key = request.headers.get("X-API-Key")
        if key == API_KEY:
            return await call_next(request)
        raise HTTPException(status_code=401, detail="Invalid API Key")