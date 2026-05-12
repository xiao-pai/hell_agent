import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TicketsAPIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def get_ticket_info(self, attraction_name: str, city: str = None) -> Optional[Dict[str, Any]]:
        try:
            return await self._search_ticket(attraction_name, city)
        except Exception as e:
            logger.error(f"Ticket search failed: {e}")
            return self._get_mock_ticket(attraction_name)
    
    async def search_tickets(self, keyword: str, city: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            return await self._search_by_keyword(keyword, city, limit)
        except Exception as e:
            logger.error(f"Ticket search failed: {e}")
            return self._get_mock_tickets(keyword, limit)
    
    async def _search_ticket(self, attraction_name: str, city: str) -> Dict[str, Any]:
        mock_tickets = {
            "故宫": {"name": "故宫博物院", "price": 60, "original_price": 60, "discount": 100, 
                    "open_time": "08:30-17:00", "book_url": "#", "city": "北京"},
            "颐和园": {"name": "颐和园", "price": 30, "original_price": 30, "discount": 100, 
                      "open_time": "06:30-18:00", "book_url": "#", "city": "北京"},
            "八达岭长城": {"name": "八达岭长城", "price": 40, "original_price": 40, "discount": 100, 
                          "open_time": "06:30-18:00", "book_url": "#", "city": "北京"},
            "西湖": {"name": "西湖景区", "price": 0, "original_price": 0, "discount": 100, 
                    "open_time": "全天", "book_url": "#", "city": "杭州"},
            "灵隐寺": {"name": "灵隐寺", "price": 75, "original_price": 75, "discount": 100, 
                      "open_time": "07:00-17:30", "book_url": "#", "city": "杭州"},
            "洱海": {"name": "洱海", "price": 0, "original_price": 0, "discount": 100, 
                    "open_time": "全天", "book_url": "#", "city": "大理"},
            "大理古城": {"name": "大理古城", "price": 35, "original_price": 35, "discount": 100, 
                        "open_time": "全天", "book_url": "#", "city": "大理"},
            "庐山": {"name": "庐山风景区", "price": 160, "original_price": 180, "discount": 89, 
                    "open_time": "06:00-20:00", "book_url": "#", "city": "九江"},
            "鄱阳湖": {"name": "鄱阳湖国家湿地公园", "price": 120, "original_price": 120, "discount": 100, 
                      "open_time": "08:00-18:00", "book_url": "#", "city": "九江"},
            "兵马俑": {"name": "秦始皇兵马俑博物馆", "price": 120, "original_price": 120, "discount": 100, 
                      "open_time": "08:30-18:00", "book_url": "#", "city": "西安"},
            "大雁塔": {"name": "大雁塔", "price": 30, "original_price": 30, "discount": 100, 
                      "open_time": "08:30-18:00", "book_url": "#", "city": "西安"},
        }
        
        for key, value in mock_tickets.items():
            if key in attraction_name or attraction_name in key:
                if city and value['city'] != city:
                    continue
                return value
        
        return self._get_mock_ticket(attraction_name)
    
    async def _search_by_keyword(self, keyword: str, city: str, limit: int) -> List[Dict[str, Any]]:
        mock_tickets = [
            {"name": "故宫博物院", "price": 60, "city": "北京", "rating": 4.9, "type": "人文古迹"},
            {"name": "颐和园", "price": 30, "city": "北京", "rating": 4.8, "type": "自然景观"},
            {"name": "八达岭长城", "price": 40, "city": "北京", "rating": 4.9, "type": "人文古迹"},
            {"name": "西湖景区", "price": 0, "city": "杭州", "rating": 4.9, "type": "自然景观"},
            {"name": "灵隐寺", "price": 75, "city": "杭州", "rating": 4.7, "type": "人文古迹"},
            {"name": "洱海", "price": 0, "city": "大理", "rating": 4.8, "type": "自然景观"},
            {"name": "大理古城", "price": 35, "city": "大理", "rating": 4.7, "type": "人文古迹"},
            {"name": "庐山风景区", "price": 160, "city": "九江", "rating": 4.8, "type": "自然景观"},
            {"name": "鄱阳湖", "price": 120, "city": "九江", "rating": 4.6, "type": "自然景观"},
            {"name": "兵马俑", "price": 120, "city": "西安", "rating": 4.9, "type": "人文古迹"},
            {"name": "大雁塔", "price": 30, "city": "西安", "rating": 4.7, "type": "人文古迹"},
            {"name": "外滩", "price": 0, "city": "上海", "rating": 4.8, "type": "现代景观"},
            {"name": "豫园", "price": 40, "city": "上海", "rating": 4.6, "type": "人文古迹"},
        ]
        
        results = []
        for ticket in mock_tickets:
            if keyword.lower() in ticket['name'].lower():
                if city and ticket['city'] != city:
                    continue
                results.append(ticket)
        
        return sorted(results, key=lambda x: x['rating'], reverse=True)[:limit]
    
    def _get_mock_ticket(self, attraction_name: str) -> Dict[str, Any]:
        return {
            "name": attraction_name,
            "price": 50,
            "original_price": 60,
            "discount": 83,
            "open_time": "09:00-17:00",
            "book_url": "#"
        }
    
    def _get_mock_tickets(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "name": f"{keyword}景区",
                "price": 50,
                "city": "未知",
                "rating": 4.5,
                "type": "景点"
            }
        ] * min(limit, 3)
    
    async def close(self):
        await self.client.aclose()