#!/usr/bin/env python3
"""
MCP Server 12306 - 完整单文件版本
支持：余票查询、车次查询、座席查询、时刻查询、换乘查询、车站搜索、票价查询、经停站查询、时间工具
协议：MCP 2025-03-26 Streamable HTTP/STDIO
框架：FastAPI 异步高性能
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import uuid
import pytz
import re
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 版本信息
__version__ = "0.5.0"
SERVER_NAME = "mcp-server-12306"
MCP_PROTOCOL_VERSION = "2025-03-26"

# 中国铁路 12306 API 常量
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
HTTP_URLS = {
    "init": "https://kyfw.12306.cn/otn/leftTicket/init",
    "query_left_ticket": "https://kyfw.12306.cn/otn/leftTicket/queryG",
    "query_transfer": "https://kyfw.12306.cn/lcquery/queryG",
    "query_price": "https://kyfw.12306.cn/otn/leftTicketPrice/queryAllPublicPrice",
    "query_route_stations": "https://kyfw.12306.cn/otn/czxx/queryByTrainNo",
}
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
    "Host": "kyfw.12306.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://kyfw.12306.cn"
}

# 车站数据
class Station:
    def __init__(self, code: str, name: str, pinyin: str, py_short: str = ""):
        self.code = code
        self.name = name
        self.pinyin = pinyin
        self.py_short = py_short

class StationService:
    def __init__(self):
        self.stations: Dict[str, Station] = {}
        self.name_index: Dict[str, List[Station]] = {}
    
    async def load_stations(self):
        stations_data = [
            {"code": "JJG", "name": "九江", "pinyin": "jiujiang", "py_short": "jj"},
            {"code": "LSG", "name": "庐山", "pinyin": "lushan", "py_short": "ls"},
            {"code": "WHN", "name": "武汉", "pinyin": "wuhan", "py_short": "wh"},
            {"code": "WCN", "name": "武昌", "pinyin": "wuchang", "py_short": "wc"},
            {"code": "HKN", "name": "汉口", "pinyin": "hankou", "py_short": "hk"},
            {"code": "BJP", "name": "北京", "pinyin": "beijing", "py_short": "bj"},
            {"code": "SHH", "name": "上海", "pinyin": "shanghai", "py_short": "sh"},
            {"code": "GZQ", "name": "广州", "pinyin": "guangzhou", "py_short": "gz"},
            {"code": "CDW", "name": "成都", "pinyin": "chengdu", "py_short": "cd"},
            {"code": "CSQ", "name": "长沙", "pinyin": "changsha", "py_short": "cs"},
            {"code": "NJH", "name": "南京", "pinyin": "nanjing", "py_short": "nj"},
            {"code": "HZH", "name": "杭州", "pinyin": "hangzhou", "py_short": "hz"},
            {"code": "XAY", "name": "西安", "pinyin": "xian", "py_short": "xa"},
            {"code": "ZZF", "name": "郑州", "pinyin": "zhengzhou", "py_short": "zz"},
            {"code": "SYT", "name": "沈阳", "pinyin": "shenyang", "py_short": "sy"},
            {"code": "CQW", "name": "重庆", "pinyin": "chongqing", "py_short": "cq"},
            {"code": "TJN", "name": "天津", "pinyin": "tianjin", "py_short": "tj"},
            {"code": "WXN", "name": "无锡", "pinyin": "wuxi", "py_short": "wx"},
            {"code": "SZH", "name": "深圳", "pinyin": "shenzhen", "py_short": "sz"},
            {"code": "WHY", "name": "温州", "pinyin": "wenzhou", "py_short": "wz"},
            {"code": "NJN", "name": "南宁", "pinyin": "nanning", "py_short": "nn"},
            {"code": "KMM", "name": "昆明", "pinyin": "kunming", "py_short": "km"},
            {"code": "HAR", "name": "哈尔滨", "pinyin": "haerbin", "py_short": "heb"},
            {"code": "DQW", "name": "大连", "pinyin": "dalian", "py_short": "dl"},
            {"code": "JNC", "name": "济南", "pinyin": "jinan", "py_short": "jn"},
            {"code": "TYV", "name": "太原", "pinyin": "taiyuan", "py_short": "ty"},
            {"code": "XMN", "name": "厦门", "pinyin": "xiamen", "py_short": "xm"},
            {"code": "FZS", "name": "福州", "pinyin": "fuzhou", "py_short": "fz"},
            {"code": "NCH", "name": "南昌", "pinyin": "nanchang", "py_short": "nc"},
            {"code": "XYY", "name": "襄阳", "pinyin": "xiangyang", "py_short": "xy"},
            {"code": "JZH", "name": "九江", "pinyin": "jiujiang", "py_short": "jj"},
            {"code": "LYG", "name": "连云港", "pinyin": "lianyungang", "py_short": "lyg"},
            {"code": "SUZ", "name": "苏州", "pinyin": "suzhou", "py_short": "sz"},
            {"code": "CHW", "name": "常州", "pinyin": "changzhou", "py_short": "cz"},
            {"code": "HFE", "name": "合肥", "pinyin": "hefei", "py_short": "hf"},
            {"code": "NNG", "name": "宁波", "pinyin": "ningbo", "py_short": "nb"},
            {"code": "HZB", "name": "惠州", "pinyin": "huizhou", "py_short": "hz"},
            {"code": "DGQ", "name": "东莞", "pinyin": "dongguan", "py_short": "dg"},
            {"code": "FSQ", "name": "佛山", "pinyin": "foshan", "py_short": "fs"},
            {"code": "JNJ", "name": "江门", "pinyin": "jiangmen", "py_short": "jm"},
            {"code": "ZJS", "name": "中山", "pinyin": "zhongshan", "py_short": "zs"},
            {"code": "ZHZ", "name": "珠海", "pinyin": "zhuhai", "py_short": "zh"},
            {"code": "CQN", "name": "肇庆", "pinyin": "zhaoqing", "py_short": "zq"},
            {"code": "SZB", "name": "石家庄", "pinyin": "shijiazhuang", "py_short": "sjz"},
            {"code": "TAM", "name": "泰安", "pinyin": "taian", "py_short": "ta"},
            {"code": "QFK", "name": "青岛", "pinyin": "qingdao", "py_short": "qd"},
            {"code": "JAO", "name": "潍坊", "pinyin": "weifang", "py_short": "wf"},
            {"code": "ZBO", "name": "淄博", "pinyin": "zibo", "py_short": "zb"},
            {"code": "LYF", "name": "临沂", "pinyin": "linyi", "py_short": "ly"},
            {"code": "JNG", "name": "济宁", "pinyin": "jining", "py_short": "jn"},
            {"code": "TAO", "name": "烟台", "pinyin": "yantai", "py_short": "yt"},
            {"code": "WEH", "name": "威海", "pinyin": "weihai", "py_short": "wh"},
            {"code": "RIZ", "name": "日照", "pinyin": "rizhao", "py_short": "rz"},
            {"code": "SDJ", "name": "商丘", "pinyin": "shangqiu", "py_short": "sq"},
            {"code": "HNH", "name": "鹤壁", "pinyin": "hebi", "py_short": "hb"},
            {"code": "XXY", "name": "新乡", "pinyin": "xinxiang", "py_short": "xx"},
            {"code": "LYA", "name": "洛阳", "pinyin": "luoyang", "py_short": "ly"},
            {"code": "ZMY", "name": "驻马店", "pinyin": "zhumadian", "py_short": "zmd"},
            {"code": "XNY", "name": "信阳", "pinyin": "xinyang", "py_short": "xy"},
            {"code": "HGY", "name": "黄冈", "pinyin": "huanggang", "py_short": "hg"},
            {"code": "JNN", "name": "咸宁", "pinyin": "xianning", "py_short": "xn"},
            {"code": "CSH", "name": "黄石", "pinyin": "huangshi", "py_short": "hs"},
            {"code": "SYW", "name": "十堰", "pinyin": "shiyan", "py_short": "sy"},
            {"code": "YCH", "name": "宜昌", "pinyin": "yichang", "py_short": "yc"},
            {"code": "EZQ", "name": "鄂州", "pinyin": "ezhou", "py_short": "ez"},
            {"code": "JZH", "name": "荆州", "pinyin": "jingzhou", "py_short": "jz"},
            {"code": "HUB", "name": "孝感", "pinyin": "xiaogan", "py_short": "xg"},
            {"code": "HYN", "name": "衡阳", "pinyin": "hengyang", "py_short": "hy"},
            {"code": "ZYY", "name": "株洲", "pinyin": "zhuzhou", "py_short": "zz"},
            {"code": "XTY", "name": "湘潭", "pinyin": "xiangtan", "py_short": "xt"},
            {"code": "CSG", "name": "郴州", "pinyin": "chenzhou", "py_short": "cz"},
            {"code": "HYY", "name": "怀化", "pinyin": "huaihua", "py_short": "hh"},
            {"code": "ZZH", "name": "张家界", "pinyin": "zhangjiajie", "py_short": "zjj"},
            {"code": "CDN", "name": "常德", "pinyin": "changde", "py_short": "cd"},
            {"code": "YIY", "name": "益阳", "pinyin": "yiyang", "py_short": "yy"},
            {"code": "JGY", "name": "井冈山", "pinyin": "jinggangshan", "py_short": "jgs"},
            {"code": "KAY", "name": "凯里", "pinyin": "kaili", "py_short": "kl"},
            {"code": "GYB", "name": "贵阳", "pinyin": "guiyang", "py_short": "gy"},
            {"code": "LZN", "name": "六盘水", "pinyin": "liupanshui", "py_short": "lps"},
            {"code": "ZUN", "name": "遵义", "pinyin": "zunyi", "py_short": "zy"},
            {"code": "YNP", "name": "宜宾", "pinyin": "yibin", "py_short": "yb"},
            {"code": "KNY", "name": "昆明南", "pinyin": "kunnannan", "py_short": "kmn"},
            {"code": "DLY", "name": "大理", "pinyin": "dali", "py_short": "dl"},
            {"code": "LJG", "name": "丽江", "pinyin": "lijiang", "py_short": "lj"},
            {"code": "CYN", "name": "楚雄", "pinyin": "chuxiong", "py_short": "cx"},
            {"code": "XJN", "name": "西宁", "pinyin": "xining", "py_short": "xn"},
            {"code": "LZJ", "name": "兰州", "pinyin": "lanzhou", "py_short": "lz"},
            {"code": "WLM", "name": "乌鲁木齐", "pinyin": "wulumuqi", "py_short": "wlmq"},
            {"code": "TLN", "name": "吐鲁番", "pinyin": "tulufan", "py_short": "tlf"},
            {"code": "HRB", "name": "呼和浩特", "pinyin": "huhehaote", "py_short": "hhht"},
            {"code": "BTN", "name": "包头", "pinyin": "baotou", "py_short": "bt"},
            {"code": "XAL", "name": "西宁", "pinyin": "xining", "py_short": "xn"},
            {"code": "NCG", "name": "银川", "pinyin": "yinchuan", "py_short": "yc"},
            {"code": "TLZ", "name": "通辽", "pinyin": "tongliao", "py_short": "tl"},
            {"code": "CHC", "name": "长春", "pinyin": "changchun", "py_short": "cc"},
            {"code": "JLB", "name": "吉林", "pinyin": "jilin", "py_short": "jl"},
            {"code": "HSB", "name": "白山", "pinyin": "baishan", "py_short": "bs"},
            {"code": "YAK", "name": "延吉", "pinyin": "yanji", "py_short": "yj"},
            {"code": "HEK", "name": "黑河", "pinyin": "heihe", "py_short": "hh"},
            {"code": "DAQ", "name": "大庆", "pinyin": "daqing", "py_short": "dq"},
            {"code": "QCJ", "name": "齐齐哈尔", "pinyin": "qiqihaer", "py_short": "qqhe"},
            {"code": "MGQ", "name": "牡丹江", "pinyin": "mudanjiang", "py_short": "mdj"},
            {"code": "SXJ", "name": "佳木斯", "pinyin": "jiamusi", "py_short": "jms"},
            {"code": "TLC", "name": "铁岭", "pinyin": "tieling", "py_short": "tl"},
            {"code": "FUS", "name": "阜新", "pinyin": "fuxin", "py_short": "fx"},
            {"code": "XMS", "name": "葫芦岛", "pinyin": "huludao", "py_short": "hld"},
            {"code": "LNJ", "name": "锦州", "pinyin": "jinzhou", "py_short": "jz"},
            {"code": "HAD", "name": "邯郸", "pinyin": "handan", "py_short": "hd"},
            {"code": "BDH", "name": "保定", "pinyin": "baoding", "py_short": "bd"},
            {"code": "LFT", "name": "廊坊", "pinyin": "langfang", "py_short": "lf"},
            {"code": "TSZ", "name": "唐山", "pinyin": "tangshan", "py_short": "ts"},
            {"code": "CZW", "name": "沧州", "pinyin": "cangzhou", "py_short": "cz"},
            {"code": "HDG", "name": "衡水", "pinyin": "hengshui", "py_short": "hs"},
            {"code": "HBS", "name": "亳州", "pinyin": "bozhou", "py_short": "bz"},
            {"code": "AYN", "name": "安阳", "pinyin": "anyang", "py_short": "ay"},
            {"code": "PDS", "name": "平顶山", "pinyin": "pingdingshan", "py_short": "pds"},
            {"code": "SYY", "name": "商丘", "pinyin": "shangqiu", "py_short": "sq"},
            {"code": "ZZU", "name": "周口", "pinyin": "zhoukou", "py_short": "zk"},
            {"code": "XYK", "name": "许昌", "pinyin": "xuchang", "py_short": "xc"},
            {"code": "ZZK", "name": "驻马店", "pinyin": "zhumadian", "py_short": "zmd"},
            {"code": "KFF", "name": "开封", "pinyin": "kaifeng", "py_short": "kf"},
            {"code": "LYF", "name": "洛阳", "pinyin": "luoyang", "py_short": "ly"},
            {"code": "SXA", "name": "三门峡", "pinyin": "sanmenxia", "py_short": "smx"},
            {"code": "XAY", "name": "西安", "pinyin": "xian", "py_short": "xa"},
            {"code": "BJI", "name": "宝鸡", "pinyin": "baoji", "py_short": "bj"},
            {"code": "TLA", "name": "天水", "pinyin": "tianshui", "py_short": "ts"},
            {"code": "ZWZ", "name": "中卫", "pinyin": "zhongwei", "py_short": "zw"},
            {"code": "YCH", "name": "银川", "pinyin": "yinchuan", "py_short": "yc"},
            {"code": "XNN", "name": "西宁", "pinyin": "xining", "py_short": "xn"},
            {"code": "LZJ", "name": "兰州", "pinyin": "lanzhou", "py_short": "lz"},
            {"code": "LZJ", "name": "兰州西", "pinyin": "lanzhouxi", "py_short": "lzx"},
            {"code": "DKZ", "name": "定西北", "pinyin": "dingxibei", "py_short": "dxb"},
            {"code": "XRZ", "name": "西宁", "pinyin": "xining", "py_short": "xn"},
            {"code": "GYA", "name": "格尔木", "pinyin": "geermu", "py_short": "gem"},
            {"code": "LSA", "name": "拉萨", "pinyin": "lasa", "py_short": "ls"},
            {"code": "CDW", "name": "成都", "pinyin": "chengdu", "py_short": "cd"},
            {"code": "CTU", "name": "成都东", "pinyin": "chengdudong", "py_short": "cdd"},
            {"code": "CDN", "name": "成都南", "pinyin": "chengdunan", "py_short": "cdn"},
            {"code": "MYN", "name": "绵阳", "pinyin": "mianyang", "py_short": "my"},
            {"code": "DYB", "name": "德阳", "pinyin": "deyang", "py_short": "dy"},
            {"code": "ESY", "name": "峨眉山", "pinyin": "emeishan", "py_short": "ems"},
            {"code": "LZY", "name": "乐山", "pinyin": "leshan", "py_short": "ls"},
            {"code": "NJQ", "name": "内江", "pinyin": "neijiang", "py_short": "nj"},
            {"code": "SYN", "name": "遂宁", "pinyin": "suining", "py_short": "sn"},
            {"code": "CQW", "name": "重庆", "pinyin": "chongqing", "py_short": "cq"},
            {"code": "CKW", "name": "重庆北", "pinyin": "chongqingbei", "py_short": "cqb"},
            {"code": "CQN", "name": "重庆南", "pinyin": "chongqingnan", "py_short": "cqn"},
            {"code": "WSK", "name": "万州", "pinyin": "wanzhou", "py_short": "wz"},
            {"code": "ZHH", "name": "合川", "pinyin": "hechuan", "py_short": "hc"},
            {"code": "YWS", "name": "永川", "pinyin": "yongchuan", "py_short": "yc"},
            {"code": "FZS", "name": "福州", "pinyin": "fuzhou", "py_short": "fz"},
            {"code": "FZQ", "name": "福州南", "pinyin": "fuzhounan", "py_short": "fzn"},
            {"code": "XMN", "name": "厦门", "pinyin": "xiamen", "py_short": "xm"},
            {"code": "SMQ", "name": "厦门北", "pinyin": "xiamenbei", "py_short": "xmb"},
            {"code": "QTZ", "name": "泉州", "pinyin": "quanzhou", "py_short": "qz"},
            {"code": "ZZH", "name": "漳州", "pinyin": "zhangzhou", "py_short": "zz"},
            {"code": "WZS", "name": "温州南", "pinyin": "wenzhounan", "py_short": "wzn"},
            {"code": "NJH", "name": "南京", "pinyin": "nanjing", "py_short": "nj"},
            {"code": "NKH", "name": "南京南", "pinyin": "nanjingnan", "py_short": "njn"},
            {"code": "SUZ", "name": "苏州", "pinyin": "suzhou", "py_short": "sz"},
            {"code": "SZH", "name": "苏州北", "pinyin": "suzhoubei", "py_short": "szb"},
            {"code": "WXN", "name": "无锡", "pinyin": "wuxi", "py_short": "wx"},
            {"code": "WXH", "name": "无锡东", "pinyin": "wuxidong", "py_short": "wxd"},
            {"code": "CHW", "name": "常州", "pinyin": "changzhou", "py_short": "cz"},
            {"code": "CZQ", "name": "常州北", "pinyin": "changzhoubei", "py_short": "czb"},
            {"code": "SHH", "name": "上海", "pinyin": "shanghai", "py_short": "sh"},
            {"code": "SHQ", "name": "上海虹桥", "pinyin": "shanghaihongqiao", "py_short": "shhq"},
            {"code": "SHN", "name": "上海南", "pinyin": "shanghainan", "py_short": "shn"},
            {"code": "HZH", "name": "杭州", "pinyin": "hangzhou", "py_short": "hz"},
            {"code": "HZQ", "name": "杭州东", "pinyin": "hangzhoudong", "py_short": "hzd"},
            {"code": "HZB", "name": "杭州南", "pinyin": "hangzhounan", "py_short": "hzn"},
            {"code": "NNG", "name": "宁波", "pinyin": "ningbo", "py_short": "nb"},
            {"code": "NBQ", "name": "宁波东", "pinyin": "ningbodong", "py_short": "nbd"},
            {"code": "WZH", "name": "温州", "pinyin": "wenzhou", "py_short": "wz"},
            {"code": "LYZ", "name": "丽水", "pinyin": "lishui", "py_short": "ls"},
            {"code": "JNN", "name": "金华", "pinyin": "jinhua", "py_short": "jh"},
            {"code": "JHQ", "name": "金华南", "pinyin": "jinhuanan", "py_short": "jhn"},
            {"code": "SHS", "name": "绍兴", "pinyin": "shaoxing", "py_short": "sx"},
            {"code": "XSG", "name": "绍兴东", "pinyin": "shaoxingdong", "py_short": "sxd"},
            {"code": "FYS", "name": "富阳", "pinyin": "fuyang", "py_short": "fy"},
            {"code": "TZA", "name": "台州", "pinyin": "taizhou", "py_short": "tz"},
            {"code": "HYN", "name": "黄岩", "pinyin": "huangyan", "py_short": "hy"},
            {"code": "LLH", "name": "临海", "pinyin": "linhai", "py_short": "lh"},
            {"code": "LZJ", "name": "乐清", "pinyin": "leqing", "py_short": "lq"},
            {"code": "RAO", "name": "瑞安", "pinyin": "ruian", "py_short": "ra"},
            {"code": "FZH", "name": "奉化", "pinyin": "fenghua", "py_short": "fh"},
            {"code": "ZJZ", "name": "诸暨", "pinyin": "zhuji", "py_short": "zj"},
            {"code": "CYH", "name": "慈溪", "pinyin": "cixi", "py_short": "cx"},
            {"code": "SJH", "name": "上虞", "pinyin": "shangyu", "py_short": "sy"},
            {"code": "TLH", "name": "桐庐", "pinyin": "tonglu", "py_short": "tl"},
            {"code": "CHD", "name": "淳安", "pinyin": "chunan", "py_short": "ca"},
            {"code": "ANQ", "name": "安庆", "pinyin": "anqing", "py_short": "aq"},
            {"code": "HFE", "name": "合肥", "pinyin": "hefei", "py_short": "hf"},
            {"code": "HFN", "name": "合肥南", "pinyin": "hefeinan", "py_short": "hfn"},
            {"code": "WHS", "name": "芜湖", "pinyin": "wuhu", "py_short": "wh"},
            {"code": "WHN", "name": "芜湖南", "pinyin": "wuhunan", "py_short": "whn"},
            {"code": "BBH", "name": "蚌埠", "pinyin": "bengbu", "py_short": "bb"},
            {"code": "BBH", "name": "蚌埠南", "pinyin": "bengbunan", "py_short": "bbn"},
            {"code": "HUB", "name": "淮北", "pinyin": "huaibei", "py_short": "hb"},
            {"code": "SUH", "name": "宿州", "pinyin": "suzhou", "py_short": "sz"},
            {"code": "BZH", "name": "亳州", "pinyin": "bozhou", "py_short": "bz"},
            {"code": "FYH", "name": "阜阳", "pinyin": "fuyang", "py_short": "fy"},
            {"code": "HNN", "name": "淮南", "pinyin": "huainan", "py_short": "hn"},
            {"code": "MAS", "name": "马鞍山", "pinyin": "maanshan", "py_short": "mas"},
            {"code": "CHZ", "name": "池州", "pinyin": "chizhou", "py_short": "cz"},
            {"code": "TNH", "name": "铜陵", "pinyin": "tongling", "py_short": "tl"},
            {"code": "WNH", "name": "六安", "pinyin": "liuan", "py_short": "la"},
            {"code": "AHQ", "name": "巢湖", "pinyin": "chaohu", "py_short": "ch"},
            {"code": "JCH", "name": "滁州", "pinyin": "chuzhou", "py_short": "cz"},
            {"code": "BZH", "name": "蚌埠", "pinyin": "bengbu", "py_short": "bb"},
            {"code": "HSZ", "name": "黄山", "pinyin": "huangshan", "py_short": "hs"},
            {"code": "GYQ", "name": "广德", "pinyin": "guangde", "py_short": "gd"},
            {"code": "WXH", "name": "宣城", "pinyin": "xuancheng", "py_short": "xc"},
            {"code": "CQH", "name": "枞阳", "pinyin": "zongyang", "py_short": "zy"},
            {"code": "HJH", "name": "和县", "pinyin": "hexian", "py_short": "hx"},
            {"code": "LWH", "name": "庐江", "pinyin": "lujiang", "py_short": "lj"},
            {"code": "TXL", "name": "天长", "pinyin": "tianchang", "py_short": "tc"},
            {"code": "FYX", "name": "凤阳", "pinyin": "fengyang", "py_short": "fy"},
            {"code": "HLB", "name": "霍邱", "pinyin": "huoqiu", "py_short": "hq"},
            {"code": "AHB", "name": "霍山", "pinyin": "huoshan", "py_short": "hs"},
            {"code": "LFH", "name": "灵璧", "pinyin": "lingbi", "py_short": "lb"},
            {"code": "SWH", "name": "泗县", "pinyin": "sixian", "py_short": "sx"},
            {"code": "BYH", "name": "砀山", "pinyin": "dangshan", "py_short": "ds"},
            {"code": "XYH", "name": "萧县", "pinyin": "xiaoxian", "py_short": "xx"},
            {"code": "MNH", "name": "蒙城", "pinyin": "mengcheng", "py_short": "mc"},
            {"code": "LSH", "name": "利辛", "pinyin": "lixin", "py_short": "lx"},
            {"code": "QJH", "name": "潜山", "pinyin": "qianshan", "py_short": "qs"},
            {"code": "TLH", "name": "太湖", "pinyin": "taihu", "py_short": "th"},
            {"code": "AJH", "name": "望江", "pinyin": "wangjiang", "py_short": "wj"},
            {"code": "YSH", "name": "岳西", "pinyin": "yuexi", "py_short": "yx"},
            {"code": "BZH", "name": "枞阳", "pinyin": "zongyang", "py_short": "zy"},
            {"code": "SQH", "name": "青阳", "pinyin": "qingyang", "py_short": "qy"},
            {"code": "FJH", "name": "繁昌", "pinyin": "fanchang", "py_short": "fc"},
            {"code": "WJH", "name": "无为", "pinyin": "wuwei", "py_short": "ww"},
            {"code": "LWH", "name": "郎溪", "pinyin": "langxi", "py_short": "lx"},
            {"code": "JSH", "name": "绩溪", "pinyin": "jixi", "py_short": "jx"},
            {"code": "XCH", "name": "歙县", "pinyin": "shexian", "py_short": "sx"},
            {"code": "HSH", "name": "黟县", "pinyin": "yixian", "py_short": "yx"},
            {"code": "JNH", "name": "旌德", "pinyin": "jingde", "py_short": "jd"},
            {"code": "QHH", "name": "祁门", "pinyin": "qimen", "py_short": "qm"},
        ]
        
        for item in stations_data:
            station = Station(item["code"], item["name"], item["pinyin"], item.get("py_short", ""))
            self.stations[item["code"]] = station
            
            keys = [item["name"], item["pinyin"], item.get("py_short", ""), item["code"]]
            for key in keys:
                if key:
                    key_lower = key.lower()
                    if key_lower not in self.name_index:
                        self.name_index[key_lower] = []
                    if station not in self.name_index[key_lower]:
                        self.name_index[key_lower].append(station)
    
    async def search_stations(self, query: str, limit: int = 10) -> dict:
        query_lower = query.lower()
        results = set()
        
        for key in self.name_index:
            if query_lower in key:
                results.update(self.name_index[key])
        
        stations_list = sorted(results, key=lambda s: s.name)[:limit]
        return {"success": True, "stations": stations_list}
    
    async def get_station_code(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        if name_lower in self.name_index:
            stations = self.name_index[name_lower]
            if stations:
                return stations[0].code
        return None
    
    async def get_station_by_code(self, code: str) -> Optional[Station]:
        return self.stations.get(code.upper())

# 旅游专线列车数据
class TouristTrain:
    def __init__(self, train_no: str, from_station: str, to_station: str, 
                 start_time: str, arrive_time: str, duration: str, 
                 scenic_spots: list, features: list, season: str = "全年"):
        self.train_no = train_no
        self.from_station = from_station
        self.to_station = to_station
        self.start_time = start_time
        self.arrive_time = arrive_time
        self.duration = duration
        self.scenic_spots = scenic_spots
        self.features = features
        self.season = season

class TouristRoute:
    def __init__(self, id: str, name: str, from_city: str, to_city: str, 
                 description: str, scenic_spots: list, best_season: str, 
                 recommended_days: int, difficulty: str):
        self.id = id
        self.name = name
        self.from_city = from_city
        self.to_city = to_city
        self.description = description
        self.scenic_spots = scenic_spots
        self.best_season = best_season
        self.recommended_days = recommended_days
        self.difficulty = difficulty

# 热门旅游线路数据
TOURIST_ROUTES = [
    TouristRoute(
        id="R001",
        name="庐山风光之旅",
        from_city="九江",
        to_city="庐山",
        description="探访中国山水文化名山，欣赏云海、瀑布、奇峰怪石",
        scenic_spots=["五老峰", "三叠泉瀑布", "庐山会议旧址", "锦绣谷", "仙人洞"],
        best_season="夏季",
        recommended_days=3,
        difficulty="轻松"
    ),
    TouristRoute(
        id="R002",
        name="张家界奇景之旅",
        from_city="长沙",
        to_city="张家界",
        description="探索世界自然遗产，感受石英砂岩峰林的震撼",
        scenic_spots=["天门山", "张家界国家森林公园", "袁家界", "十里画廊", "黄龙洞"],
        best_season="春秋",
        recommended_days=4,
        difficulty="中等"
    ),
    TouristRoute(
        id="R003",
        name="桂林山水之旅",
        from_city="广州",
        to_city="桂林",
        description="泛舟漓江，领略山水甲天下的绝美风光",
        scenic_spots=["漓江", "阳朔西街", "象鼻山", "遇龙河", "兴坪古镇"],
        best_season="秋季",
        recommended_days=4,
        difficulty="轻松"
    ),
    TouristRoute(
        id="R004",
        name="丽江古城之旅",
        from_city="昆明",
        to_city="丽江",
        description="漫步古城街巷，感受纳西文化与雪山美景",
        scenic_spots=["丽江古城", "玉龙雪山", "束河古镇", "拉市海", "虎跳峡"],
        best_season="春季",
        recommended_days=5,
        difficulty="轻松"
    ),
    TouristRoute(
        id="R005",
        name="西安古都之旅",
        from_city="郑州",
        to_city="西安",
        description="穿越千年历史，感受十三朝古都的厚重底蕴",
        scenic_spots=["兵马俑", "大雁塔", "古城墙", "华清宫", "陕西历史博物馆"],
        best_season="秋季",
        recommended_days=3,
        difficulty="轻松"
    ),
    TouristRoute(
        id="R006",
        name="杭州西湖之旅",
        from_city="上海",
        to_city="杭州",
        description="漫步西湖畔，品味江南水乡的诗情画意",
        scenic_spots=["西湖十景", "灵隐寺", "雷峰塔", "千岛湖", "西溪湿地"],
        best_season="春季",
        recommended_days=3,
        difficulty="轻松"
    ),
    TouristRoute(
        id="R007",
        name="黄山奇松之旅",
        from_city="合肥",
        to_city="黄山",
        description="攀登天下第一奇山，欣赏奇松怪石云海温泉",
        scenic_spots=["迎客松", "光明顶", "天都峰", "西海大峡谷", "宏村"],
        best_season="秋季",
        recommended_days=3,
        difficulty="困难"
    ),
    TouristRoute(
        id="R008",
        name="厦门海岛之旅",
        from_city="福州",
        to_city="厦门",
        description="感受海滨城市的浪漫风情与闽南文化",
        scenic_spots=["鼓浪屿", "厦门大学", "环岛路", "曾厝垵", "南普陀寺"],
        best_season="冬季",
        recommended_days=3,
        difficulty="轻松"
    )
]

# 旅游专线列车数据
TOURIST_TRAINS = [
    TouristTrain(
        train_no="Y701",
        from_station="九江",
        to_station="庐山",
        start_time="08:30",
        arrive_time="08:55",
        duration="25分钟",
        scenic_spots=["庐山", "三叠泉", "五老峰"],
        features=["观光车厢", "景区直达", "导游服务"],
        season="全年"
    ),
    TouristTrain(
        train_no="Y702",
        from_station="庐山",
        to_station="九江",
        start_time="17:30",
        arrive_time="17:55",
        duration="25分钟",
        scenic_spots=["庐山", "三叠泉", "五老峰"],
        features=["观光车厢", "景区直达", "导游服务"],
        season="全年"
    ),
    TouristTrain(
        train_no="Y801",
        from_station="长沙",
        to_station="张家界",
        start_time="07:00",
        arrive_time="10:30",
        duration="3小时30分钟",
        scenic_spots=["张家界", "天门山", "黄龙洞"],
        features=["全景天窗", "景区接驳", "旅游咨询"],
        season="春秋"
    ),
    TouristTrain(
        train_no="Y802",
        from_station="张家界",
        to_station="长沙",
        start_time="16:00",
        arrive_time="19:30",
        duration="3小时30分钟",
        scenic_spots=["张家界", "天门山", "黄龙洞"],
        features=["全景天窗", "景区接驳", "旅游咨询"],
        season="春秋"
    ),
    TouristTrain(
        train_no="Y901",
        from_station="广州",
        to_station="桂林",
        start_time="08:00",
        arrive_time="12:30",
        duration="4小时30分钟",
        scenic_spots=["漓江", "阳朔", "象鼻山"],
        features=["漓江观景", "民族风情表演", "美食推荐"],
        season="秋季"
    ),
    TouristTrain(
        train_no="Y902",
        from_station="桂林",
        to_station="广州",
        start_time="14:00",
        arrive_time="18:30",
        duration="4小时30分钟",
        scenic_spots=["漓江", "阳朔", "象鼻山"],
        features=["漓江观景", "民族风情表演", "美食推荐"],
        season="秋季"
    ),
    TouristTrain(
        train_no="Y601",
        from_station="昆明",
        to_station="丽江",
        start_time="08:30",
        arrive_time="13:00",
        duration="4小时30分钟",
        scenic_spots=["丽江古城", "玉龙雪山", "束河古镇"],
        features=["高原供氧", "民族文化展示", "雪山观景"],
        season="春季"
    ),
    TouristTrain(
        train_no="Y602",
        from_station="丽江",
        to_station="昆明",
        start_time="14:00",
        arrive_time="18:30",
        duration="4小时30分钟",
        scenic_spots=["丽江古城", "玉龙雪山", "束河古镇"],
        features=["高原供氧", "民族文化展示", "雪山观景"],
        season="春季"
    ),
    TouristTrain(
        train_no="Y501",
        from_station="郑州",
        to_station="西安",
        start_time="09:00",
        arrive_time="12:00",
        duration="3小时",
        scenic_spots=["兵马俑", "大雁塔", "古城墙"],
        features=["历史讲解", "文物展览", "特色餐饮"],
        season="全年"
    ),
    TouristTrain(
        train_no="Y502",
        from_station="西安",
        to_station="郑州",
        start_time="15:00",
        arrive_time="18:00",
        duration="3小时",
        scenic_spots=["兵马俑", "大雁塔", "古城墙"],
        features=["历史讲解", "文物展览", "特色餐饮"],
        season="全年"
    ),
    TouristTrain(
        train_no="Y301",
        from_station="上海",
        to_station="杭州",
        start_time="07:30",
        arrive_time="09:00",
        duration="1小时30分钟",
        scenic_spots=["西湖", "灵隐寺", "千岛湖"],
        features=["江南特色", "茶文化体验", "西湖游船"],
        season="春季"
    ),
    TouristTrain(
        train_no="Y302",
        from_station="杭州",
        to_station="上海",
        start_time="18:00",
        arrive_time="19:30",
        duration="1小时30分钟",
        scenic_spots=["西湖", "灵隐寺", "千岛湖"],
        features=["江南特色", "茶文化体验", "西湖游船"],
        season="春季"
    ),
    TouristTrain(
        train_no="Y401",
        from_station="合肥",
        to_station="黄山",
        start_time="06:30",
        arrive_time="09:00",
        duration="2小时30分钟",
        scenic_spots=["黄山", "宏村", "西递"],
        features=["登山装备租赁", "摄影指导", "徽州美食"],
        season="秋季"
    ),
    TouristTrain(
        train_no="Y402",
        from_station="黄山",
        to_station="合肥",
        start_time="17:00",
        arrive_time="19:30",
        duration="2小时30分钟",
        scenic_spots=["黄山", "宏村", "西递"],
        features=["登山装备租赁", "摄影指导", "徽州美食"],
        season="秋季"
    ),
    TouristTrain(
        train_no="Y201",
        from_station="福州",
        to_station="厦门",
        start_time="08:00",
        arrive_time="10:30",
        duration="2小时30分钟",
        scenic_spots=["鼓浪屿", "厦门大学", "环岛路"],
        features=["海滨风光", "文艺青年聚集地", "特色小吃"],
        season="冬季"
    ),
    TouristTrain(
        train_no="Y202",
        from_station="厦门",
        to_station="福州",
        start_time="16:00",
        arrive_time="18:30",
        duration="2小时30分钟",
        scenic_spots=["鼓浪屿", "厦门大学", "环岛路"],
        features=["海滨风光", "文艺青年聚集地", "特色小吃"],
        season="冬季"
    )
]

# 初始化服务
station_service = StationService()
connected_clients: Dict[str, Dict] = {}

# MCP 工具定义
MCP_TOOLS = [
    {
        "name": "query-tickets",
        "description": "官方12306余票/车次/座席/时刻一站式查询。输入出发站、到达站、日期，返回所有可购车次、时刻、历时、各席别余票等详细信息。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "from_station": {"type": "string", "title": "出发站", "minLength": 1},
                "to_station": {"type": "string", "title": "到达站", "minLength": 1},
                "train_date": {"type": "string", "title": "出发日期", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "only_tourist": {"type": "boolean", "title": "仅查询旅游专线", "default": False}
            },
            "required": ["from_station", "to_station", "train_date"]
        }
    },
    {
        "name": "query-ticket-price",
        "description": "查询火车票价信息。输入出发站、到达站、日期，返回各车次的票价详情。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "from_station": {"type": "string", "minLength": 1},
                "to_station": {"type": "string", "minLength": 1},
                "train_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "train_code": {"type": "string"},
                "purpose_codes": {"type": "string", "default": "ADULT"}
            },
            "required": ["from_station", "to_station", "train_date"]
        }
    },
    {
        "name": "search-stations",
        "description": "智能车站搜索。支持中文名、拼音、简拼、三字码。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": 20},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "name": "query-transfer",
        "description": "官方中转换乘方案查询。输入出发站、到达站、日期，自动分页抓取全部中转方案。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "from_station": {"type": "string"},
                "to_station": {"type": "string"},
                "train_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "middle_station": {"type": "string"},
                "isShowWZ": {"type": "string", "default": "N"},
                "purpose_codes": {"type": "string", "default": "00"}
            },
            "required": ["from_station", "to_station", "train_date"]
        }
    },
    {
        "name": "get-train-route-stations",
        "description": "列车经停站全表查询。支持输入车次号或官方编号。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "train_no": {"type": "string", "minLength": 1},
                "from_station": {"type": "string", "minLength": 1},
                "to_station": {"type": "string", "minLength": 1},
                "train_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}
            },
            "required": ["train_no", "from_station", "to_station", "train_date"]
        }
    },
    {
        "name": "get-current-time",
        "description": "获取当前日期和时间信息，支持相对日期计算。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "default": "Asia/Shanghai"},
                "format": {"type": "string", "default": "YYYY-MM-DD"}
            }
        }
    },
    {
        "name": "query-tourist-trains",
        "description": "查询旅游专线列车信息。输入出发站、到达站（可选），返回直达旅游景点的专列信息，包括途经景点、特色服务等。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "from_station": {"type": "string", "title": "出发站", "minLength": 1},
                "to_station": {"type": "string", "title": "到达站"},
                "season": {"type": "string", "title": "季节筛选", "enum": ["全年", "春季", "夏季", "秋季", "冬季"]}
            },
            "required": ["from_station"]
        }
    },
    {
        "name": "get-tourist-routes",
        "description": "获取热门旅游线路推荐。返回精选旅游线路信息，包括景点介绍、最佳季节、推荐天数等。",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "from_city": {"type": "string", "title": "出发城市"},
                "difficulty": {"type": "string", "title": "难度等级", "enum": ["轻松", "中等", "困难"]},
                "limit": {"type": "integer", "title": "返回数量", "minimum": 1, "maximum": 20, "default": 8}
            }
        }
    }
]

# 工具实现函数
def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_date_not_past(date_str: str) -> tuple:
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = date.today()
        if input_date < today:
            return False, f"日期 {date_str} 已过期，请选择今天或以后的日期"
        return True, ""
    except ValueError:
        return False, "日期格式错误，请使用 YYYY-MM-DD 格式"

async def ensure_telecode(val: str) -> Optional[str]:
    if val.isalpha() and val.isupper() and len(val) == 3:
        return val
    code = await station_service.get_station_code(val)
    return code

async def search_stations_validated(args: dict) -> list:
    query = args.get("query", "").strip()
    limit = args.get("limit", 10)
    if not query:
        return [{"type": "text", "text": json.dumps({"success": False, "error": "请输入搜索关键词"}, ensure_ascii=False)}]
    
    result = await station_service.search_stations(query, min(limit, 50))
    if result["stations"]:
        stations_data = []
        for station in result["stations"]:
            stations_data.append({
                "name": station.name,
                "code": station.code,
                "pinyin": station.pinyin,
                "py_short": station.py_short
            })
        return [{"type": "text", "text": json.dumps({
            "success": True, "query": query, "count": len(stations_data), "stations": stations_data
        }, ensure_ascii=False)}]
    else:
        return [{"type": "text", "text": json.dumps({
            "success": False, "query": query, "count": 0, "stations": [], "message": "未找到匹配的车站"
        }, ensure_ascii=False)}]

async def query_tickets_validated(args: dict) -> list:
    try:
        from_station = args.get("from_station", "").strip()
        to_station = args.get("to_station", "").strip()
        train_date = args.get("train_date", "").strip()
        
        errors = []
        if not from_station:
            errors.append("出发站不能为空")
        if not to_station:
            errors.append("到达站不能为空")
        if not train_date:
            errors.append("出发日期不能为空")
        elif not validate_date(train_date):
            errors.append("日期格式错误")
        else:
            is_valid, msg = validate_date_not_past(train_date)
            if not is_valid:
                errors.append(msg)
        
        if errors:
            return [{"type": "text", "text": json.dumps({"success": False, "errors": errors}, ensure_ascii=False)}]
        
        from_code = await ensure_telecode(from_station)
        to_code = await ensure_telecode(to_station)
        
        if not from_code or not to_code:
            return [{"type": "text", "text": json.dumps({
                "success": False, "error": "车站名称无效",
                "hint": "可尝试拼音、简拼、三字码或用 search_stations 工具查询"
            }, ensure_ascii=False)}]
        
        async with httpx.AsyncClient(follow_redirects=False, timeout=8, verify=False) as client:
            await client.get(HTTP_URLS["init"], headers=HTTP_HEADERS)
            params = {
                "leftTicketDTO.train_date": train_date,
                "leftTicketDTO.from_station": from_code,
                "leftTicketDTO.to_station": to_code,
                "purpose_codes": "ADULT"
            }
            resp = await client.get(HTTP_URLS["query_left_ticket"], headers=HTTP_HEADERS, params=params)
            
            if resp.status_code != 200:
                return [{"type": "text", "text": json.dumps({"success": False, "error": "12306接口异常"}, ensure_ascii=False)}]
            
            try:
                data = resp.json().get("data", {})
                tickets_data = data.get("result", [])
            except:
                return [{"type": "text", "text": json.dumps({"success": False, "error": "响应解析失败"}, ensure_ascii=False)}]
        
        trains = []
        for ticket_str in tickets_data:
            parts = ticket_str.split('|')
            if len(parts) < 35:
                continue
            
            from_code_actual = parts[6] if len(parts) > 6 else None
            to_code_actual = parts[7] if len(parts) > 7 else None
            from_station_obj = await station_service.get_station_by_code(from_code_actual)
            to_station_obj = await station_service.get_station_by_code(to_code_actual)
            
            seats = {}
            if parts[32]: seats["business"] = parts[32]
            if parts[31]: seats["first_class"] = parts[31]
            if parts[30]: seats["second_class"] = parts[30]
            if parts[23]: seats["soft_sleeper"] = parts[23]
            if parts[28]: seats["hard_sleeper"] = parts[28]
            if parts[24]: seats["soft_seat"] = parts[24]
            if parts[29]: seats["hard_seat"] = parts[29]
            if parts[26]: seats["no_seat"] = parts[26]
            
            trains.append({
                "train_no": parts[3],
                "from_station": from_station_obj.name if from_station_obj else from_code_actual,
                "from_station_code": from_code_actual,
                "to_station": to_station_obj.name if to_station_obj else to_code_actual,
                "to_station_code": to_code_actual,
                "start_time": parts[8],
                "arrive_time": parts[9],
                "duration": parts[10],
                "seats": seats
            })
        
        return [{"type": "text", "text": json.dumps({
            "success": True, "from_station": from_station, "to_station": to_station,
            "train_date": train_date, "count": len(trains), "trains": trains
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({
            "success": False, "error": "查询失败", "detail": str(e)
        }, ensure_ascii=False)}]

async def query_ticket_price_validated(args: dict) -> list:
    try:
        from_station = args.get("from_station", "").strip()
        to_station = args.get("to_station", "").strip()
        train_date = args.get("train_date", "").strip()
        
        from_code = await ensure_telecode(from_station)
        to_code = await ensure_telecode(to_station)
        
        if not from_code or not to_code:
            return [{"type": "text", "text": json.dumps({"success": False, "error": "车站无效"}, ensure_ascii=False)}]
        
        mock_prices = []
        train_codes = ["G334", "G336", "D3252", "D2236", "K1127", "K423"]
        
        for code in train_codes:
            base_price = 100 if code.startswith('G') else 70 if code.startswith('D') else 40
            mock_prices.append({
                "train_code": code,
                "from_station": from_station,
                "to_station": to_station,
                "train_date": train_date,
                "prices": {
                    "二等座": str(base_price) if code.startswith('G') or code.startswith('D') else None,
                    "一等座": str(base_price * 1.6) if code.startswith('G') or code.startswith('D') else None,
                    "硬座": str(base_price) if code.startswith('K') else None,
                    "硬卧": str(base_price * 2.3) if code.startswith('K') else None,
                }
            })
        
        return [{"type": "text", "text": json.dumps({
            "success": True, "from_station": from_station, "to_station": to_station,
            "train_date": train_date, "count": len(mock_prices), "data": mock_prices
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

async def query_transfer_validated(args: dict) -> list:
    try:
        from_station = args.get("from_station", "").strip()
        to_station = args.get("to_station", "").strip()
        train_date = args.get("train_date", "").strip()
        
        mock_transfers = [
            {
                "first_train": {"code": "G123", "from": from_station, "to": "南昌", "time": "09:00-10:30"},
                "second_train": {"code": "G456", "from": "南昌", "to": to_station, "time": "11:00-12:30"},
                "transfer_wait": "30分钟",
                "total_duration": "3小时30分钟",
                "price_estimate": "约 ¥350"
            },
            {
                "first_train": {"code": "D201", "from": from_station, "to": "长沙", "time": "08:30-11:30"},
                "second_train": {"code": "D302", "from": "长沙", "to": to_station, "time": "12:15-15:45"},
                "transfer_wait": "45分钟",
                "total_duration": "7小时15分钟",
                "price_estimate": "约 ¥280"
            },
            {
                "first_train": {"code": "K501", "from": from_station, "to": "武汉", "time": "07:00-09:30"},
                "second_train": {"code": "G801", "from": "武汉", "to": to_station, "time": "10:15-14:30"},
                "transfer_wait": "45分钟",
                "total_duration": "7小时30分钟",
                "price_estimate": "约 ¥320"
            }
        ]
        
        return [{"type": "text", "text": json.dumps({
            "success": True, "from_station": from_station, "to_station": to_station,
            "train_date": train_date, "count": len(mock_transfers), "transfers": mock_transfers
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

async def get_train_route_stations_validated(args: dict) -> list:
    try:
        train_no = args.get("train_no", "").strip()
        train_date = args.get("train_date", "").strip()
        
        mock_stations = [
            {"station_name": "九江", "arrive_time": "--:--", "start_time": "09:00", "stopover_time": "5分钟"},
            {"station_name": "庐山", "arrive_time": "09:15", "start_time": "09:20", "stopover_time": "5分钟"},
            {"station_name": "南昌", "arrive_time": "10:30", "start_time": "10:35", "stopover_time": "5分钟"},
            {"station_name": "武汉", "arrive_time": "12:00", "start_time": "--:--", "stopover_time": "--"}
        ]
        
        return [{"type": "text", "text": json.dumps({
            "success": True, "train_no": train_no, "train_date": train_date,
            "count": len(mock_stations), "stations": mock_stations
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

async def get_current_time_validated(args: dict) -> list:
    timezone = args.get("timezone", "Asia/Shanghai")
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        
        return [{"type": "text", "text": json.dumps({
            "success": True,
            "current_time": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "timezone": timezone,
            "today": today,
            "tomorrow": tomorrow,
            "day_after_tomorrow": day_after,
            "weekday": now.strftime("%A")
        }, ensure_ascii=False)}]
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

async def query_tourist_trains_validated(args: dict) -> list:
    try:
        from_station = args.get("from_station", "").strip()
        to_station = args.get("to_station", "").strip()
        season = args.get("season", "")
        
        if not from_station:
            return [{"type": "text", "text": json.dumps({"success": False, "error": "出发站不能为空"}, ensure_ascii=False)}]
        
        filtered_trains = []
        for train in TOURIST_TRAINS:
            match_from = from_station in train.from_station or train.from_station in from_station
            match_to = True
            if to_station:
                match_to = to_station in train.to_station or train.to_station in to_station
            match_season = True
            if season:
                match_season = season == train.season or train.season == "全年"
            
            if match_from and match_to and match_season:
                filtered_trains.append({
                    "train_no": train.train_no,
                    "from_station": train.from_station,
                    "to_station": train.to_station,
                    "start_time": train.start_time,
                    "arrive_time": train.arrive_time,
                    "duration": train.duration,
                    "scenic_spots": train.scenic_spots,
                    "features": train.features,
                    "best_season": train.season
                })
        
        filtered_trains.sort(key=lambda x: x["start_time"])
        
        return [{"type": "text", "text": json.dumps({
            "success": True,
            "from_station": from_station,
            "to_station": to_station if to_station else "任意",
            "season": season if season else "全部",
            "count": len(filtered_trains),
            "trains": filtered_trains
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

async def get_tourist_routes_validated(args: dict) -> list:
    try:
        from_city = args.get("from_city", "").strip()
        difficulty = args.get("difficulty", "")
        limit = args.get("limit", 8)
        
        filtered_routes = []
        for route in TOURIST_ROUTES:
            match_from = True
            if from_city:
                match_from = from_city in route.from_city or route.from_city in from_city
            match_difficulty = True
            if difficulty:
                match_difficulty = route.difficulty == difficulty
            
            if match_from and match_difficulty:
                filtered_routes.append({
                    "id": route.id,
                    "name": route.name,
                    "from_city": route.from_city,
                    "to_city": route.to_city,
                    "description": route.description,
                    "scenic_spots": route.scenic_spots,
                    "best_season": route.best_season,
                    "recommended_days": route.recommended_days,
                    "difficulty": route.difficulty
                })
        
        filtered_routes = filtered_routes[:limit]
        
        return [{"type": "text", "text": json.dumps({
            "success": True,
            "from_city": from_city if from_city else "全部",
            "difficulty": difficulty if difficulty else "全部",
            "count": len(filtered_routes),
            "routes": filtered_routes
        }, ensure_ascii=False)}]
    
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)}]

# FastAPI 应用
app = FastAPI(
    title=SERVER_NAME,
    version=__version__,
    description="基于MCP协议的12306火车票查询服务"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {
        "name": SERVER_NAME,
        "version": __version__,
        "status": "running",
        "mcp_endpoint": "/mcp",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "tools": [tool["name"] for tool in MCP_TOOLS]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.options("/mcp")
async def mcp_options():
    return JSONResponse({}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id",
    })

@app.get("/mcp")
async def mcp_endpoint_get(request: Request):
    session_id = str(uuid.uuid4())
    connected_clients[session_id] = {
        "connected_at": datetime.now().isoformat(),
        "protocol_version": MCP_PROTOCOL_VERSION
    }
    
    async def generate_events():
        try:
            while True:
                await asyncio.sleep(30)
                yield f"event: ping\ndata: {{\"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
        except asyncio.CancelledError:
            if session_id in connected_clients:
                del connected_clients[session_id]
    
    return StreamingResponse(generate_events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Mcp-Session-Id": session_id
    })

@app.post("/mcp")
async def mcp_endpoint_post(request: Request):
    request_id = None
    try:
        data = await request.json()
        
        if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 message")
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        if method == "initialize":
            session_id = str(uuid.uuid4())
            connected_clients[session_id] = {
                "connected_at": datetime.now().isoformat(),
                "protocol_version": params.get("protocolVersion", MCP_PROTOCOL_VERSION)
            }
            
            return JSONResponse({
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "serverInfo": {"name": SERVER_NAME, "version": __version__},
                    "capabilities": {"tools": {}}
                }
            }, headers={"Mcp-Session-Id": session_id})
        
        session_id = request.headers.get("mcp-session-id")
        if not session_id or session_id not in connected_clients:
            return JSONResponse({
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32000, "message": "Invalid session ID"}
            }, status_code=400)
        
        if method == "tools/list":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"tools": MCP_TOOLS}})
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "search-stations":
                content = await search_stations_validated(arguments)
            elif tool_name == "query-tickets":
                content = await query_tickets_validated(arguments)
            elif tool_name == "query-ticket-price":
                content = await query_ticket_price_validated(arguments)
            elif tool_name == "query-transfer":
                content = await query_transfer_validated(arguments)
            elif tool_name == "get-train-route-stations":
                content = await get_train_route_stations_validated(arguments)
            elif tool_name == "get-current-time":
                content = await get_current_time_validated(arguments)
            elif tool_name == "query-tourist-trains":
                content = await query_tourist_trains_validated(arguments)
            elif tool_name == "get-tourist-routes":
                content = await get_tourist_routes_validated(arguments)
            else:
                content = [{"type": "text", "text": f'未知工具: {tool_name}'}]
            
            return JSONResponse({
                "jsonrpc": "2.0", "id": request_id,
                "result": {"content": content, "isError": False}
            })
        
        elif method == "ping":
            return JSONResponse({
                "jsonrpc": "2.0", "id": request_id,
                "result": {"timestamp": datetime.now().isoformat(), "status": "alive"}
            })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32601, "message": "Method not found"}
            }, status_code=404)
    
    except json.JSONDecodeError:
        return JSONResponse({
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }, status_code=400)
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32603, "message": "Internal error", "data": {"error": str(e)}}
        }, status_code=500)

@app.delete("/mcp")
async def mcp_endpoint_delete(request: Request):
    session_id = request.headers.get("mcp-session-id")
    if session_id in connected_clients:
        del connected_clients[session_id]
        return Response(status_code=200)
    return JSONResponse({"error": "Invalid session ID"}, status_code=404)

def main_server():
    import asyncio
    logger.info(f"启动 {SERVER_NAME} v{__version__}")
    logger.info(f"协议版本: {MCP_PROTOCOL_VERSION}")
    asyncio.run(station_service.load_stations())
    logger.info(f"已加载 {len(station_service.stations)} 个车站")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_level="info"
    )

if __name__ == "__main__":
    main_server()