"""API client for the LMS backend.

Provides methods to query the LMS API with Bearer token authentication.
Handles errors gracefully and returns user-friendly messages.
"""

import httpx
from typing import Any


class APIError(Exception):
    """Base exception for API errors."""
    pass


class ConnectionError(APIError):
    """Raised when the backend is unreachable."""
    pass


class APIClient:
    """Client for the LMS backend API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._headers = {"Authorization": f"Bearer {api_key}"}
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an HTTP request to the backend.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/items/")
            **kwargs: Additional arguments for httpx
            
        Returns:
            JSON response data
            
        Raises:
            ConnectionError: If backend is unreachable
            APIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers,
                    timeout=10.0,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"connection refused ({self.base_url}). Check that the services are running.")
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down.")
        except httpx.TimeoutException:
            raise APIError(f"request timeout ({self.base_url}). The backend may be overloaded.")
        except httpx.HTTPError as e:
            raise APIError(f"HTTP error: {str(e)}")
    
    async def health_check(self) -> dict:
        """Check if the backend is healthy.
        
        Returns:
            Dict with 'status' and 'item_count' keys
        """
        try:
            items = await self._request("GET", "/items/")
            return {
                "status": "healthy",
                "item_count": len(items) if isinstance(items, list) else 0
            }
        except ConnectionError:
            raise
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"unexpected error: {str(e)}")
    
    async def get_labs(self) -> list[dict]:
        """Get all available labs.
        
        Returns:
            List of lab dictionaries with 'id', 'name', 'title' keys
        """
        try:
            items = await self._request("GET", "/items/")
            # Filter for labs (type might be 'lab' or have lab-like structure)
            labs = []
            for item in items:
                if isinstance(item, dict):
                    labs.append({
                        "id": item.get("id", item.get("name", "unknown")),
                        "name": item.get("name", "Unknown"),
                        "title": item.get("title", item.get("description", ""))
                    })
            return labs
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch labs: {str(e)}")
    
    async def get_pass_rates(self, lab: str) -> dict:
        """Get pass rates for a specific lab.
        
        Args:
            lab: Lab identifier (e.g., "lab-04")
            
        Returns:
            Dict with task names and pass rates
        """
        try:
            data = await self._request("GET", "/analytics/pass-rates", params={"lab": lab})
            return data
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch pass rates for {lab}: {str(e)}")
    
    async def get_learners(self) -> list[dict]:
        """Get all enrolled learners."""
        try:
            return await self._request("GET", "/learners/")
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch learners: {str(e)}")
    
    async def get_scores(self, lab: str) -> dict:
        """Get score distribution for a lab."""
        try:
            return await self._request("GET", "/analytics/scores", params={"lab": lab})
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch scores for {lab}: {str(e)}")
    
    async def get_timeline(self, lab: str) -> dict:
        """Get submission timeline for a lab."""
        try:
            return await self._request("GET", "/analytics/timeline", params={"lab": lab})
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch timeline for {lab}: {str(e)}")
    
    async def get_groups(self, lab: str) -> list[dict]:
        """Get per-group performance for a lab."""
        try:
            return await self._request("GET", "/analytics/groups", params={"lab": lab})
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch groups for {lab}: {str(e)}")
    
    async def get_top_learners(self, lab: str, limit: int = 5) -> list[dict]:
        """Get top learners for a lab.
        
        Args:
            lab: Lab identifier
            limit: Number of top learners to return
        """
        try:
            return await self._request(
                "GET",
                "/analytics/top-learners",
                params={"lab": lab, "limit": limit}
            )
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch top learners for {lab}: {str(e)}")
    
    async def get_completion_rate(self, lab: str) -> dict:
        """Get completion rate for a lab."""
        try:
            return await self._request("GET", "/analytics/completion-rate", params={"lab": lab})
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to fetch completion rate for {lab}: {str(e)}")
    
    async def sync_pipeline(self) -> dict:
        """Trigger ETL sync."""
        try:
            return await self._request("POST", "/pipeline/sync", json={})
        except (ConnectionError, APIError):
            raise
        except Exception as e:
            raise APIError(f"failed to sync pipeline: {str(e)}")
