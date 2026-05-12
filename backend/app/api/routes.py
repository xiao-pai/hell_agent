import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query
from backend.app.models.schemas import TripPlanRequest, TripPlan
from backend.app.agents.trip_planner import TripPlannerAgent
from backend.app.services.transportation import TransportationService
from backend.app.services.attractions import AttractionsService
from backend.app.services.online_attractions import OnlineAttractionsService
from backend.app.services.weather import WeatherService

logger = logging.getLogger(__name__)
router = APIRouter()
planner = TripPlannerAgent()
transportation_service = TransportationService()
attractions_service = AttractionsService()
online_attractions_service = OnlineAttractionsService()
weather_service = WeatherService()

@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest):
    logger.info("Received trip plan request: city=%s, days=%s, tourist=%s", request.city, request.days, request.prefer_tourist)
    try:
        plan = await planner.plan_trip(request)
        logger.info("Trip plan created successfully for city=%s", request.city)
        return plan
    except Exception as e:
        logger.exception("Failed to create trip plan")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tourist-trains")
async def get_tourist_trains(
    from_station: str = Query(..., description="出发站"),
    to_station: str = Query(None, description="到达站（可选）"),
    season: str = Query(None, description="季节筛选：全年/春季/夏季/秋季/冬季")
):
    logger.info("Getting tourist trains: from=%s, to=%s, season=%s", from_station, to_station, season)
    try:
        trains = await transportation_service.get_tourist_trains(from_station, to_station, season)
        return {"success": True, "count": len(trains), "trains": trains}
    except Exception as e:
        logger.exception("Failed to get tourist trains")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tourist-routes")
async def get_tourist_routes(
    from_city: str = Query(None, description="出发城市（可选）"),
    difficulty: str = Query(None, description="难度等级：轻松/中等/困难"),
    limit: int = Query(8, ge=1, le=20, description="返回数量")
):
    logger.info("Getting tourist routes: from=%s, difficulty=%s, limit=%s", from_city, difficulty, limit)
    try:
        routes = await transportation_service.get_tourist_routes(from_city)
        if difficulty:
            routes = [r for r in routes if r.get('difficulty') == difficulty]
        return {"success": True, "count": len(routes[:limit]), "routes": routes[:limit]}
    except Exception as e:
        logger.exception("Failed to get tourist routes")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-attractions")
async def search_attractions(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query(None, description="城市筛选（可选）"),
    avoid_crowds: bool = Query(False, description="是否避开热门"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    logger.info("Searching attractions: keyword=%s, city=%s, avoid_crowds=%s", keyword, city, avoid_crowds)
    try:
        all_attractions = []
        if city:
            attractions = attractions_service.get_attractions(city, avoid_crowds)
            all_attractions.extend(attractions)
        else:
            for city_name in attractions_service.attractions_db.keys():
                attractions = attractions_service.get_attractions(city_name, avoid_crowds)
                all_attractions.extend([{**a, 'city': city_name} for a in attractions])
        
        keyword_lower = keyword.lower()
        filtered = [
            a for a in all_attractions 
            if keyword_lower in a.get('name', '').lower() or 
               keyword_lower in a.get('description', '').lower() or
               keyword_lower in a.get('type', '').lower()
        ]
        
        filtered = sorted(filtered, key=lambda x: x.get('popularity', 0), reverse=True)
        
        return {"success": True, "count": len(filtered[:limit]), "attractions": filtered[:limit]}
    except Exception as e:
        logger.exception("Failed to search attractions")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cities")
async def get_cities():
    logger.info("Getting all supported cities")
    try:
        cities = list(attractions_service.attractions_db.keys())
        return {"success": True, "count": len(cities), "cities": cities}
    except Exception as e:
        logger.exception("Failed to get cities")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather")
async def get_weather(city: str = Query(..., description="城市名称")):
    logger.info("Getting weather for city=%s", city)
    try:
        weather = await weather_service.get_weather_forecast(city)
        if weather:
            return {"success": True, **weather}
        else:
            return {"success": False, "error": "获取天气失败"}
    except Exception as e:
        logger.exception("Failed to get weather")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-attractions-online")
async def search_attractions_online(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query(None, description="城市筛选（可选）"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    logger.info("Online search attractions: keyword=%s, city=%s", keyword, city)
    try:
        attractions = await online_attractions_service.search_attractions(keyword, city, limit)
        return {"success": True, "count": len(attractions), "attractions": attractions}
    except Exception as e:
        logger.exception("Failed to search attractions online")
        raise HTTPException(status_code=500, detail=str(e))
