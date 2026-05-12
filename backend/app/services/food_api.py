import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FoodAPIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
    
    async def search_restaurants(self, city: str, keyword: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = await self._search_by_mock_api(city, keyword, limit)
            return results
        except Exception as e:
            logger.error(f"Restaurant search failed: {e}")
            return self._get_mock_restaurants(city, limit)
    
    async def get_local_specialties(self, city: str) -> List[Dict[str, Any]]:
        specialties = {
            "北京": [
                {"name": "北京烤鸭", "description": "皮脆肉嫩，肥而不腻", "price_range": "¥100-200", "recommend": "全聚德、大董"},
                {"name": "涮羊肉", "description": "铜锅涮肉，传统风味", "price_range": "¥80-150", "recommend": "东来顺、南门涮肉"},
                {"name": "炸酱面", "description": "老北京传统面食", "price_range": "¥20-40", "recommend": "海碗居"},
                {"name": "豆汁儿焦圈", "description": "北京特色早餐", "price_range": "¥10-20", "recommend": "尹三豆汁"},
            ],
            "上海": [
                {"name": "小笼包", "description": "皮薄馅大，汤汁鲜美", "price_range": "¥30-60", "recommend": "小笼包"},
                {"name": "生煎包", "description": "底脆面软，肉香多汁", "price_range": "¥15-30", "recommend": "大壶春"},
                {"name": "红烧肉", "description": "肥而不腻，入口即化", "price_range": "¥60-100", "recommend": "上海本帮菜"},
                {"name": "油爆虾", "description": "鲜嫩爽口，甜咸适中", "price_range": "¥80-120", "recommend": "老上海菜馆"},
            ],
            "杭州": [
                {"name": "西湖醋鱼", "description": "酸甜适口，鲜嫩爽滑", "price_range": "¥80-120", "recommend": "楼外楼"},
                {"name": "东坡肉", "description": "色泽红亮，酥烂入味", "price_range": "¥50-80", "recommend": "知味观"},
                {"name": "龙井虾仁", "description": "茶香浓郁，虾仁鲜嫩", "price_range": "¥120-180", "recommend": "绿茶餐厅"},
                {"name": "叫化鸡", "description": "泥烤而成，香气扑鼻", "price_range": "¥80-150", "recommend": "楼外楼"},
            ],
            "成都": [
                {"name": "火锅", "description": "麻辣鲜香，回味无穷", "price_range": "¥80-150", "recommend": "小龙坎、蜀大侠"},
                {"name": "担担面", "description": "麻辣鲜香，劲道爽滑", "price_range": "¥15-30", "recommend": "陈麻婆"},
                {"name": "麻婆豆腐", "description": "麻辣鲜香，嫩而不散", "price_range": "¥30-50", "recommend": "陈麻婆豆腐"},
                {"name": "夫妻肺片", "description": "麻辣鲜香，口感丰富", "price_range": "¥30-50", "recommend": "紫燕百味鸡"},
            ],
            "西安": [
                {"name": "肉夹馍", "description": "外酥里嫩，肉香四溢", "price_range": "¥10-20", "recommend": "潼关肉夹馍"},
                {"name": "羊肉泡馍", "description": "汤鲜味浓，馍筋肉烂", "price_range": "¥30-50", "recommend": "老孙家"},
                {"name": "凉皮", "description": "酸辣爽口，筋道爽滑", "price_range": "¥10-15", "recommend": "魏家凉皮"},
                {"name": "biangbiang面", "description": "面宽如裤，劲道爽滑", "price_range": "¥15-25", "recommend": "关中面馆"},
            ],
            "大理": [
                {"name": "酸辣鱼", "description": "酸辣鲜香，鱼肉鲜嫩", "price_range": "¥60-100", "recommend": "白族风味"},
                {"name": "烤乳扇", "description": "奶香浓郁，外酥里嫩", "price_range": "¥10-20", "recommend": "古城小吃"},
                {"name": "饵丝", "description": "软糯可口，汤汁鲜美", "price_range": "¥15-25", "recommend": "巍山扒肉饵丝"},
                {"name": "雕梅酒", "description": "酸甜可口，度数适中", "price_range": "¥30-50", "recommend": "本地特产"},
            ],
            "九江": [
                {"name": "庐山石鸡", "description": "肉质鲜嫩，营养丰富", "price_range": "¥80-120", "recommend": "庐山特色"},
                {"name": "庐山云雾茶", "description": "清香幽雅，滋味鲜爽", "price_range": "¥200-500/斤", "recommend": "庐山特产"},
                {"name": "九江茶饼", "description": "酥脆香甜，回味悠长", "price_range": "¥20-50/盒", "recommend": "梁义隆"},
                {"name": "萝卜饼", "description": "外酥里嫩，咸香可口", "price_range": "¥5-10", "recommend": "街边小吃"},
            ]
        }
        
        return specialties.get(city, [])
    
    async def _search_by_mock_api(self, city: str, keyword: str, limit: int) -> List[Dict[str, Any]]:
        mock_restaurants = {
            "北京": [
                {"name": "四季民福烤鸭店", "address": "东城区王府井", "rating": 4.8, "price": 150, "cuisine": "北京菜", "specialty": "烤鸭"},
                {"name": "大董烤鸭店", "address": "朝阳区团结湖", "rating": 4.9, "price": 200, "cuisine": "北京菜", "specialty": "烤鸭"},
                {"name": "海碗居", "address": "西城区西四", "rating": 4.5, "price": 60, "cuisine": "北京菜", "specialty": "炸酱面"},
                {"name": "南门涮肉", "address": "东城区东单", "rating": 4.7, "price": 120, "cuisine": "火锅", "specialty": "涮羊肉"},
            ],
            "上海": [
                {"name": "南翔馒头店", "address": "黄浦区豫园", "rating": 4.6, "price": 50, "cuisine": "上海菜", "specialty": "小笼包"},
                {"name": "老吉士酒家", "address": "徐汇区天平路", "rating": 4.8, "price": 150, "cuisine": "上海菜", "specialty": "本帮菜"},
                {"name": "大壶春", "address": "黄浦区四川中路", "rating": 4.5, "price": 30, "cuisine": "上海菜", "specialty": "生煎"},
            ],
            "杭州": [
                {"name": "楼外楼", "address": "西湖区孤山路", "rating": 4.7, "price": 180, "cuisine": "杭帮菜", "specialty": "西湖醋鱼"},
                {"name": "知味观", "address": "上城区仁和路", "rating": 4.6, "price": 80, "cuisine": "杭帮菜", "specialty": "东坡肉"},
                {"name": "绿茶餐厅", "address": "西湖区龙井路", "rating": 4.5, "price": 70, "cuisine": "杭帮菜", "specialty": "龙井虾仁"},
            ],
            "成都": [
                {"name": "小龙坎火锅", "address": "锦江区春熙路", "rating": 4.8, "price": 100, "cuisine": "火锅", "specialty": "麻辣火锅"},
                {"name": "陈麻婆豆腐", "address": "青羊区青华路", "rating": 4.7, "price": 60, "cuisine": "川菜", "specialty": "麻婆豆腐"},
                {"name": "兔头王", "address": "锦江区玉林路", "rating": 4.6, "price": 80, "cuisine": "川菜", "specialty": "兔头"},
            ],
            "九江": [
                {"name": "庐山特色菜馆", "address": "浔阳区庐山南路", "rating": 4.5, "price": 80, "cuisine": "江西菜", "specialty": "庐山石鸡"},
                {"name": "梁义隆", "address": "浔阳区大中路", "rating": 4.4, "price": 30, "cuisine": "小吃", "specialty": "茶饼"},
                {"name": "九江鱼庄", "address": "浔阳区滨江路", "rating": 4.6, "price": 100, "cuisine": "江西菜", "specialty": "鄱阳湖鱼"},
            ]
        }
        
        restaurants = mock_restaurants.get(city, [])
        if keyword:
            keyword = keyword.lower()
            restaurants = [r for r in restaurants if keyword in r['name'].lower() or keyword in r['cuisine'].lower()]
        
        return sorted(restaurants, key=lambda x: x['rating'], reverse=True)[:limit]
    
    def _get_mock_restaurants(self, city: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "name": f"{city}特色餐厅",
                "address": f"{city}市中心",
                "rating": 4.5,
                "price": 80,
                "cuisine": "本地菜",
                "specialty": "本地特色"
            }
        ] * min(limit, 3)
    
    async def close(self):
        await self.client.aclose()