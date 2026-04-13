"""活动中心与分享能力。"""

from __future__ import annotations

import io
import secrets
from datetime import datetime
from typing import Any, Dict, List

from utils import RUNTIME_DIR, get_settings, read_json, write_json

ACTIVITY_PATH = RUNTIME_DIR / "activities.json"

DEFAULT_ACTIVITY_TEMPLATES: List[Dict[str, Any]] = [
    {
        "activity_id": "knowledge-contest",
        "name": "长征精神知识竞赛",
        "description": "面向课堂、团日活动和专题学习的标准化竞赛模板。",
        "mode": "知识竞赛",
        "time_range": "长期开放",
        "node_scope": ["ruijin_departure", "xiangjiang_battle", "zunyi_meeting", "sidu_chishui", "luding_bridge", "huining_meeting"],
        "status": "进行中",
        "created_by": "system",
    },
    {
        "activity_id": "party-study-day",
        "name": "党史学习日",
        "description": "聚焦转折会议、长征精神和理论学习的专题活动模板。",
        "mode": "党史学习日",
        "time_range": "90分钟",
        "node_scope": ["tongdao_turn", "liping_meeting", "houchang_meeting", "zunyi_meeting", "bangluo_meeting"],
        "status": "进行中",
        "created_by": "system",
    },
    {
        "activity_id": "study-tour-task",
        "name": "红色研学任务",
        "description": "适合景区、纪念馆与研学团使用的沉浸式路线任务。",
        "mode": "研学任务",
        "time_range": "120分钟",
        "node_scope": ["ruijin_departure", "yudu_crossing", "xiangjiang_battle", "luding_bridge", "grassland_crossing", "wuqi_meeting"],
        "status": "进行中",
        "created_by": "system",
    },
]


def _load_activities() -> List[Dict[str, Any]]:
    """读取活动列表。"""
    activities = read_json(ACTIVITY_PATH, []) or []
    if not activities:
        write_json(ACTIVITY_PATH, DEFAULT_ACTIVITY_TEMPLATES)
        return [item.copy() for item in DEFAULT_ACTIVITY_TEMPLATES]
    return activities


def _save_activities(activities: List[Dict[str, Any]]) -> None:
    """保存活动列表。"""
    write_json(ACTIVITY_PATH, activities)


def list_activities() -> List[Dict[str, Any]]:
    """列出活动。"""
    return sorted(_load_activities(), key=lambda item: item.get("name", ""))


def get_activity(activity_id: str = "") -> Dict[str, Any]:
    """按 id 获取活动。"""
    for item in _load_activities():
        if item.get("activity_id") == activity_id:
            return item.copy()
    return {}


def create_activity(
    *,
    name: str,
    mode: str,
    description: str,
    time_range: str,
    node_scope: List[str],
    created_by: str = "admin",
) -> Dict[str, Any]:
    """创建活动。"""
    activities = _load_activities()
    activity_id = f"act-{secrets.token_hex(4)}"
    activity = {
        "activity_id": activity_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode.strip() or "知识竞赛",
        "time_range": time_range.strip() or "60分钟",
        "node_scope": [item for item in node_scope if item],
        "status": "进行中",
        "created_by": created_by,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    activities.append(activity)
    _save_activities(activities)
    return activity


def update_activity(activity_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新活动。"""
    activities = _load_activities()
    updated: Dict[str, Any] = {}
    for index, item in enumerate(activities):
        if item.get("activity_id") != activity_id:
            continue
        item = item.copy()
        item.update({key: value for key, value in patch.items() if value is not None})
        activities[index] = item
        updated = item
        break
    if updated:
        _save_activities(activities)
    return updated


def build_activity_share_link(activity: Dict[str, Any]) -> str:
    """生成活动分享链接。"""
    base_url = str(get_settings().get("public_base_url", "") or "").strip()
    if base_url:
        return f"{base_url.rstrip('/')}/?activity_id={activity.get('activity_id', '')}"
    return f"?activity_id={activity.get('activity_id', '')}"


def build_activity_qr_bytes(link: str) -> bytes:
    """生成活动二维码图片。"""
    try:
        import qrcode
    except Exception:
        return b""
    image = qrcode.make(link)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

