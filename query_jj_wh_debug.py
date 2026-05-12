import asyncio
import json
import httpx
import sys

async def query_tickets(date):
    async with httpx.AsyncClient() as client:
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
        
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "query-tickets",
                    "arguments": {
                        "from_station": "九江",
                        "to_station": "武汉",
                        "train_date": date
                    }
                }
            },
            headers={"Mcp-Session-Id": session_id}
        )
        result = response.json()
        if "result" in result and "content" in result["result"]:
            text_content = result["result"]["content"][0]["text"]
            data = json.loads(text_content)
            return data
        return None

async def main():
    print("=== 查询不同日期的车次数量 ===")
    
    today = "2026-05-12"
    tomorrow = "2026-05-13"
    future = "2026-05-15"
    later = "2026-05-20"
    
    dates = [today, tomorrow, future, later]
    for date in dates:
        data = await query_tickets(date)
        if data and data.get("success"):
            count = data.get("count", 0)
            trains = data.get("trains", [])
            print("\n[%s]: %d 趟车次" % (date, count))
            if trains:
                print("  部分车次:")
                for train in trains[:5]:
                    print("    %s: %s -> %s %s-%s (%s)" % (
                        train.get('train_no', ''),
                        train.get('from_station', ''),
                        train.get('to_station', ''),
                        train.get('start_time', ''),
                        train.get('arrive_time', ''),
                        train.get('duration', '')
                    ))
        else:
            print("\n[%s]: 查询失败" % date)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())