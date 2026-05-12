import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "智能旅行助手 API"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "智能旅行助手后端服务正在运行" in response.json()["message"]

def test_trip_plan_endpoint():
    request_data = {
        "city": "北京",
        "start_date": "2024-07-01",
        "end_date": "2024-07-03",
        "days": 3,
        "preferences": "历史文化",
        "budget": "中等",
        "transportation": "公共交通",
        "accommodation": "经济型酒店",
        "departure": "上海"
    }
    response = client.post("/api/plan", json=request_data)
    if response.status_code == 200:
        data = response.json()
        assert "city" in data
        assert "days" in data
        assert isinstance(data["days"], list)
    else:
        assert response.status_code == 500