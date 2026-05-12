import json
import urllib.request
import urllib.error
import sys

url = "http://127.0.0.1:8000/api/plan"
payload = {
    "city": "上海",
    "start_date": "2026-06-01",
    "end_date": "2026-06-03",
    "days": 3,
    "preferences": "文化, 美食, 轻松",
    "budget": "中等",
    "transportation": "地铁优先",
    "accommodation": "市中心舒适型",
    "departure": "杭州"
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        print(resp.status)
        print(body)
except Exception:
    import traceback

    traceback.print_exc()
    sys.exit(1)
