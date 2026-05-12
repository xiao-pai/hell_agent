import json
import logging
import re
from typing import Optional
from openai import AsyncOpenAI
from backend.app.config import settings
from backend.app.models.schemas import TripPlan, TripPlanRequest, DayPlan, WeatherForecast, HotelSuggestion
from backend.app.services.transportation import TransportationService
from backend.app.services.weather import WeatherService
from backend.app.services.hotels import HotelsService
from backend.app.services.attractions import AttractionsService
from backend.app.services.trip_recommender import TripRecommender

logger = logging.getLogger(__name__)

class TripPlannerAgent:
    def __init__(self):
        self.model = settings.LLM_MODEL_ID
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=120
        )
        self.transportation_service = TransportationService()
        self.weather_service = WeatherService()
        self.hotels_service = HotelsService()
        self.attractions_service = AttractionsService()
        self.trip_recommender = TripRecommender(self.attractions_service)

    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY is not configured")
        if not settings.LLM_BASE_URL:
            raise ValueError("LLM_BASE_URL is not configured")

        logger.info("Calling LLM model=%s", self.model)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            choice = response.choices[0]
            content = getattr(choice.message, "content", None)
            if not content:
                content = getattr(choice, "text", None)
            content = content or ""
            logger.info("LLM response length=%s", len(content))
            return content
        except Exception as e:
            logger.error("LLM API call failed: %s", str(e))
            raise

    async def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        logger.info("Start planning trip for city=%s days=%s tourist=%s", request.city, request.days, request.prefer_tourist)

        if not request.city or not request.departure:
            raise ValueError("出发地和目的地城市不能为空")

        transportation_options = await self._get_transportation_options(request)

        plan_data = self.trip_recommender.recommend_trip(
            city=request.city,
            days=request.days,
            preferences=request.preferences,
            avoid_crowds=request.avoid_crowds,
            travel_style=request.travel_style
        )

        tourist_routes = transportation_options.get('tourist_routes') if transportation_options else None
        
        weather = await self.weather_service.get_weather_forecast(request.city)
        hotels = self.hotels_service.search_hotels(request.city, request.budget)
        
        weather_forecast = None
        if weather:
            weather_forecast = WeatherForecast(
                city=weather.get("city", ""),
                forecast=weather.get("forecast", []),
                tips=weather.get("tips", "")
            )
        
        hotel_suggestions = None
        if hotels:
            hotel_suggestions = [HotelSuggestion(**hotel) for hotel in hotels[:3]]

        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=[DayPlan(**day) for day in plan_data.get("days", [])],
            overall_suggestions=plan_data.get("overall_suggestions", ""),
            budget=plan_data.get("budget"),
            transportation=transportation_options,
            tourist_routes=tourist_routes,
            weather=weather_forecast,
            hotels=hotel_suggestions
        )

    async def _get_transportation_options(self, request: TripPlanRequest) -> Optional[dict]:
        try:
            logger.debug(f"Getting transportation options: departure={request.departure}, city={request.city}, transportation={request.transportation}, date={request.start_date}, tourist={request.prefer_tourist}")
            result = await self.transportation_service.get_transportation_options(
                request.departure,
                request.city,
                request.transportation,
                request.start_date,
                request.prefer_tourist
            )
            logger.debug(f"Transportation options result: long_distance_count={len(result.get('long_distance', []))}, local_count={len(result.get('local', []))}, tourist_routes_count={len(result.get('tourist_routes', []))}")
            return result
        except Exception as e:
            logger.warning("Failed to get transportation options: %s", e)
            return None

    def _extract_json(self, text: str) -> dict:
        if not text:
            logger.warning("LLM response is empty")
            return {}
        
        try:
            text = text.strip()
            
            if text.startswith('```'):
                lines = text.split('\n')
                content = []
                in_code = False
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code:
                        content.append(line)
                text = '\n'.join(content)
            
            text = text.strip()
            
            cleaned_text = self._clean_json_text(text)
            
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass
            
            match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    fixed = self._fix_json(match.group())
                    try:
                        return json.loads(fixed)
                    except json.JSONDecodeError as e:
                        logger.error("Failed to parse matched JSON after fix: %s", e)
            
            match = re.search(r"\[.*\]", cleaned_text, re.DOTALL)
            if match:
                try:
                    return {"days": json.loads(match.group())}
                except json.JSONDecodeError:
                    fixed = self._fix_json(match.group())
                    try:
                        return {"days": json.loads(fixed)}
                    except json.JSONDecodeError as e:
                        logger.error("Failed to parse matched list after fix: %s", e)
                    
        except Exception as e:
            logger.error("Unexpected error in _extract_json: %s", e)
        
        logger.error("LLM response content (first 500 chars): %s", text[:500] if len(text) > 500 else text)
        return self._get_default_plan()
    
    def _clean_json_text(self, text: str) -> str:
        text = text.replace('\\n', '\n')
        text = text.replace('\\"', '"')
        text = text.replace("\\'", "'")
        text = text.replace("“", "\"")
        text = text.replace("”", "\"")
        text = text.replace("‘", "'")
        text = text.replace("’", "'")
        return text
    
    def _fix_json(self, json_str: str) -> str:
        lines = json_str.split('\n')
        fixed_lines = []
        for line in lines:
            line = line.rstrip()
            if line.endswith(',') and (line.strip().endswith(']') or line.strip().endswith('}')):
                line = line[:-1]
            fixed_lines.append(line)
        return '\n'.join(fixed_lines)
    
    def _get_default_plan(self) -> dict:
        return {
            "days": [
                {
                    "date": "2026-05-15",
                    "day_index": 1,
                    "description": "第一天行程",
                    "attractions": [
                        {
                            "name": "当地著名景点",
                            "address": "城市中心",
                            "location": {"longitude": 0, "latitude": 0},
                            "visit_duration": 120,
                            "description": "欢迎来到目的地，开始您的旅程！",
                            "ticket_price": 0
                        }
                    ],
                    "hotel": "推荐入住市中心酒店"
                }
            ],
            "overall_suggestions": "祝您旅途愉快！",
            "budget": {"total": 0}
        }
