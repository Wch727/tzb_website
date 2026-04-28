"""沉浸式角色系统。"""

from __future__ import annotations

from typing import Any, Dict, List

ROLE_PROFILES: List[Dict[str, Any]] = [
    {
        "role_id": "scout",
        "name": "侦察兵",
        "title": "前出探路的侦察兵",
        "tagline": "先一步抵达岔路、渡口和山口，判断前方是否安全，帮助队伍避开危险。",
        "specialty": "路线识别 / 敌情研判 / 地图纠错",
        "loadout": "任务物品：简易地图、望远镜、路线标记绳",
        "mission_focus": "重点关注路线选择、战场态势和战略转折。",
        "special_hint": "你更擅长识别地图、行军路线和战术变化。",
        "bonus_text": "地图与路线类题目答对后额外获得 2 点粮草。",
        "checklist": ["先看地形和行军方向。", "判断敌军封锁或追击可能来自哪里。", "把答案和路线变化联系起来。"],
        "starter_grain": 4,
        "starter_stars": 0,
        "recommended_nodes": ["xiangjiang_battle", "sidu_chishui", "jinshajiang_crossing"],
    },
    {
        "role_id": "medic",
        "name": "卫生员",
        "title": "随队护航的卫生员",
        "tagline": "在急行军、恶劣天气和战斗间隙守住队伍生命线，关注伤病、补给与互助。",
        "specialty": "伤员救护 / 艰苦环境 / 军民互助",
        "loadout": "任务物品：急救包、草鞋、口粮登记袋",
        "mission_focus": "重点关注军民互助、伤病员保障和艰苦奋斗精神。",
        "special_hint": "你更适合完成情境选择与艰难环境相关任务。",
        "bonus_text": "情境类题目答对后额外获得 2 点红星积分。",
        "checklist": ["先判断队伍面临的生存压力。", "关注伤病员、群众支援和补给条件。", "从人的处境中理解长征精神。"],
        "starter_grain": 6,
        "starter_stars": 0,
        "recommended_nodes": ["yudu_crossing", "snow_mountains", "grassland_crossing"],
    },
    {
        "role_id": "signal",
        "name": "通讯员",
        "title": "保障联络的通讯员",
        "tagline": "在会议、转兵和急行军之间传递命令，保证队伍在复杂局势中行动一致。",
        "specialty": "会议决策 / 命令传达 / 队伍协同",
        "loadout": "任务物品：电文袋、口令本、行军路线简表",
        "mission_focus": "重点关注会议决策、指挥体系和关键命令传递。",
        "special_hint": "你更适合完成会议节点和组织决策相关题目。",
        "bonus_text": "会议与转折类题目答对后额外获得 2 点红星积分。",
        "checklist": ["先找出本关的关键决策。", "判断命令如何影响后续路线。", "关注组织调整带来的变化。"],
        "starter_grain": 5,
        "starter_stars": 1,
        "recommended_nodes": ["tongdao_turn", "liping_meeting", "zunyi_meeting"],
    },
    {
        "role_id": "quartermaster",
        "name": "粮秣员",
        "title": "守住补给线的粮秣员",
        "tagline": "负责盘点粮草、估算行军消耗，在雪山草地和长途转移中维持队伍基本供给。",
        "specialty": "粮草调度 / 行军消耗 / 后勤保障",
        "loadout": "任务物品：粮袋、补给清册、行军里程牌",
        "mission_focus": "重点关注补给、行军距离、环境消耗和队伍持续作战能力。",
        "special_hint": "你更适合判断为什么某些路线必须快速通过，为什么某些节点考验后勤承受力。",
        "bonus_text": "艰苦环境与补给类题目答对后额外获得 2 点粮草。",
        "checklist": ["先判断这一站最大的消耗来自哪里。", "关注粮食、寒冷、渡河和行军速度。", "把战略选择和后勤压力联系起来。"],
        "starter_grain": 7,
        "starter_stars": 0,
        "recommended_nodes": ["snow_mountains", "grassland_crossing", "bangluo_meeting"],
    },
    {
        "role_id": "political",
        "name": "宣传员",
        "title": "凝聚军心的宣传员",
        "tagline": "把战斗经历、会议精神和群众工作讲清楚，帮助队伍在困难中保持信念和方向。",
        "specialty": "精神动员 / 群众工作 / 历史意义",
        "loadout": "任务物品：宣传标语、记录本、简易讲稿",
        "mission_focus": "重点关注长征精神、群众支持、理想信念和历史意义。",
        "special_hint": "你更适合回答精神专题、意义判断和故事讲述类题目。",
        "bonus_text": "精神意义类题目答对后额外获得 2 点红星积分。",
        "checklist": ["先找出本关体现的精神品质。", "关注群众支持和队伍信念。", "答题时不要只记事件，要说清为什么重要。"],
        "starter_grain": 5,
        "starter_stars": 2,
        "recommended_nodes": ["zunyi_meeting", "snow_mountains", "huining_meeting"],
    },
    {
        "role_id": "engineer",
        "name": "工兵",
        "title": "开路架桥的工兵",
        "tagline": "面对江河、桥梁、山地和险道时，负责判断通行条件，寻找突破口。",
        "specialty": "桥梁渡口 / 障碍突破 / 地形工程",
        "loadout": "任务物品：绳索、木桩、渡河工具包",
        "mission_focus": "重点关注渡河、桥梁、天险和突破通道。",
        "special_hint": "你更适合完成金沙江、大渡河、泸定桥等突破节点的题目。",
        "bonus_text": "渡河与通道类题目答对后额外获得 1 点红星积分和 1 点粮草。",
        "checklist": ["先判断关键障碍是什么。", "关注渡口、桥梁和通道控制权。", "把工程突破和战略主动联系起来。"],
        "starter_grain": 5,
        "starter_stars": 1,
        "recommended_nodes": ["jinshajiang_crossing", "dadu_river", "luding_bridge"],
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


def build_role_task(role: Dict[str, Any], node_title: str, node_stage: str, question_type: str) -> Dict[str, Any]:
    """生成角色专属任务卡。"""
    role_id = role.get("role_id", "scout")
    base = {
        "mission_title": f"{role.get('name', '侦察兵')}任务卡",
        "mission_brief": f"你正在执行“{node_title}”关卡任务，本关属于“{node_stage}”阶段。",
        "checklist": [],
        "reward_hint": role.get("bonus_text", ""),
    }
    custom_checklist = role.get("checklist", [])
    if custom_checklist:
        base["checklist"] = [
            *custom_checklist[:2],
            f"本关题型为“{question_type}”，请按“{role.get('specialty', '历史线索')}”方向判断。",
        ]
        return base
    if role_id == "scout":
        base["checklist"] = [
            "先判断路线节点与战略转折之间的关系。",
            "关注地形、机动与敌我态势变化。",
            f"本关题型为“{question_type}”，优先从战术线索中作答。",
        ]
    elif role_id == "medic":
        base["checklist"] = [
            "先理解红军在极端环境中的保障压力。",
            "关注军民互助、伤员转运与艰苦环境。",
            f"本关题型为“{question_type}”，优先从人物处境和生存条件中判断。",
        ]
    else:
        base["checklist"] = [
            "先梳理会议、命令与队伍协同关系。",
            "关注关键决策如何改变后续路线与战局。",
            f"本关题型为“{question_type}”，优先从组织和指挥链条中作答。",
        ]
    return base


def build_role_feedback(role: Dict[str, Any], correct: bool, question_type: str) -> str:
    """生成角色专属点评。"""
    role_name = role.get("name", "侦察兵")
    if correct:
        return (
            f"{role_name}本关判断准确。你不仅完成了“{question_type}”题目，"
            "也把角色职责和长征历史线索结合起来了。"
        )
    return (
        f"{role_name}本关还有提升空间。建议回到角色任务卡，重新对照本关的"
        f"“{question_type}”线索与历史背景，再复盘一次。"
    )
