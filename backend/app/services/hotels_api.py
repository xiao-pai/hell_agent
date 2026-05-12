import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class HotelsAPIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def search_hotels(self, city: str, check_in: str = None, check_out: str = None, 
                           budget_min: int = 0, budget_max: int = 10000, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = await self._search_by_mock_api(city, budget_min, budget_max, limit)
            return results
        except Exception as e:
            logger.error(f"Hotel search failed: {e}")
            return self._get_mock_hotels(city, limit)
    
    async def _search_by_mock_api(self, city: str, budget_min: int, budget_max: int, limit: int) -> List[Dict[str, Any]]:
        mock_hotels = {
            "北京": [
                {"name": "北京国贸大酒店", "address": "朝阳区建国门外大街1号", "price": 1280, "rating": 4.8, "type": "豪华型", "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"},
                {"name": "北京王府井希尔顿酒店", "address": "东城区王府井东大街8号", "price": 1100, "rating": 4.7, "type": "豪华型", "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d"},
                {"name": "桔子水晶酒店", "address": "西城区西单北大街109号", "price": 450, "rating": 4.5, "type": "舒适型", "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb"},
                {"name": "如家精选酒店", "address": "朝阳区望京街9号", "price": 320, "rating": 4.2, "type": "经济型", "image": "https://images.unsplash.com/photo-1448747163421-ff2a50c605a7"},
                {"name": "北京四季酒店", "address": "朝阳区亮马桥路48号", "price": 2580, "rating": 4.9, "type": "豪华型", "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"},
            ],
            "上海": [
                {"name": "上海外滩华尔道夫酒店", "address": "黄浦区中山东一路2号", "price": 1880, "rating": 4.8, "type": "豪华型", "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"},
                {"name": "上海浦东丽思卡尔顿酒店", "address": "浦东新区世纪大道8号", "price": 2200, "rating": 4.9, "type": "豪华型", "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d"},
                {"name": "全季酒店", "address": "静安区南京西路1266号", "price": 580, "rating": 4.5, "type": "舒适型", "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb"},
                {"name": "7天连锁酒店", "address": "徐汇区漕溪北路88号", "price": 260, "rating": 3.8, "type": "经济型", "image": "https://images.unsplash.com/photo-1448747163421-ff2a50c605a7"},
            ],
            "杭州": [
                {"name": "杭州西湖国宾馆", "address": "西湖区杨公堤18号", "price": 1580, "rating": 4.8, "type": "豪华型", "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"},
                {"name": "杭州洲际酒店", "address": "江干区解放东路2号", "price": 980, "rating": 4.7, "type": "豪华型", "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d"},
                {"name": "汉庭优佳酒店", "address": "西湖区文三路478号", "price": 380, "rating": 4.3, "type": "舒适型", "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb"},
                {"name": "布丁酒店", "address": "拱墅区湖墅南路186号", "price": 220, "rating": 3.9, "type": "经济型", "image": "https://images.unsplash.com/photo-1448747163421-ff2a50c605a7"},
            ],
            "大理": [
                {"name": "大理古城英迪格酒店", "address": "大理古城人民路58号", "price": 880, "rating": 4.7, "type": "豪华型", "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"},
                {"name": "大理悦榕庄", "address": "大理市双廊镇大建旁村", "price": 2280, "rating": 4.9, "type": "豪华型", "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d"},
                {"name": "大理古城花筑酒店", "address": "大理古城南门双鹤路", "price": 420, "rating": 4.4, "type": "舒适型", "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb"},
                {"name": "大理古城青旅", "address": "大理古城洋人街", "price": 80, "rating": 4.0, "type": "经济型", "image": "https://images.unsplash.com/photo-1448747163421-ff2a50c605a7"},
            ],
            "九江": [
                {"name": "九江富力万达嘉华酒店", "address": "濂溪区长虹西大道101号", "price": 680, "rating": 4.6, "type": "豪华型", "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"},
                {"name": "九江庐山国际大酒店", "address": "浔阳区南湖路116号", "price": 520, "rating": 4.5, "type": "舒适型", "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d"},
                {"name": "如家商旅酒店", "address": "浔阳区九江火车站旁", "price": 280, "rating": 4.2, "type": "经济型", "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb"},
                {"name": "九江庐山牯岭大酒店", "address": "庐山市牯岭镇", "price": 480, "rating": 4.4, "type": "舒适型", "image": "https://images.unsplash.com/photo-1448747163421-ff2a50c605a7"},
            ]
        }
        
        hotels = mock_hotels.get(city, [])
        filtered = [h for h in hotels if budget_min <= h['price'] <= budget_max]
        
        return sorted(filtered, key=lambda x: x['rating'], reverse=True)[:limit]
    
    def _get_mock_hotels(self, city: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "name": f"{city}精品酒店",
                "address": f"{city}市中心",
                "price": 450,
                "rating": 4.5,
                "type": "舒适型",
                "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945"
            }
        ] * min(limit, 3)
    
    async def close(self):
        await self.client.aclose()