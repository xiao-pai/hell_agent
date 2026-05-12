import asyncio
import json
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        print("=== 初始化连接 ===")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "capabilities": {},
                    "protocolVersion": "2025-03-26"
                }
            }
        )
        session_id = response.headers.get("mcp-session-id")
        print(f"获取到 Session ID: {session_id}")
        print()
        
        print("=== 1. 搜索九江车站 ===")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search-stations",
                    "arguments": {"query": "九江", "limit": 5}
                }
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        
        print("=== 2. 搜索武汉车站 ===")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search-stations",
                    "arguments": {"query": "武汉", "limit": 5}
                }
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        
        print("=== 3. 查询九江到武汉的车票 ===")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "query-tickets",
                    "arguments": {
                        "from_station": "九江",
                        "to_station": "武汉",
                        "train_date": "2026-05-15"
                    }
                }
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        
        print("=== 4. 查询九江到武汉的票价 ===")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "query-ticket-price",
                    "arguments": {
                        "from_station": "九江",
                        "to_station": "武汉",
                        "train_date": "2026-05-15"
                    }
                }
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())