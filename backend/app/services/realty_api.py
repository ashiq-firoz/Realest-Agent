import httpx
from typing import Any, Dict, Optional

from app.config import settings

class RealtyApiService:
    def __init__(self):
        self.base_url = f"https://{settings.REALTY_AU_HOST}"
        self.headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": settings.REALTY_AU_HOST,
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def auto_complete(self, query: str) -> Dict[str, Any]:
        return await self._get("/auto-complete", {"query": query})

    async def properties_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get("/properties/list", params)

    async def properties_detail(self, id: str) -> Dict[str, Any]:
        return await self._get("/properties/detail", {"id": id})

    async def properties_v3_lookup(self, id: str) -> Dict[str, Any]:
        return await self._get("/properties/v3/lookup", {"id": id})

    async def schools_list(self, lat: float, lon: float) -> Dict[str, Any]:
        return await self._get("/schools/list", {"lat": lat, "lon": lon})

    async def agency_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get("/agency/list", params)

    async def agency_detail(self, agencyId: str) -> Dict[str, Any]:
        return await self._get("/agency/detail", {"agencyId": agencyId})

    async def agency_get_listings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get("/agency/get-listings", params)

    async def agents_v2_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get("/agents/v2/list", params)

    async def agents_detail(self, id: str) -> Dict[str, Any]:
        return await self._get("/agents/detail", {"id": id})

    async def agents_get_listings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get("/agents/get-listings", params)

realty_api = RealtyApiService()
