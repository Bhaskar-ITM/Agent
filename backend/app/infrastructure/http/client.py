import requests
from typing import Any, Dict, Optional
from app.core.exceptions import ExternalServiceError
from app.core.config import settings


class HttpClient:
    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        # Performance: Use requests.Session for connection pooling to reduce TCP/TLS overhead
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            # Use the pooled session for the request.
            # Session headers are automatically merged with the headers provided here.
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            if not response.ok:
                raise ExternalServiceError(
                    service=url,
                    status_code=response.status_code,
                    message=response.text,
                )

            return response.json() if response.content else None

        except requests.RequestException as e:
            raise ExternalServiceError(
                service=url,
                status_code=500,
                message=str(e),
            )
