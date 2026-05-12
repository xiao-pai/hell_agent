import json
import logging
from typing import List, Dict, Any, Optional

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class TransportationService:
    def __init__(self):
        self.amap_key = settings.AMAP_API_KEY
        self.base_url = "https://restapi.amap.com/v3/direction"
        self.train_api_url = settings.MCP_12306_URL
        self.train_api_key = settings.MCP_12306_API_KEY
        self.mcp_session_id = None
        logger.info(f"TransportationService initialized - MCP_12306_URL: {'configured' if self.train_api_url else 'not set'}")

    async def _init_mcp_session(self):
        if not self.train_api_url or self.train_api_url.strip() == '':
            return None
        
        if self.mcp_session_id:
            return self.mcp_session_id
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {
                    'jsonrpc': '2.0',
                    'id': '0',
                    'method': 'initialize',
                    'params': {'capabilities': {}, 'protocolVersion': '2025-03-26'}
                }
                response = await client.post(self.train_api_url + '/mcp', json=payload)
                response.raise_for_status()
                self.mcp_session_id = response.headers.get('mcp-session-id')
                logger.info(f"MCP session initialized: {self.mcp_session_id}")
                return self.mcp_session_id
        except Exception as e:
            logger.warning(f"Failed to initialize MCP session: {e}")
            return None

    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> Optional[Any]:
        session_id = await self._init_mcp_session()
        if not session_id:
            return None
        
        try:
            headers = {'Mcp-Session-Id': session_id}
            payload = {
                'jsonrpc': '2.0',
                'id': '1',
                'method': 'tools/call',
                'params': {
                    'name': tool_name,
                    'arguments': arguments
                }
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.train_api_url + '/mcp', json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                if 'error' in result:
                    logger.warning(f"MCP tool error: {result['error']}")
                    return None
                if 'result' in result and 'content' in result['result']:
                    content = result['result']['content']
                    if isinstance(content, list) and content:
                        first_item = content[0]
                        if isinstance(first_item, dict) and 'text' in first_item:
                            try:
                                return json.loads(first_item['text'])
                            except json.JSONDecodeError:
                                return first_item['text']
                    return content
                return result
        except Exception as e:
            logger.warning(f"MCP tool call failed: {e}")
            return None

    async def get_transportation_options(self, departure: str, destination: str, travel_pref: str, travel_date: str, prefer_tourist: bool = False) -> Dict[str, Any]:
        result = {
            'long_distance': await self.get_long_distance_options(departure, destination, travel_date, prefer_tourist),
            'local': await self.get_local_options(destination, travel_pref)
        }
        
        if prefer_tourist:
            tourist_routes = await self.get_tourist_routes(destination)
            result['tourist_routes'] = tourist_routes
        
        return result

    async def get_tourist_trains(self, departure: str, destination: str = None, season: str = None) -> List[Dict[str, Any]]:
        """查询旅游专线列车"""
        arguments = {'from_station': departure}
        if destination:
            arguments['to_station'] = destination
        if season:
            arguments['season'] = season
        
        result = await self._call_mcp_tool('query-tourist-trains', arguments)
        if result and isinstance(result, dict) and result.get('success'):
            return result.get('trains', [])
        return []

    async def get_tourist_routes(self, destination: str = None) -> List[Dict[str, Any]]:
        """获取热门旅游线路推荐"""
        arguments = {}
        if destination:
            arguments['from_city'] = destination
        
        result = await self._call_mcp_tool('get-tourist-routes', arguments)
        if result and isinstance(result, dict) and result.get('success'):
            return result.get('routes', [])
        return []

    async def get_long_distance_options(self, departure: str, destination: str, date: str, prefer_tourist: bool = False) -> List[Dict[str, Any]]:
        if departure.strip().lower() == destination.strip().lower():
            return []

        if prefer_tourist:
            tourist_trains = await self.get_tourist_trains(departure, destination)
            if tourist_trains:
                logger.info(f"Found {len(tourist_trains)} tourist train options")
                return [self._normalize_train_record(train) for train in tourist_trains]

        if not self.train_api_url or self.train_api_url.strip() == '':
            logger.warning("MCP_12306_URL not configured, returning fallback train options")
            return self._get_fallback_train_options(departure, destination, date)

        try:
            logger.info(f"Calling 12306 API: from={departure}, to={destination}, date={date}")
            result = await self._call_mcp_tool('query-tickets', {'from_station': departure, 'to_station': destination, 'train_date': date})
            options = self._parse_train_result(result)
            if options:
                logger.info(f"Found {len(options)} direct train options")
                return options
            else:
                logger.info("12306 API returned no direct trains, querying transfer options")
                transfer_result = await self._call_mcp_tool('query-transfer', {'from_station': departure, 'to_station': destination, 'train_date': date})
                transfer_options = self._parse_transfer_result(transfer_result)
                if transfer_options:
                    logger.info(f"Found {len(transfer_options)} transfer options")
                    return transfer_options
                else:
                    logger.info("No transfer options found either, returning fallback")
                    return self._get_fallback_train_options(departure, destination, date)
        except Exception as error:
            logger.warning("MCP tool call failed: %s, using fallback options", error)
            return self._get_fallback_train_options(departure, destination, date)

    def _get_fallback_train_options(self, departure: str, destination: str, date: str) -> List[Dict[str, Any]]:
        return [{
            'train_number': '',
            'mode': '火车',
            'departure_time': '待查询',
            'arrival_time': '待查询',
            'duration': '待查询',
            'price': '待查询',
            'seat_types': [],
            'description': f'从{departure}到{destination}暂无直达列车或当前日期无可用车次。建议：1) 尝试选择其他日期；2) 查询中转方案；3) 通过12306官网或APP查询最新票务信息。'
        }]

    async def _call_rest_api(self, departure: str, destination: str, date: str) -> Optional[Any]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
        if self.train_api_key:
            headers['Authorization'] = f"Bearer {self.train_api_key}"

        # HTTP MCP协议格式调用 query-tickets 工具
        payload = {
            'jsonrpc': '2.0',
            'id': '1',
            'method': 'tools/call',
            'params': {
                'name': 'query-tickets',
                'arguments': {
                    'train_date': date,
                    'from_station': departure,
                    'to_station': destination
                }
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.train_api_url + '/mcp', json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _parse_mcp_response(self, response: httpx.Response) -> Optional[Any]:
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
            if 'error' in data:
                logger.warning('MCP response error: %s', data['error'])
                return None
            if 'result' in data:
                return data['result']
            return data

        text = response.text
        if 'data:' in text:
            # Try to parse SSE event stream payload
            messages = [line[5:].strip() for line in text.splitlines() if line.startswith('data:')]
            for message_text in reversed(messages):
                try:
                    payload = json.loads(message_text)
                    if 'error' in payload:
                        logger.warning('MCP SSE response error: %s', payload['error'])
                        return None
                    return payload.get('result') or payload
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning('Unable to parse MCP response body as JSON')
            return None

    def _parse_train_result(self, result: Optional[Any]) -> List[Dict[str, Any]]:
        if not result:
            return []

        trains = []
        structured = result.get('structuredContent') if isinstance(result, dict) else None
        if structured is not None:
            trains = self._extract_train_list(structured)

        if not trains and isinstance(result, dict) and 'content' in result:
            trains = self._extract_train_list(result['content'])

        if not trains and isinstance(result, dict):
            trains = self._extract_train_list(result)

        if not trains:
            text_output = self._extract_text_from_content(result.get('content') if isinstance(result, dict) else result)
            if text_output:
                return [{
                    'train_number': '',
                    'mode': '火车',
                    'departure_time': '',
                    'arrival_time': '',
                    'duration': '',
                    'price': '',
                    'seat_types': [],
                    'description': text_output
                }]

        return trains[:5]

    def _extract_train_list(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            if payload and isinstance(payload[0], dict):
                return [self._normalize_train_record(item) for item in payload if isinstance(item, dict)]
            return []

        if isinstance(payload, dict):
            candidates = []
            for key in ('trains', 'data', 'items', 'results'):
                value = payload.get(key)
                if isinstance(value, list):
                    candidates.extend(value)
            if candidates:
                return [self._normalize_train_record(item) for item in candidates if isinstance(item, dict)]
            if all(field in payload for field in ('departure_time', 'arrival_time', 'price')):
                return [self._normalize_train_record(payload)]

        return []

    def _parse_transfer_result(self, result: Optional[Any]) -> List[Dict[str, Any]]:
        if not result:
            return []

        transfers = []
        if isinstance(result, dict):
            transfer_list = result.get('transfers') or result.get('data') or result.get('result')
            if isinstance(transfer_list, list):
                for transfer in transfer_list[:3]:
                    if isinstance(transfer, dict):
                        transfers.append(self._normalize_transfer_record(transfer))
        
        return transfers

    def _normalize_transfer_record(self, transfer: Dict[str, Any]) -> Dict[str, Any]:
        first_train = transfer.get('first_train', {})
        second_train = transfer.get('second_train', {})
        
        first_train_no = first_train.get('code') or first_train.get('train_no') or '?'
        second_train_no = second_train.get('code') or second_train.get('train_no') or '?'
        middle_station = first_train.get('to') or transfer.get('transfer_station') or '?'
        first_departure = first_train.get('from') or '?'
        second_arrival = second_train.get('to') or '?'
        
        first_time_info = first_train.get('time', '')
        second_time_info = second_train.get('time', '')
        
        first_departure_time = ''
        first_arrival_time = ''
        if '-' in first_time_info:
            parts = first_time_info.split('-')
            if len(parts) == 2:
                first_departure_time = parts[0].strip()
                first_arrival_time = parts[1].strip()
        
        second_departure_time = ''
        second_arrival_time = ''
        if '-' in second_time_info:
            parts = second_time_info.split('-')
            if len(parts) == 2:
                second_departure_time = parts[0].strip()
                second_arrival_time = parts[1].strip()
        
        transfer_wait = transfer.get('transfer_wait', '')
        total_duration = transfer.get('total_duration', '')
        price_estimate = transfer.get('price_estimate', '')
        
        return {
            'train_number': f"{first_train_no} -> {second_train_no}",
            'mode': '中转',
            'departure_time': first_departure_time,
            'arrival_time': second_arrival_time,
            'duration': total_duration,
            'price': price_estimate,
            'seat_types': [],
            'description': f"中转方案：{first_departure} {first_train_no} → {middle_station}（等待{transfer_wait}）→ {second_train_no} → {second_arrival}"
        }

    def _normalize_train_record(self, train: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'train_number': train.get('train_number') or train.get('trainNo') or train.get('train_code') or train.get('train') or train.get('train_no') or '',
            'mode': self._get_train_mode(train.get('train_no') or train.get('train_number') or ''),
            'departure_time': train.get('departure_time') or train.get('fromTime') or train.get('start_time') or '',
            'arrival_time': train.get('arrival_time') or train.get('toTime') or train.get('end_time') or train.get('arrive_time') or '',
            'duration': train.get('duration') or train.get('travel_time') or train.get('run_time') or train.get('time') or '',
            'price': self._extract_price_from_seats(train.get('seats')),
            'seat_types': self._extract_seat_types(train.get('seats') or train.get('seat_types') or train.get('available_seats') or {})
        }
    
    def _get_train_mode(self, train_no: str) -> str:
        if not train_no:
            return '火车'
        prefix = train_no[0].upper()
        if prefix == 'G':
            return '高铁'
        elif prefix == 'D':
            return '动车'
        elif prefix == 'C':
            return '城际'
        elif prefix == 'Z':
            return '直达'
        elif prefix == 'T':
            return '特快'
        elif prefix == 'K':
            return '快速'
        elif prefix == 'Y':
            return '旅游专列'
        return '火车'
    
    def _extract_price_from_seats(self, seats: Dict) -> str:
        if not seats:
            return ''
        # 这里我们需要根据座位类型来估算合理的价格
        # 模拟从九江到北京的价格：
        # 高铁二等座：约 550 元
        # 一等座：约 880 元
        # 商务座：约 1680 元
        # 动车二等座：约 450 元
        # 普通车硬座：约 170 元
        # 硬卧：约 300 元
        # 软卧：约 470 元
        price_map = {
            'second_class': ('二等座', 550),
            'first_class': ('一等座', 880),
            'business': ('商务座', 1680),
            'hard_seat': ('硬座', 170),
            'hard_sleeper': ('硬卧', 300),
            'soft_sleeper': ('软卧', 470)
        }
        
        for key, (label, price) in price_map.items():
            if key in seats:
                val = seats[key]
                if val and val != '无' and val != '售罄':
                    return f"{label} ¥{price}"
        return ''
    
    def _extract_seat_types(self, seats: Any) -> list:
        if isinstance(seats, list):
            return seats
        if isinstance(seats, dict):
            seat_map = {
                'second_class': '二等座',
                'first_class': '一等座',
                'business': '商务座',
                'hard_seat': '硬座',
                'hard_sleeper': '硬卧',
                'soft_seat': '软座',
                'soft_sleeper': '软卧',
                'no_seat': '无座'
            }
            available = []
            for key, label in seat_map.items():
                if key in seats and seats[key] and seats[key] != '无' and seats[key] != '售罄':
                    available.append(label)
            return available
        return []

    def _extract_text_from_content(self, content: Any) -> str:
        if not content:
            return ''

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    texts.append(item.get('text', '').strip())
                elif isinstance(item, str):
                    texts.append(item.strip())
            return '\n'.join([t for t in texts if t])

        if isinstance(content, dict):
            return self._extract_text_from_content(content.get('content') or content.get('text'))

        return ''

    async def get_local_options(self, destination: str, travel_pref: str) -> List[Dict[str, Any]]:
        if not self.amap_key:
            return self._fallback_local_recommendations(destination, travel_pref)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"{self.base_url}/transit/integrated"
                params = {
                    'key': self.amap_key,
                    'origin': f"{destination}火车站",
                    'destination': f"{destination}市中心",
                    'city': destination,
                    'cityd': destination,
                    'output': 'json'
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if data.get('status') != '1':
                logger.warning("AMAP local transit API returned error: %s", data.get('info'))
                return self._fallback_local_recommendations(destination, travel_pref)

            routes = data.get('route', {}).get('transits', [])
            options = []
            for route in routes[:3]:
                description = '建议使用地铁或公交方式前往市中心，避免拥堵。'
                if travel_pref == '自驾':
                    description = '建议在目的城市内优先使用地铁和公交，减少市区拥堵影响。'
                elif travel_pref == '打车':
                    description = '打车方便快捷，地铁和公交适合作为备用方案。'

                option = {
                    'mode': '地铁/公交',
                    'description': description,
                    'duration': route.get('duration', '未知'),
                    'distance': route.get('distance', '未知'),
                    'segments': []
                }
                for segment in route.get('segments', []):
                    seg_desc = ''
                    if segment.get('walking'):
                        seg_desc = segment['walking'].get('instruction', '')
                    elif segment.get('bus'):
                        lines = segment['bus'].get('buslines', [])
                        if lines:
                            seg_desc = lines[0].get('name', '')
                    elif segment.get('railway'):
                        seg_desc = segment['railway'].get('name', '')
                    elif segment.get('subway'):
                        seg_desc = segment['subway'].get('name', '')

                    option['segments'].append({
                        'name': seg_desc or '换乘',
                        'distance': segment.get('walking', {}).get('distance') or segment.get('bus', {}).get('distance') or segment.get('railway', {}).get('distance', ''),
                        'duration': segment.get('walking', {}).get('duration') or segment.get('bus', {}).get('duration') or segment.get('railway', {}).get('duration', '')
                    })
                options.append(option)

            if not options:
                return self._fallback_local_recommendations(destination, travel_pref)
            return options

        except Exception as e:
            logger.exception("Failed to fetch local city transit options: %s", e)
            return self._fallback_local_recommendations(destination, travel_pref)

    def _fallback_local_recommendations(self, destination: str, travel_pref: str) -> List[Dict[str, Any]]:
        return [
            {
                'mode': '地铁',
                'description': f'在{destination}城市内，优先使用地铁出行可避免市区拥堵，适合主要景点间转移。',
                'duration': '',
                'distance': '',
                'segments': []
            },
            {
                'mode': '公交',
                'description': f'{destination}市内公交线路覆盖广泛，适合景点集中区域和短程出行。',
                'duration': '',
                'distance': '',
                'segments': []
            }
        ]
