import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class HotelsService:
    def __init__(self):
        self.hotels_db = {
            "杭州": [
                {"name": "杭州西湖国宾馆", "address": "杭州市西湖区杨公堤18号", "price": 1280, "rating": 4.9, 
                 "type": "豪华型", "distance_to_center": "步行10分钟", "facilities": ["免费WiFi", "游泳池", "餐厅"]},
                {"name": "杭州香格里拉饭店", "address": "杭州市西湖区北山山路78号", "price": 980, "rating": 4.8, 
                 "type": "豪华型", "distance_to_center": "步行15分钟", "facilities": ["免费WiFi", "健身房", "SPA"]},
                {"name": "全季酒店(杭州西湖湖滨店)", "address": "杭州市上城区平海路124号", "price": 420, "rating": 4.6, 
                 "type": "舒适型", "distance_to_center": "步行5分钟", "facilities": ["免费WiFi", "停车场"]},
                {"name": "如家精选酒店(杭州西湖店)", "address": "杭州市西湖区文二路38号", "price": 260, "rating": 4.4, 
                 "type": "经济型", "distance_to_center": "地铁2站", "facilities": ["免费WiFi"]},
                {"name": "杭州青芝坞民宿", "address": "杭州市西湖区青芝坞路", "price": 380, "rating": 4.7, 
                 "type": "民宿", "distance_to_center": "打车10分钟", "facilities": ["免费WiFi", "庭院"]},
            ],
            "大理": [
                {"name": "大理古城美咖酒店", "address": "大理市大理古城复兴路", "price": 580, "rating": 4.8, 
                 "type": "舒适型", "distance_to_center": "步行5分钟", "facilities": ["免费WiFi", "露台"]},
                {"name": "大理洱海海景酒店", "address": "大理市双廊镇洱海畔", "price": 1580, "rating": 4.9, 
                 "type": "豪华型", "distance_to_center": "打车30分钟", "facilities": ["免费WiFi", "海景房", "餐厅"]},
                {"name": "大理古城客栈", "address": "大理市大理古城人民路", "price": 280, "rating": 4.5, 
                 "type": "经济型", "distance_to_center": "步行3分钟", "facilities": ["免费WiFi"]},
                {"name": "大理喜洲严家民居客栈", "address": "大理市喜洲镇", "price": 450, "rating": 4.6, 
                 "type": "民宿", "distance_to_center": "打车20分钟", "facilities": ["免费WiFi", "白族特色"]},
            ],
            "上海": [
                {"name": "上海外滩华尔道夫酒店", "address": "上海市黄浦区中山东一路2号", "price": 2580, "rating": 4.9, 
                 "type": "豪华型", "distance_to_center": "步行3分钟", "facilities": ["免费WiFi", "游泳池", "SPA"]},
                {"name": "上海浦东丽思卡尔顿酒店", "address": "上海市浦东新区世纪大道8号", "price": 2280, "rating": 4.8, 
                 "type": "豪华型", "distance_to_center": "地铁1站", "facilities": ["免费WiFi", "健身房", "餐厅"]},
                {"name": "上海全季酒店(陆家嘴店)", "address": "上海市浦东新区陆家嘴环路", "price": 580, "rating": 4.6, 
                 "type": "舒适型", "distance_to_center": "步行8分钟", "facilities": ["免费WiFi", "停车场"]},
                {"name": "上海如家快捷酒店(外滩店)", "address": "上海市黄浦区福州路", "price": 320, "rating": 4.3, 
                 "type": "经济型", "distance_to_center": "步行10分钟", "facilities": ["免费WiFi"]},
            ],
            "北京": [
                {"name": "北京故宫东华门大酒店", "address": "北京市东城区东华门大街", "price": 1680, "rating": 4.8, 
                 "type": "豪华型", "distance_to_center": "步行5分钟", "facilities": ["免费WiFi", "餐厅"]},
                {"name": "北京国贸大酒店", "address": "北京市朝阳区建国门外大街1号", "price": 1880, "rating": 4.9, 
                 "type": "豪华型", "distance_to_center": "地铁1站", "facilities": ["免费WiFi", "游泳池", "SPA"]},
                {"name": "北京汉庭酒店(王府井店)", "address": "北京市东城区王府井大街", "price": 480, "rating": 4.5, 
                 "type": "舒适型", "distance_to_center": "步行3分钟", "facilities": ["免费WiFi"]},
                {"name": "北京7天连锁酒店(天安门店)", "address": "北京市西城区前门西大街", "price": 280, "rating": 4.2, 
                 "type": "经济型", "distance_to_center": "步行8分钟", "facilities": ["免费WiFi"]},
            ],
            "西安": [
                {"name": "西安凯悦酒店", "address": "西安市新城区东大街233号", "price": 1280, "rating": 4.8, 
                 "type": "豪华型", "distance_to_center": "步行5分钟", "facilities": ["免费WiFi", "游泳池", "餐厅"]},
                {"name": "西安大雁塔假日酒店", "address": "西安市雁塔区大雁塔北广场", "price": 880, "rating": 4.6, 
                 "type": "舒适型", "distance_to_center": "步行3分钟", "facilities": ["免费WiFi", "健身房"]},
                {"name": "西安全季酒店(钟楼店)", "address": "西安市碑林区钟楼旁", "price": 450, "rating": 4.5, 
                 "type": "舒适型", "distance_to_center": "步行2分钟", "facilities": ["免费WiFi"]},
                {"name": "西安如家酒店(回民街店)", "address": "西安市莲湖区回民街", "price": 260, "rating": 4.3, 
                 "type": "经济型", "distance_to_center": "步行3分钟", "facilities": ["免费WiFi"]},
            ],
        }
    
    def search_hotels(self, city: str, budget: str = "中等") -> List[Dict[str, Any]]:
        try:
            logger.info(f"Searching hotels for {city}, budget={budget}")
            
            hotels = self.hotels_db.get(city, [])
            
            price_ranges = {
                "经济型": (0, 350),
                "中等": (300, 800),
                "高档": (700, 1500),
                "豪华": (1500, 5000)
            }
            
            min_price, max_price = price_ranges.get(budget, (0, 5000))
            
            filtered_hotels = [
                h for h in hotels if min_price <= h.get("price", 0) <= max_price
            ]
            
            return sorted(filtered_hotels, key=lambda x: x.get("rating", 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to search hotels: {e}")
            return []
    
    def get_hotel_detail(self, city: str, name: str) -> Optional[Dict[str, Any]]:
        try:
            hotels = self.hotels_db.get(city, [])
            for hotel in hotels:
                if hotel.get("name") == name:
                    return hotel
            return None
        except Exception as e:
            logger.error(f"Failed to get hotel detail: {e}")
            return None