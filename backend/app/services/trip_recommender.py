import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TripRecommender:
    def __init__(self, attractions_service):
        self.attractions_service = attractions_service
    
    def recommend_trip(self, city: str, days: int, preferences: str = "", 
                       avoid_crowds: bool = False, travel_style: str = "balanced") -> dict:
        logger.info(f"Generating trip recommendation for {city}, {days} days, preferences={preferences}, avoid_crowds={avoid_crowds}, travel_style={travel_style}")
        
        attractions = self.attractions_service.get_attractions(city, avoid_crowds)
        
        if not attractions:
            logger.warning(f"No attractions found for {city}")
            return self._generate_empty_plan(city, days)
        
        filtered_attractions = self._filter_attractions(attractions, preferences)
        sorted_attractions = self._sort_attractions(filtered_attractions, avoid_crowds)
        
        daily_attractions = self._schedule_attractions(sorted_attractions, days, travel_style)
        
        return self._generate_plan(city, days, daily_attractions)
    
    def _filter_attractions(self, attractions: List[Dict], preferences: str) -> List[Dict]:
        if not preferences or preferences.lower() == "全部":
            return attractions
        
        keywords = preferences.lower().split(" ")
        filtered = []
        
        for attr in attractions:
            matches = False
            for keyword in keywords:
                if keyword in attr.get('name', '').lower() or \
                   keyword in attr.get('description', '').lower() or \
                   keyword in attr.get('type', '').lower():
                    matches = True
                    break
            if matches:
                filtered.append(attr)
        
        return filtered if filtered else attractions
    
    def _sort_attractions(self, attractions: List[Dict], avoid_crowds: bool) -> List[Dict]:
        if avoid_crowds:
            return sorted(attractions, key=lambda x: x.get('popularity', 0))
        return sorted(attractions, key=lambda x: x.get('popularity', 0), reverse=True)
    
    def _schedule_attractions(self, attractions: List[Dict], days: int, travel_style: str) -> List[List[Dict]]:
        daily_counts = {
            "relaxed": 2,
            "balanced": 3,
            "active": 4
        }
        
        count_per_day = daily_counts.get(travel_style, 3)
        
        grouped = self._group_by_location(attractions)
        
        daily_attractions = []
        current_day = []
        current_area = None
        
        for area, area_attrs in grouped:
            for attr in area_attrs:
                is_far = attr.get('type') in ['自然景观', '登山', '长城', '远郊']
                
                if is_far and current_day:
                    daily_attractions.append(current_day)
                    current_day = [attr]
                    current_area = area
                elif current_day and current_area != area and len(current_day) >= count_per_day - 1:
                    daily_attractions.append(current_day)
                    current_day = [attr]
                    current_area = area
                else:
                    current_day.append(attr)
                    current_area = area
                
                if len(current_day) >= count_per_day:
                    daily_attractions.append(current_day)
                    current_day = []
                    current_area = None
        
        if current_day:
            daily_attractions.append(current_day)
        
        daily_attractions = daily_attractions[:days]
        
        if not daily_attractions and attractions:
            daily_attractions = [[a] for a in attractions[:days]]
        
        return daily_attractions
    
    def _group_by_location(self, attractions: List[Dict]) -> list:
        location_groups = {
            "北京": {
                "城区核心": ["故宫", "天安门", "人民广场", "南锣鼓巷", "什刹海", "王府井", "前门"],
                "西北郊": ["颐和园", "圆明园", "北京大学", "清华大学", "香山"],
                "远郊": ["八达岭长城", "慕田峪长城", "明十三陵"],
                "奥林匹克": ["奥林匹克公园", "鸟巢", "水立方"]
            },
            "杭州": {
                "西湖周边": ["西湖", "断桥残雪", "雷峰塔", "苏堤", "白堤", "岳王庙"],
                "西部景区": ["灵隐寺", "飞来峰", "龙井村", "九溪烟树"],
                "郊区": ["西溪湿地", "千岛湖"]
            },
            "上海": {
                "浦西": ["外滩", "豫园", "南京路", "人民广场", "田子坊"],
                "浦东": ["陆家嘴", "东方明珠", "上海中心", "环球金融中心"],
                "郊区": ["迪士尼", "朱家角"]
            },
            "西安": {
                "市区": ["兵马俑", "大雁塔", "小雁塔", "陕西历史博物馆", "钟楼", "鼓楼"],
                "城墙内": ["回民街", "碑林"],
                "郊区": ["华山"]
            },
            "大理": {
                "古城": ["大理古城", "人民路"],
                "洱海周边": ["洱海", "双廊古镇", "喜洲古镇", "海舌生态公园"],
                "苍山": ["苍山", "崇圣寺三塔"]
            }
        }
        
        groups = []
        city = attractions[0].get('city', '') if attractions else ''
        city_groups = location_groups.get(city, {})
        
        if city_groups:
            remaining = []
            for area, keywords in city_groups.items():
                area_attrs = []
                for attr in attractions:
                    name = attr.get('name', '')
                    if any(keyword in name for keyword in keywords):
                        area_attrs.append(attr)
                if area_attrs:
                    groups.append((area, area_attrs))
            
            all_grouped = set()
            for _, attrs in groups:
                for attr in attrs:
                    all_grouped.add(attr.get('name', ''))
            
            for attr in attractions:
                if attr.get('name', '') not in all_grouped:
                    remaining.append(attr)
            
            if remaining:
                groups.append(("其他", remaining))
        else:
            groups.append(("全部", attractions))
        
        return groups
    
    def _generate_plan(self, city: str, days: int, daily_attractions: List[List[Dict]]) -> dict:
        start_date = datetime.now() + timedelta(days=1)
        
        plan_days = []
        total_cost = 0
        
        for day_idx, attractions in enumerate(daily_attractions):
            date_str = (start_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")
            
            day_attractions = []
            prev_name = ""
            
            for idx, attr in enumerate(attractions):
                transport = ""
                if idx > 0:
                    transport = self._estimate_transport(prev_name, attr.get('name', ''))
                
                day_attractions.append({
                    "name": attr.get('name', ''),
                    "address": attr.get('address', ''),
                    "location": {
                        "longitude": attr.get('longitude', 0),
                        "latitude": attr.get('latitude', 0)
                    },
                    "visit_duration": attr.get('visit_duration', 120),
                    "description": attr.get('description', ''),
                    "ticket_price": attr.get('ticket_price', 0),
                    "transport_from_previous": transport
                })
                total_cost += attr.get('ticket_price', 0)
                prev_name = attr.get('name', '')
            
            plan_days.append({
                "date": date_str,
                "day_index": day_idx + 1,
                "description": self._generate_day_description(day_idx + 1, attractions),
                "attractions": day_attractions,
                "hotel": self._suggest_hotel(city),
                "daily_transport_tips": self._generate_transport_tips(city)
            })
        
        total_cost += days * 200
        total_cost += days * 80
        
        return {
            "days": plan_days,
            "overall_suggestions": self._generate_overall_suggestions(city, days),
            "budget": {"total": total_cost}
        }
    
    def _estimate_transport(self, from_name: str, to_name: str) -> str:
        if not from_name:
            return ""
        
        common_pairs = {
            ("西湖", "灵隐寺"): "打车20分钟",
            ("灵隐寺", "西溪湿地"): "地铁1小时",
            ("大理古城", "洱海"): "打车30分钟",
            ("天安门", "故宫"): "步行10分钟",
            ("外滩", "陆家嘴"): "地铁20分钟",
            ("兵马俑", "大雁塔"): "地铁1小时",
        }
        
        return common_pairs.get((from_name, to_name), "地铁或打车约30分钟")
    
    def _generate_day_description(self, day_num: int, attractions: List[Dict]) -> str:
        names = [a.get('name', '') for a in attractions]
        return f"第{day_num}天：{'、'.join(names)}"
    
    def _suggest_hotel(self, city: str) -> str:
        hotels = {
            "九江": "推荐入住浔阳区或庐山脚下，方便游览",
            "杭州": "推荐入住西湖附近酒店，方便出行",
            "大理": "推荐入住大理古城内客栈",
            "上海": "推荐入住外滩或陆家嘴附近",
            "北京": "推荐入住天安门或王府井附近",
            "西安": "推荐入住钟楼附近",
            "成都": "推荐入住春熙路附近",
            "重庆": "推荐入住解放碑附近",
            "广州": "推荐入住天河区",
            "深圳": "推荐入住福田或南山",
            "苏州": "推荐入住观前街附近",
            "南京": "推荐入住夫子庙附近",
            "武汉": "推荐入住武昌区",
            "青岛": "推荐入住八大关附近",
            "厦门": "推荐入住思明区",
            "三亚": "推荐入住亚龙湾或海棠湾",
            "桂林": "推荐入住阳朔",
            "丽江": "推荐入住丽江古城内",
            "张家界": "推荐入住武陵源景区附近",
            "九寨沟": "推荐入住沟口附近",
            "香格里拉": "推荐入住独克宗古城",
            "拉萨": "推荐入住布达拉宫附近",
        }
        return hotels.get(city, f"推荐入住{city}市中心")
    
    def _generate_transport_tips(self, city: str) -> str:
        tips = {
            "九江": "九江景点较为分散，建议打车或自驾前往，庐山景区需乘坐景区交通车",
            "杭州": "杭州地铁覆盖主要景点，建议购买地铁卡",
            "大理": "古城内步行即可，去洱海建议打车或包车",
            "上海": "地铁非常方便，推荐使用Metro大都会APP",
            "北京": "地铁覆盖广，热门景点建议早起避开人流",
            "西安": "城墙内景点集中，步行可达",
            "成都": "市区景点地铁可达，去都江堰建议坐城际列车",
            "重庆": "注意区分渝中区和江北，长江索道值得体验",
            "广州": "地铁发达，广州塔建议提前预约",
            "深圳": "地铁方便，东部华侨城建议安排一整天",
            "苏州": "园林景点集中，可步行或骑行",
            "南京": "地铁覆盖主要景点，秦淮河夜景很美",
            "武汉": "长江大桥值得步行体验",
            "青岛": "沿海景点可步行或骑行",
            "厦门": "鼓浪屿需坐船，提前购票",
            "三亚": "景点分散，建议租车或打车",
            "桂林": "漓江游船需提前预订",
            "丽江": "古城内步行，去玉龙雪山建议报团",
            "张家界": "景区交通车很重要，提前规划路线",
            "九寨沟": "景区内有观光车，按景点顺序游览",
            "香格里拉": "海拔高，注意休息",
            "拉萨": "布达拉宫需提前预约，注意高原反应",
        }
        return tips.get(city, f"{city}交通便利，建议使用公共交通")
    
    def _generate_overall_suggestions(self, city: str, days: int) -> str:
        suggestions = {
            "九江": f"九江{days}日游，庐山是核心景点，建议安排一整天游览。鄱阳湖观鸟最佳季节是冬季。",
            "杭州": f"杭州{days}日游，西湖是必去景点，灵隐寺香火旺盛值得一去。",
            "大理": f"大理{days}日游，洱海环湖骑行是特色体验，古城夜景很美。",
            "上海": f"上海{days}日游，外滩夜景和陆家嘴天际线不容错过。",
            "北京": f"北京{days}日游，故宫建议安排一整天，长城建议早出发。",
            "西安": f"西安{days}日游，兵马俑和陕西历史博物馆是文化精髓。",
            "成都": f"成都{days}日游，大熊猫基地一定要早去，宽窄巷子体验慢生活。",
            "重庆": f"重庆{days}日游，洪崖洞夜景必看，长江索道体验山城特色。",
            "广州": f"广州{days}日游，早茶是特色，广州塔俯瞰全城。",
            "深圳": f"深圳{days}日游，主题公园众多，东部华侨城值得一游。",
            "苏州": f"苏州{days}日游，园林艺术甲天下，周庄古镇体验水乡风情。",
            "南京": f"南京{days}日游，历史文化名城，中山陵和夫子庙必去。",
            "武汉": f"武汉{days}日游，黄鹤楼看长江，户部巷吃美食。",
            "青岛": f"青岛{days}日游，海滨城市风光好，崂山值得一爬。",
            "厦门": f"厦门{days}日游，鼓浪屿文艺之旅，环岛路骑行。",
            "三亚": f"三亚{days}日游，海岛度假胜地，蜈支洲岛海水清澈。",
            "桂林": f"桂林{days}日游，漓江山水甲天下，阳朔西街很热闹。",
            "丽江": f"丽江{days}日游，古城慢生活，玉龙雪山壮丽。",
            "张家界": f"张家界{days}日游，阿凡达取景地，玻璃桥很刺激。",
            "九寨沟": f"九寨沟{days}日游，人间仙境，彩池美不胜收。",
            "香格里拉": f"香格里拉{days}日游，高原风光，普达措国家公园值得一去。",
            "拉萨": f"拉萨{days}日游，布达拉宫神圣庄严，纳木错湖美景。",
        }
        return suggestions.get(city, f"祝您在{city}旅途愉快！")
    
    def _generate_empty_plan(self, city: str, days: int) -> dict:
        start_date = datetime.now() + timedelta(days=1)
        
        plan_days = []
        for day_idx in range(min(days, 3)):
            date_str = (start_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")
            plan_days.append({
                "date": date_str,
                "day_index": day_idx + 1,
                "description": f"第{day_idx + 1}天行程",
                "attractions": [{
                    "name": f"{city}著名景点",
                    "address": f"{city}市中心",
                    "location": {"longitude": 0, "latitude": 0},
                    "visit_duration": 120,
                    "description": f"欢迎来到{city}旅游！",
                    "ticket_price": 0,
                    "transport_from_previous": ""
                }],
                "hotel": f"推荐入住{city}市中心酒店",
                "daily_transport_tips": f"{city}交通便利"
            })
        
        return {
            "days": plan_days,
            "overall_suggestions": f"祝您在{city}旅途愉快！",
            "budget": {"total": days * 300}
        }