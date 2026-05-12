import logging
import httpx
from typing import List, Dict, Any, Optional

from backend.app.config import settings

logger = logging.getLogger(__name__)

class OnlineAttractionsService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.amap_api_key = settings.AMAP_API_KEY
    
    async def search_attractions(self, keyword: str, city: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = []
            
            results.extend(await self._search_by_amap(keyword, city))
            
            results.extend(await self._search_by_wiki(keyword))
            
            results.extend(self._search_local_fallback(keyword, city))
            
            seen = set()
            unique_results = []
            for r in results:
                name = r.get('name', '')
                if name not in seen:
                    seen.add(name)
                    unique_results.append(r)
            
            return unique_results[:limit]
        except Exception as e:
            logger.error(f"Failed to search attractions: {e}")
            return self._search_local_fallback(keyword, city)
    
    async def _search_by_amap(self, keyword: str, city: str = None) -> List[Dict[str, Any]]:
        if not self.amap_api_key:
            logger.warning("AMAP_API_KEY not configured, skipping amap search")
            return []
        
        try:
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                "keywords": keyword,
                "city": city or "全国",
                "types": "110000|110100|110200|110300|110400|110500",
                "offset": 10,
                "page": 1,
                "extensions": "all",
                "key": self.amap_api_key
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get('status') == '1':
                results = []
                for poi in data.get('pois', []):
                    results.append({
                        "name": poi.get('name', ''),
                        "address": poi.get('address', ''),
                        "longitude": float(poi.get('location', '0,0').split(',')[0]),
                        "latitude": float(poi.get('location', '0,0').split(',')[1]),
                        "description": poi.get('type', '') + " - " + poi.get('address', ''),
                        "ticket_price": 0,
                        "open_time": "",
                        "visit_duration": 120,
                        "popularity": 3,
                        "type": self._convert_type(poi.get('type', '')),
                        "source": "amap"
                    })
                return results
        except Exception as e:
            logger.warning(f"Amap API failed: {e}")
        
        return []
    
    async def _search_by_wiki(self, keyword: str) -> List[Dict[str, Any]]:
        try:
            url = "https://zh.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": keyword + " 景点",
                "srlimit": 5,
                "format": "json"
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            results = []
            for item in data.get('query', {}).get('search', []):
                results.append({
                    "name": item.get('title', ''),
                    "address": "",
                    "longitude": 0,
                    "latitude": 0,
                    "description": "维基百科收录的景点",
                    "ticket_price": 0,
                    "open_time": "",
                    "visit_duration": 180,
                    "popularity": 4,
                    "type": "人文古迹",
                    "source": "wikipedia"
                })
            return results
        except Exception as e:
            logger.warning(f"Wikipedia API failed: {e}")
        
        return []
    
    def _search_local_fallback(self, keyword: str, city: str = None) -> List[Dict[str, Any]]:
        from backend.app.services.attractions import AttractionsService
        
        local_service = AttractionsService()
        
        all_attractions = []
        if city and city in local_service.attractions_db:
            attractions = local_service.get_attractions(city, False)
            all_attractions.extend([{**a, 'city': city} for a in attractions])
        else:
            for city_name in local_service.attractions_db.keys():
                attractions = local_service.get_attractions(city_name, False)
                all_attractions.extend([{**a, 'city': city_name} for a in attractions])
        
        keyword_lower = keyword.lower()
        return [
            a for a in all_attractions
            if keyword_lower in a.get('name', '').lower() or
               keyword_lower in a.get('description', '').lower() or
               keyword_lower in a.get('type', '').lower()
        ]
    
    def _convert_type(self, type_str: str) -> str:
        type_map = {
            "风景名胜": "自然景观",
            "文物古迹": "人文古迹",
            "公园": "自然景观",
            "博物馆": "人文古迹",
            "旅游景点": "自然景观",
            "历史古迹": "人文古迹",
            "纪念馆": "人文古迹",
            "寺庙": "人文古迹"
        }
        
        for key, value in type_map.items():
            if key in type_str:
                return value
        
        return "其他"
    
    async def get_city_attractions(self, city: str, limit: int = 10) -> List[Dict[str, Any]]:
        local_results = await self.search_attractions("", city, limit)
        
        return local_results[:limit]
    
    async def close(self):
        await self.client.aclose()