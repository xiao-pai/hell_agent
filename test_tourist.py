import asyncio
import json
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        print("=== 1. 初始化连接 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {"capabilities": {}, "protocolVersion": "2025-03-26"}
            }
        )
        session_id = response.headers.get("mcp-session-id")
        print(f"获取到 Session ID: {session_id}")
        
        print("\n=== 2. 查询旅游专线列车 - 九江出发 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "query-tourist-trains", "arguments": {"from_station": "九江"}}
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n=== 3. 查询旅游专线列车 - 九江到庐山 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "query-tourist-trains", "arguments": {"from_station": "九江", "to_station": "庐山"}}
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n=== 4. 获取热门旅游线路推荐 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "get-tourist-routes", "arguments": {"limit": 5}}
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n=== 5. 获取轻松难度的旅游线路 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "get-tourist-routes", "arguments": {"difficulty": "轻松", "limit": 3}}
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n=== 6. 查询春季旅游专列 ===")
        response = await client.post(
            "http://localhost:8888/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "query-tourist-trains", "arguments": {"from_station": "上海", "season": "春季"}}
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())