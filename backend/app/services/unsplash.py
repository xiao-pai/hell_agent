import httpx
from backend.app.config import settings

class UnsplashService:
    def __init__(self):
        self.access_key = settings.UNSPLASH_ACCESS_KEY
        self.base_url = "https://api.unsplash.com"

    async def get_photo_url(self, query: str) -> str:
        """根据查询词获取第一张图片的URL"""
        url = f"{self.base_url}/search/photos"
        headers = {"Authorization": f"Client-ID {self.access_key}"}
        params = {"query": query, "per_page": 1}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data["results"]:
                    return data["results"][0]["urls"]["regular"]
        return ""
