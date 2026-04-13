"""沉浸式角色系统。"""

from __future__ import annotations

from typing import Any, Dict, List

ROLE_PROFILES: List[Dict[str, Any]] = [
    {
        "role_id": "scout",
        "name": "侦察兵",
        "title": "前出探路的侦察兵",
        "tagline": "擅长路线判断、地形识别和敌情研判。",
        "mission_focus": "重点关注路线选择、战场态势和战略转折。",
        "special_hint": "你更擅长识别地图、行军路线和战术变化。",
        "bonus_text": "地图与路线类题目答对后额外获得 2 点粮草。",
        "starter_grain": 4,
        "starter_stars": 0,
        "recommended_nodes": ["xiangjiang_battle", "sidu_chishui", "jinshajiang_crossing"],
    },
    {
        "role_id": "medic",
        "name": "卫生员",
        "title": "随队护航的卫生员",
        "tagline": "擅长保障、救护和艰苦环境中的坚持。",
        "mission_focus": "重点关注军民互助、伤病员保障和艰苦奋斗精神。",
        "special_hint": "你更适合完成情境选择与艰难环境相关任务。",
        "bonus_text": "情境类题目答对后额外获得 2 点红星积分。",
        "starter_grain": 6,
        "starter_stars": 0,
        "recommended_nodes": ["yudu_crossing", "snow_mountains", "grassland_crossing"],
    },
    {
        "role_id": "signal",
        "name": "通讯员",
        "title": "保障联络的通讯员",
        "tagline": "擅长会议节点、指挥衔接和信息传达。",
        "mission_focus": "重点关注会议决策、指挥体系和关键命令传递。",
        "special_hint": "你更适合完成会议节点和组织决策相关题目。",
        "bonus_text": "会议与转折类题目答对后额外获得 2 点红星积分。",
        "starter_grain": 5,
        "starter_stars": 1,
        "recommended_nodes": ["tongdao_turn", "liping_meeting", "zunyi_meeting"],
    },
]


def list_roles() -> List[Dict[str, Any]]:
    """返回全部角色。"""
    return [item.copy() for item in ROLE_PROFILES]


def get_role(role_id: str = "") -> Dict[str, Any]:
    """按角色 id 获取角色信息。"""
    normalized = str(role_id or "").strip().lower()
    for item in ROLE_PROFILES:
        if item["role_id"] == normalized or item["name"] == role_id:
            return item.copy()
    return ROLE_PROFILES[0].copy()


def get_role_names() -> List[str]:
    """返回角色名称列表。"""
    return [item["name"] for item in ROLE_PROFILES]


def role_id_by_name(role_name: str) -> str:
    """通过角色名称获取 id。"""
    for item in ROLE_PROFILES:
        if item["name"] == role_name:
            return item["role_id"]
    return ROLE_PROFILES[0]["role_id"]


def build_role_brief(role: Dict[str, Any], node_title: str, node_stage: str) -> str:
    """生成角色任务提示。"""
    return (
        f"当前身份：{role.get('name', '侦察兵')}。"
        f"你正在进入“{node_title}”关卡，本关位于“{node_stage}”阶段。"
        f"{role.get('mission_focus', '')}"
        f"{role.get('special_hint', '')}"
    )

