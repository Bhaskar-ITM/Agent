import requests
from typing import Any, Dict, Optional
from app.core.exceptions import ExternalServiceError
from app.core.config import settings


class HttpClient:
    def __init__(self, base_url: str, default_headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        # Bolt: Use requests.Session for connection pooling to reduce TCP/TLS handshake overhead
        self.session = requests.Session()

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
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            # Bolt: Utilize the shared session for the request to benefit from connection pooling
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=merged_headers,
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
