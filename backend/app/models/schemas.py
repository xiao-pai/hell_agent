from pydantic import BaseModel, Field
from typing import List, Optional

class Location(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

class Attraction(BaseModel):
    name: str
    address: str
    location: Location
    visit_duration: int = 60
    description: str
    ticket_price: int = 0
    image_url: Optional[str] = None
    transport_from_previous: Optional[str] = None  # 从上个景点如何到达

class DayPlan(BaseModel):
    date: str
    day_index: int
    description: str = ""
    attractions: List[Attraction] = []
    hotel: Optional[str] = None
    daily_transport_tips: Optional[str] = None  # 当日交通提示

class TouristRoute(BaseModel):
    id: str
    name: str
    from_city: str
    to_city: str
    description: str
    scenic_spots: List[str]
    best_season: str
    recommended_days: int
    difficulty: str

class WeatherForecast(BaseModel):
    city: str
    forecast: List[dict] = []
    tips: str = ""

class HotelSuggestion(BaseModel):
    name: str
    address: str
    price: int
    rating: float
    type: str
    distance_to_center: str
    facilities: List[str] = []

class TripPlan(BaseModel):
    city: str
    start_date: str
    end_date: str
    days: List[DayPlan]
    overall_suggestions: str = ""
    budget: Optional[dict] = None
    transportation: Optional[dict] = None
    tourist_routes: Optional[List[TouristRoute]] = None
    weather: Optional[WeatherForecast] = None
    hotels: Optional[List[HotelSuggestion]] = None

class TripPlanRequest(BaseModel):
    city: str
    start_date: str
    end_date: str
    days: int
    preferences: str
    budget: str
    transportation: str
    accommodation: str
    departure: str  # 添加出发地字段
    prefer_tourist: bool = False  # 是否偏好旅游专线
    avoid_crowds: bool = False  # 是否避开热门景点
    travel_style: str = "balanced"  # 旅行风格：relaxed(轻松), balanced(平衡), active(紧凑)
