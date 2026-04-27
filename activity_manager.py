"""活动中心与分享能力。"""

from __future__ import annotations

import io
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from utils import RUNTIME_DIR, get_settings, read_json, write_json

ACTIVITY_PATH = RUNTIME_DIR / "activities.json"

DEFAULT_ACTIVITY_TEMPLATES: List[Dict[str, Any]] = [
    {
        "activity_id": "knowledge-contest",
        "name": "长征精神知识竞赛",
        "description": "面向课堂、党史学习日和主题竞赛的标准化活动模板，强调主线剧情、角色扮演和积分排行。",
        "mode": "知识竞赛",
        "time_range": "长期开放",
        "node_scope": [
            "ruijin_departure",
            "xiangjiang_battle",
            "zunyi_meeting",
            "sidu_chishui",
            "jinshajiang_crossing",
            "luding_bridge",
            "grassland_crossing",
            "huining_meeting",
        ],
        "status": "进行中",
        "created_by": "system",
        "support_team_mode": True,
        "support_branch_pk": True,
        "max_team_size": 6,
    },
    {
        "activity_id": "party-study-day",
        "name": "党史学习日",
        "description": "聚焦转折节点、长征精神与理论学习的专题活动模板，适合支部学习与班级联学。",
        "mode": "党史学习日",
        "time_range": "90分钟",
        "node_scope": [
            "tongdao_turn",
            "liping_meeting",
            "houchang_meeting",
            "zunyi_meeting",
            "bangluo_meeting",
            "wuqi_meeting",
        ],
        "status": "进行中",
        "created_by": "system",
        "support_team_mode": True,
        "support_branch_pk": True,
        "max_team_size": 8,
    },
    {
        "activity_id": "study-tour-task",
        "name": "红色研学任务",
        "description": "适合景区、纪念馆与研学团队使用的沉浸式路线任务，支持小队协作完成节点挑战。",
        "mode": "研学任务",
        "time_range": "120分钟",
        "node_scope": [
            "ruijin_departure",
            "yudu_crossing",
            "xiangjiang_battle",
            "luding_bridge",
            "snow_mountains",
            "grassland_crossing",
            "wuqi_meeting",
        ],
        "status": "进行中",
        "created_by": "system",
        "support_team_mode": True,
        "support_branch_pk": False,
        "max_team_size": 5,
    },
]


def _load_activities() -> List[Dict[str, Any]]:
    """读取活动列表。"""
    rows = read_json(ACTIVITY_PATH, []) or []
    if not rows:
        write_json(ACTIVITY_PATH, DEFAULT_ACTIVITY_TEMPLATES)
        return [item.copy() for item in DEFAULT_ACTIVITY_TEMPLATES]
    normalized: List[Dict[str, Any]] = []
    for item in rows:
        normalized.append(
            {
                "activity_id": str(item.get("activity_id", "") or f"act-{secrets.token_hex(4)}"),
                "name": str(item.get("name", "未命名活动") or "未命名活动"),
                "description": str(item.get("description", "") or ""),
                "mode": str(item.get("mode", "知识竞赛") or "知识竞赛"),
                "time_range": str(item.get("time_range", "60分钟") or "60分钟"),
                "node_scope": list(item.get("node_scope", []) or []),
                "status": str(item.get("status", "进行中") or "进行中"),
                "created_by": str(item.get("created_by", "admin") or "admin"),
                "created_at": str(item.get("created_at", "") or ""),
                "support_team_mode": bool(item.get("support_team_mode", True)),
                "support_branch_pk": bool(item.get("support_branch_pk", True)),
                "max_team_size": int(item.get("max_team_size", 6) or 6),
            }
        )
    return normalized


def _save_activities(rows: List[Dict[str, Any]]) -> None:
    """保存活动列表。"""
    write_json(ACTIVITY_PATH, rows)


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
    support_team_mode: bool = True,
    support_branch_pk: bool = True,
    max_team_size: int = 6,
) -> Dict[str, Any]:
    """创建活动。"""
    rows = _load_activities()
    activity = {
        "activity_id": f"act-{secrets.token_hex(4)}",
        "name": str(name or "").strip() or "未命名活动",
        "description": str(description or "").strip(),
        "mode": str(mode or "").strip() or "知识竞赛",
        "time_range": str(time_range or "").strip() or "60分钟",
        "node_scope": [item for item in node_scope if item],
        "status": "进行中",
        "created_by": created_by,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "support_team_mode": bool(support_team_mode),
        "support_branch_pk": bool(support_branch_pk),
        "max_team_size": max(2, min(int(max_team_size or 6), 20)),
    }
    rows.append(activity)
    _save_activities(rows)
    return activity


def update_activity(activity_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新活动。"""
    rows = _load_activities()
    updated: Dict[str, Any] = {}
    for index, item in enumerate(rows):
        if item.get("activity_id") != activity_id:
            continue
        row = item.copy()
        for key, value in patch.items():
            if value is None:
                continue
            row[key] = value
        row["max_team_size"] = max(2, min(int(row.get("max_team_size", 6) or 6), 20))
        rows[index] = row
        updated = row
        break
    if updated:
        _save_activities(rows)
    return updated


def _public_base_url() -> str:
    """读取公开访问根地址，避免二维码只有相对路径。"""
    base_url = str(os.getenv("PUBLIC_BASE_URL") or get_settings().get("public_base_url", "") or "").strip()
    if not base_url:
        return ""
    parsed = urlsplit(base_url)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")
    return base_url.rstrip("/")


def build_activity_share_link(activity: Dict[str, Any], team_id: str = "") -> str:
    """生成可扫码访问的活动或小队分享链接。"""
    params = {"activity_id": activity.get("activity_id", "")}
    if team_id:
        params["team_id"] = team_id
    query = urlencode({key: value for key, value in params.items() if value})
    base_url = _public_base_url()
    page_path = f"/{quote('活动中心')}"
    if base_url:
        return f"{base_url}{page_path}?{query}"
    return f"{page_path}?{query}"


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
