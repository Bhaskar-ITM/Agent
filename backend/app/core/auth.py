from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(request: Request, api_key: str | None = Security(api_key_header)) -> str:
    if settings.ENV == "test":
        return "test-bypass"

    # Callback endpoint has its own dedicated shared-secret guard.
    if request.url.path.endswith("/callback"):
        return "callback-path"

    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return api_key
