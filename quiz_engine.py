"""剧情关卡与多媒体答题引擎。"""

from __future__ import annotations

from typing import Any, Dict, List

from activity_manager import get_activity
from content_store import get_route_node_data, load_route_nodes_data
from knowledge_cards import build_related_knowledge_bundle
from progression import build_progress_summary, default_progress, record_quiz_result
from role_system import build_role_brief, build_role_feedback, build_role_task, get_role

QUESTION_TYPE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "ruijin_departure": {
        "question_type": "情境选择题",
        "mission_prompt": "你刚从中央苏区整装出发，必须在复杂局势中作出正确判断。",
        "material_title": "出发前情境导入",
        "material_points": ["中央红军即将离开中央苏区，战略转移迫在眉睫。", "你需要理解“为什么出发”而不是只记住“从哪里出发”。"],
    },
    "xiangjiang_battle": {
        "question_type": "看图识史",
        "mission_prompt": "请结合眼前图片和背景判断，这场战役为什么会成为长征初期的重大转折前奏。",
        "material_title": "图像观察要点",
        "material_points": ["注意战役环境与红军处境的艰险程度。", "思考巨大牺牲为何促使后续路线与决策发生变化。"],
    },
    "sidu_chishui": {
        "question_type": "地图纠错",
        "mission_prompt": "请结合路线图判断，红军应如何通过机动调动摆脱围追堵截。",
        "material_title": "地图纠错线索",
        "material_points": ["先看路线是否符合“机动灵活、避实击虚”的特点。", "错误路线通常会让红军陷入被围堵或暴露主力方向。"],
    },
    "luding_bridge": {
        "question_type": "看图识史",
        "mission_prompt": "请结合桥梁场景和战略位置，判断其历史价值。",
        "material_title": "场景观察要点",
        "material_points": ["关注桥梁本身的险要程度与渡河难度。", "思考为什么控制桥梁会影响整支队伍的生死与行军节奏。"],
    },
    "snow_mountains": {
        "question_type": "听音辨曲",
        "mission_prompt": "请先播放音频线索，再判断它体现的是哪一类长征精神。",
        "material_title": "音频线索解读",
        "material_points": ["先听关键诗句，再把它与雪山环境联系起来。", "注意“乐观主义”与“艰苦奋斗”这两个关键词。"],
        "audio_text": "红军不怕远征难，万水千山只等闲。更喜岷山千里雪，三军过后尽开颜。",
        "custom_question": "请先播放音频线索。这段诗句最能帮助理解长征中的哪一核心精神？",
        "custom_options": [
            "A. 艰苦奋斗、革命乐观主义",
            "B. 城市工业化建设",
            "C. 海上贸易精神",
            "D. 外交谈判艺术",
        ],
        "custom_answer": "A. 艰苦奋斗、革命乐观主义",
        "custom_explanation": "诗句集中表现了红军面对雪山等极端环境时的革命乐观主义和艰苦奋斗精神，因此最适合作为“翻越雪山”节点的音频线索。",
    },
}


def _node_ids_for_activity(activity_id: str = "") -> List[str]:
    """获取活动对应的节点范围。"""
    if activity_id:
        activity = get_activity(activity_id)
        if activity.get("node_scope"):
            return [item for item in activity.get("node_scope", []) if get_route_node_data(item)]
    return [item.get("id", "") for item in load_route_nodes_data()]


def create_story_state(role_id: str, activity_id: str = "", start_node_id: str = "") -> Dict[str, Any]:
    """创建主线剧情状态。"""
    role = get_role(role_id)
    node_ids = _node_ids_for_activity(activity_id)
    if start_node_id and start_node_id in node_ids:
        current_index = node_ids.index(start_node_id)
    else:
        current_index = 0
    activity = get_activity(activity_id) if activity_id else {}
    return {
        "role_id": role["role_id"],
        "role_name": role["name"],
        "activity_id": activity_id or "global",
        "activity_name": activity.get("name", "长征主线闯关"),
        "node_ids": node_ids,
        "current_index": current_index,
        "history": [],
        "progress": default_progress(
            role_name=role["name"],
            starter_grain=int(role.get("starter_grain", 5)),
            starter_stars=int(role.get("starter_stars", 0)),
        ),
        "finished": False,
    }


def set_story_checkpoint(state: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """将剧情跳转到指定节点。"""
    updated = state.copy()
    node_ids = updated.get("node_ids", [])
    if node_id in node_ids:
        updated["current_index"] = node_ids.index(node_id)
    return updated


def get_current_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取当前节点。"""
    node_ids = state.get("node_ids", [])
    if not node_ids:
        return {}
    current_index = min(max(int(state.get("current_index", 0)), 0), len(node_ids) - 1)
    return get_route_node_data(node_ids[current_index]) or {}


def _question_payload(node: Dict[str, Any]) -> Dict[str, Any]:
    """生成题目载荷。"""
    payload = QUESTION_TYPE_OVERRIDES.get(node.get("id", ""), {}).copy()
    quiz = node.get("quiz", {}) or {}
    payload.setdefault("question_type", "情境选择题")
    payload.setdefault("custom_question", quiz.get("question", ""))
    payload.setdefault("custom_options", quiz.get("options", []))
    payload.setdefault("custom_answer", quiz.get("answer", ""))
    payload.setdefault("custom_explanation", quiz.get("explanation", ""))
    return payload


def get_stage_package(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取当前关卡的完整展示数据。"""
    node = get_current_node(state)
    if not node:
        return {"node": {}, "finished": True}
    role = get_role(state.get("role_id", "scout"))
    payload = _question_payload(node)
    knowledge_cards = build_related_knowledge_bundle(node)
    return {
        "node": node,
        "role": role,
        "activity_id": state.get("activity_id", "global"),
        "activity_name": state.get("activity_name", "长征主线闯关"),
        "question_type": payload.get("question_type", "情境选择题"),
        "mission_prompt": payload.get("mission_prompt", ""),
        "role_brief": build_role_brief(role, node.get("title", ""), node.get("route_stage", "")),
        "role_task": build_role_task(role, node.get("title", ""), node.get("route_stage", ""), payload.get("question_type", "情境选择题")),
        "question": payload.get("custom_question") or node.get("quiz", {}).get("question", ""),
        "options": payload.get("custom_options") or node.get("quiz", {}).get("options", []),
        "expected_answer": payload.get("custom_answer") or node.get("quiz", {}).get("answer", ""),
        "explanation": payload.get("custom_explanation") or node.get("quiz", {}).get("explanation", ""),
        "extended_note": node.get("quiz", {}).get("extended_note", ""),
        "audio_text": payload.get("audio_text", ""),
        "material_title": payload.get("material_title", ""),
        "material_points": payload.get("material_points", []),
        "knowledge_cards": knowledge_cards,
        "progress": build_progress_summary(state.get("progress", {})),
        "current_step": int(state.get("current_index", 0)) + 1,
        "total_steps": len(state.get("node_ids", [])),
    }


def submit_stage_answer(state: Dict[str, Any], answer: str) -> Dict[str, Any]:
    """提交当前关卡答案。"""
    node = get_current_node(state)
    if not node:
        return {"state": state, "finished": True}

    stage = get_stage_package(state)
    expected_answer = str(stage.get("expected_answer", "") or "")
    correct = answer.strip() == expected_answer.strip()
    role = stage.get("role", {})
    question_type = stage.get("question_type", "情境选择题")
    bonus_stars = 0
    bonus_grain = 0
    if correct:
        if question_type == "地图纠错" and role.get("role_id") == "scout":
            bonus_grain += 2
        if question_type == "情境选择题" and role.get("role_id") == "medic":
            bonus_stars += 2
        if node.get("type") == "event" and role.get("role_id") == "signal":
            bonus_stars += 2
    role_mastery_key = ""
    if correct:
        if role.get("role_id") == "scout" and question_type in ["地图纠错", "看图识史"]:
            role_mastery_key = "scout"
        elif role.get("role_id") == "medic" and question_type in ["情境选择题", "听音辨曲"]:
            role_mastery_key = "medic"
        elif role.get("role_id") == "signal" and node.get("type") == "event":
            role_mastery_key = "signal"

    updated_state = state.copy()
    updated_state["history"] = list(state.get("history", []))
    updated_state["history"].append(
        {
            "node_id": node.get("id", ""),
            "title": node.get("title", ""),
            "question_type": question_type,
            "correct": correct,
            "selected_answer": answer,
        }
    )
    updated_state["progress"] = record_quiz_result(
        state.get("progress", {}),
        node_id=node.get("id", ""),
        node_title=node.get("title", ""),
        question=stage.get("question", ""),
        selected_answer=answer,
        expected_answer=expected_answer,
        explanation=stage.get("explanation", ""),
        correct=correct,
        question_type=question_type,
        bonus_stars=bonus_stars,
        bonus_grain=bonus_grain,
        role_mastery_key=role_mastery_key,
    )

    updated_state["current_index"] = int(state.get("current_index", 0)) + 1
    updated_state["finished"] = updated_state["current_index"] >= len(updated_state.get("node_ids", []))
    next_node = get_current_node(updated_state) if not updated_state["finished"] else {}
    return {
        "state": updated_state,
        "correct": correct,
        "feedback": "回答正确，已推进到下一关。" if correct else "本题未答对，已收录到错题复盘。",
        "answered_node": node,
        "next_node": next_node,
        "finished": updated_state["finished"],
        "role_feedback": build_role_feedback(role, correct, question_type),
        "answer_detail": {
            "expected_answer": expected_answer,
            "explanation": stage.get("explanation", ""),
            "extended_note": stage.get("extended_note", ""),
            "question_type": question_type,
        },
        "knowledge_cards": stage.get("knowledge_cards", []),
        "progress": build_progress_summary(updated_state.get("progress", {})),
    }
