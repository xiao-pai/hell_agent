import logging
import httpx
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

class WeatherAPIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.amap_api_key = settings.AMAP_API_KEY
    
    async def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        if not self.amap_api_key:
            logger.warning("AMAP_API_KEY not configured")
            return await self._get_mock_weather(city)
        
        try:
            url = "https://restapi.amap.com/v3/weather/weatherInfo"
            params = {
                "city": city,
                "key": self.amap_api_key,
                "extensions": "all"
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get('status') == '1':
                forecasts = data.get('forecasts', [])
                if forecasts:
                    return self._parse_amap_response(forecasts[0])
        except Exception as e:
            logger.error(f"Amap weather API failed: {e}")
        
        return await self._get_mock_weather(city)
    
    def _parse_amap_response(self, forecast: Dict) -> Dict[str, Any]:
        return {
            "city": forecast.get('city', ''),
            "today": {
                "date": forecast.get('reporttime', ''),
                "weather": forecast.get('casts', [{}])[0].get('dayweather', ''),
                "high_temp": forecast.get('casts', [{}])[0].get('daytemp', ''),
                "low_temp": forecast.get('casts', [{}])[0].get('nighttemp', ''),
                "wind": forecast.get('casts', [{}])[0].get('daywind', ''),
                "wind_level": forecast.get('casts', [{}])[0].get('daypower', '')
            },
            "forecast": [
                {
                    "date": cast.get('date', ''),
                    "weather": cast.get('dayweather', ''),
                    "high_temp": cast.get('daytemp', ''),
                    "low_temp": cast.get('nighttemp', '')
                } for cast in forecast.get('casts', [])
            ]
        }
    
    async def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        mock_data = {
            "北京": {"weather": "晴", "high": 28, "low": 18, "desc": "晴朗舒适"},
            "上海": {"weather": "多云", "high": 30, "low": 22, "desc": "多云转晴"},
            "杭州": {"weather": "晴", "high": 27, "low": 17, "desc": "阳光明媚"},
            "广州": {"weather": "雷阵雨", "high": 32, "low": 25, "desc": "午后有雨"},
            "成都": {"weather": "阴", "high": 24, "low": 16, "desc": "阴天舒适"},
            "西安": {"weather": "晴", "high": 26, "low": 15, "desc": "晴朗干燥"},
            "大理": {"weather": "晴", "high": 25, "low": 14, "desc": "高原阳光"},
            "丽江": {"weather": "多云", "high": 23, "low": 12, "desc": "气候宜人"},
            "三亚": {"weather": "晴", "high": 32, "low": 26, "desc": "热带风情"},
            "厦门": {"weather": "多云", "high": 29, "low": 23, "desc": "海风习习"},
            "九江": {"weather": "晴", "high": 26, "low": 16, "desc": "天气晴朗"}
        }
        
        data = mock_data.get(city, {"weather": "晴", "high": 25, "low": 15, "desc": "天气良好"})
        
        return {
            "city": city,
            "today": {
                "date": "2026-05-12",
                "weather": data["weather"],
                "high_temp": str(data["high"]),
                "low_temp": str(data["low"]),
                "description": data["desc"]
            },
            "forecast": [
                {"date": "2026-05-13", "weather": data["weather"], "high_temp": str(data["high"]), "low_temp": str(data["low"])},
                {"date": "2026-05-14", "weather": data["weather"], "high_temp": str(data["high"]-1), "low_temp": str(data["low"])},
                {"date": "2026-05-15", "weather": "多云", "high_temp": str(data["high"]), "low_temp": str(data["low"]+1)}
            ]
        }
    
    async def close(self):
        await self.client.aclose()