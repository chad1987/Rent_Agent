import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field


REMOTE_BASE = os.getenv("RENT_API_BASE", "http://7.225.29.223:8080")
DEFAULT_PLATFORM = "安居客"
DISTRICTS = ["海淀", "朝阳", "通州", "昌平", "大兴", "房山", "西城", "丰台", "顺义", "东城"]
PLATFORMS = ["链家", "安居客", "58同城"]


class ChatRequest(BaseModel):
    model_ip: Optional[str] = None
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


@dataclass
class SessionState:
    filters: Dict[str, Any] = field(default_factory=dict)
    last_house_ids: List[str] = field(default_factory=list)
    last_platform: str = DEFAULT_PLATFORM
    initialized: bool = False


class RentAgent:
    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}
        self.client = httpx.AsyncClient(timeout=8.0)
        self.competition_user_id = os.getenv("COMPETITION_USER_ID", "").strip()

    async def close(self) -> None:
        await self.client.aclose()

    def get_state(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState()
        return self.sessions[session_id]

    def get_user_id(self, session_id: str) -> str:
        # 强烈建议线上设置 COMPETITION_USER_ID 为真实工号。
        return self.competition_user_id or session_id

    async def call_api(self, method: str, path: str, *, user_id: Optional[str], params: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
        url = f"{REMOTE_BASE}{path}"
        headers = {"X-User-ID": user_id} if user_id else {}
        try:
            resp = await self.client.request(method, url, params=params, headers=headers)
            data = resp.json()
            return resp.status_code < 400, data
        except Exception as e:
            return False, {"error": str(e), "path": path, "params": params}

    async def ensure_initialized(self, session_id: str) -> Dict[str, Any]:
        state = self.get_state(session_id)
        if state.initialized:
            return {"name": "houses/init", "success": True, "output": "already_initialized"}
        ok, data = await self.call_api("POST", "/api/houses/init", user_id=self.get_user_id(session_id))
        state.initialized = True
        return {"name": "houses/init", "success": ok, "output": data}

    def parse_intent(self, message: str) -> str:
        has_house_id = bool(re.search(r"\bHF_\d+\b", message))
        if has_house_id and any(k in message for k in ["退租", "取消租", "不租"]):
            return "terminate"
        if has_house_id and any(k in message for k in ["下架", "隐藏"]):
            return "offline"
        if has_house_id and any(k in message for k in ["租", "下单", "订"]):
            return "rent"
        if any(k in message for k in ["对比", "比较", "哪个好", "哪套更好"]):
            return "compare"
        if any(k in message for k in ["找", "查询", "筛选", "推荐", "房源", "租房", "看看", "想要"]):
            return "query"
        return "chat"

    def parse_filters(self, message: str, state: SessionState) -> Dict[str, Any]:
        filters = dict(state.filters)

        if any(k in message for k in ["重置", "清空", "重新来", "换一批"]):
            filters = {}

        for district in DISTRICTS:
            if district in message:
                filters["district"] = district

        for p in PLATFORMS:
            if p in message:
                state.last_platform = p

        if "整租" in message:
            filters["rental_type"] = "整租"
        elif "合租" in message:
            filters["rental_type"] = "合租"

        if "有电梯" in message or "电梯房" in message:
            filters["elevator"] = "true"
        elif "无电梯" in message:
            filters["elevator"] = "false"

        for deco in ["豪华", "精装", "简装", "毛坯", "空房"]:
            if deco in message:
                filters["decoration"] = deco

        for ori in ["朝南", "朝北", "朝东", "朝西", "南北", "东西"]:
            if ori in message:
                filters["orientation"] = ori

        if "民水民电" in message:
            filters["utilities_type"] = "民水民电"

        if "近地铁" in message:
            filters["max_subway_dist"] = 800
        elif "地铁可达" in message:
            filters["max_subway_dist"] = 1000

        station_m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,20}站)", message)
        if station_m:
            filters["subway_station"] = station_m.group(1)

        commute_m = re.search(r"(?:通勤|到西二旗)\D{0,4}(\d{1,3})\s*分", message)
        if commute_m:
            filters["commute_to_xierqi_max"] = int(commute_m.group(1))

        bed_map = {
            "一居": "1", "1居": "1", "一室": "1", "1室": "1",
            "两居": "2", "二居": "2", "2居": "2", "二室": "2", "2室": "2",
            "三居": "3", "3居": "3", "三室": "3", "3室": "3",
            "四居": "4", "4居": "4", "四室": "4", "4室": "4",
        }
        for k, v in bed_map.items():
            if k in message:
                filters["bedrooms"] = v
                break

        # 预算
        price_range = re.search(r"(\d{3,5})\s*[-到至]\s*(\d{3,5})", message)
        if price_range:
            low, high = int(price_range.group(1)), int(price_range.group(2))
            filters["min_price"], filters["max_price"] = min(low, high), max(low, high)

        max_price = re.search(r"(?:预算|不超过|最高|以内|以下)\D{0,4}(\d{3,5})", message)
        if max_price:
            filters["max_price"] = int(max_price.group(1))

        min_price = re.search(r"(?:至少|最低|以上)\D{0,4}(\d{3,5})", message)
        if min_price and "平" not in message[max(min_price.start() - 3, 0):min_price.end() + 3]:
            filters["min_price"] = int(min_price.group(1))

        # 面积
        area_range = re.search(r"(\d{2,3})\s*[-到至]\s*(\d{2,3})\s*(?:平|㎡)", message)
        if area_range:
            low, high = int(area_range.group(1)), int(area_range.group(2))
            filters["min_area"], filters["max_area"] = min(low, high), max(low, high)

        min_area = re.search(r"(\d{2,3})\s*(?:平|㎡)\s*(?:以上|起)", message)
        if min_area:
            filters["min_area"] = int(min_area.group(1))

        return filters

    def score_house(self, h: Dict[str, Any], f: Dict[str, Any]) -> float:
        score = 100.0
        price = h.get("price") or 99999
        subway = h.get("subway_distance") or 99999
        commute = h.get("commute_to_xierqi") or 999

        if "max_price" in f:
            score -= max(0, (price - f["max_price"]) / 200)
        else:
            score -= price / 3000

        if "min_price" in f and price < f["min_price"]:
            score -= (f["min_price"] - price) / 300

        if "max_subway_dist" in f:
            score -= max(0, (subway - f["max_subway_dist"]) / 60)
        else:
            score -= subway / 1600

        if "commute_to_xierqi_max" in f:
            score -= max(0, (commute - f["commute_to_xierqi_max"]) / 6)
        else:
            score -= commute / 25

        if f.get("elevator") == "true" and str(h.get("elevator", "")).lower() == "true":
            score += 3

        if f.get("decoration") and f["decoration"] in str(h.get("decoration", "")):
            score += 2

        if f.get("orientation") and f["orientation"] in str(h.get("orientation", "")):
            score += 1

        return score

    async def query_houses(self, session_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
        state = self.get_state(session_id)
        user_id = self.get_user_id(session_id)
        state.filters = self.parse_filters(message, state)

        query = dict(state.filters)
        query["listing_platform"] = state.last_platform
        query["page"] = 1
        query["page_size"] = 120

        ok, data = await self.call_api("GET", "/api/houses/by_platform", user_id=user_id, params=query)
        if not ok:
            result = {"message": "查询失败，请稍后重试", "houses": []}
            return json.dumps(result, ensure_ascii=False), {"name": "houses/by_platform", "success": False, "output": data}

        items = data.get("data", {}).get("items", [])
        ranked = sorted(items, key=lambda x: self.score_house(x, state.filters), reverse=True)
        top = ranked[:5]
        house_ids = [it.get("house_id") for it in top if it.get("house_id")]
        state.last_house_ids = house_ids

        if house_ids:
            message_text = f"共筛到{len(items)}套，已返回匹配度最高的{len(house_ids)}套。"
        else:
            message_text = "没有符合条件的可租房源，建议放宽预算或地铁/通勤条件。"

        result = {"message": message_text, "houses": house_ids}
        tool = {
            "name": "houses/by_platform",
            "success": True,
            "output": {"filters": query, "total": len(items), "top_ids": house_ids},
        }
        return json.dumps(result, ensure_ascii=False), tool

    async def house_action(self, session_id: str, message: str, action: str) -> Tuple[str, Dict[str, Any]]:
        user_id = self.get_user_id(session_id)
        state = self.get_state(session_id)
        house_ids = re.findall(r"\bHF_\d+\b", message)
        if not house_ids and state.last_house_ids:
            house_ids = [state.last_house_ids[0]]

        if not house_ids:
            return "请提供要操作的房源ID（如 HF_2001）。", {"name": action, "success": False, "output": "missing_house_id"}

        house_id = house_ids[0]
        platform = state.last_platform
        for p in PLATFORMS:
            if p in message:
                platform = p
                break

        path = {
            "rent": f"/api/houses/{house_id}/rent",
            "terminate": f"/api/houses/{house_id}/terminate",
            "offline": f"/api/houses/{house_id}/offline",
        }[action]

        ok, data = await self.call_api("POST", path, user_id=user_id, params={"listing_platform": platform})
        text_map = {"rent": "租房", "terminate": "退租", "offline": "下架"}
        if ok:
            return f"已完成{text_map[action]}：{house_id}（{platform}）", {"name": action, "success": True, "output": data}
        return f"{text_map[action]}失败：{data}", {"name": action, "success": False, "output": data}

    async def compare(self, session_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
        user_id = self.get_user_id(session_id)
        state = self.get_state(session_id)
        house_ids = re.findall(r"\bHF_\d+\b", message)
        if len(house_ids) < 2:
            house_ids = state.last_house_ids[:2]
        if len(house_ids) < 2:
            return "请提供两个房源ID，我再帮您做对比。", {"name": "compare", "success": False, "output": "need_two_ids"}

        details: List[Dict[str, Any]] = []
        for hid in house_ids[:2]:
            ok, data = await self.call_api("GET", f"/api/houses/{hid}", user_id=user_id)
            if ok and isinstance(data.get("data"), dict):
                house = data["data"]
                details.append(
                    {
                        "house_id": hid,
                        "district": house.get("district"),
                        "area": house.get("area"),
                        "price": house.get("price"),
                        "subway_distance": house.get("subway_distance"),
                        "commute_to_xierqi": house.get("commute_to_xierqi"),
                    }
                )

        if len(details) < 2:
            return "对比失败：未获取到两套房源详情。", {"name": "compare", "success": False, "output": details}

        a, b = details[0], details[1]
        sa = self.score_house(a, state.filters)
        sb = self.score_house(b, state.filters)
        better = a if sa >= sb else b
        text = (
            f"对比结果：{a['house_id']}(¥{a['price']}，地铁{a['subway_distance']}m，通勤{a.get('commute_to_xierqi')}分) vs "
            f"{b['house_id']}(¥{b['price']}，地铁{b['subway_distance']}m，通勤{b.get('commute_to_xierqi')}分)。"
            f"综合更推荐 {better['house_id']}。"
        )
        return text, {"name": "compare", "success": True, "output": details}


agent = RentAgent()
app = FastAPI(title="Contest Rent Agent")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await agent.close()


@app.post("/api/v1/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    start = time.time()
    tools: List[Dict[str, Any]] = []

    init_tool = await agent.ensure_initialized(req.session_id)
    tools.append(init_tool)

    intent = agent.parse_intent(req.message)
    if intent == "query":
        response, tool = await agent.query_houses(req.session_id, req.message)
        tools.append(tool)
    elif intent in {"rent", "terminate", "offline"}:
        response, tool = await agent.house_action(req.session_id, req.message, intent)
        tools.append(tool)
    elif intent == "compare":
        response, tool = await agent.compare(req.session_id, req.message)
        tools.append(tool)
    else:
        response = "您好，我可以帮您租房。请告诉我预算、区域、户型、是否近地铁、通勤等要求。"

    end = time.time()
    return {
        "session_id": req.session_id,
        "response": response,
        "status": "success",
        "tool_results": tools,
        "timestamp": int(end),
        "duration_ms": int((end - start) * 1000),
    }
