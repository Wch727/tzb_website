"""长征史轻量闯关与节点数据模块。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from content_store import (
    build_static_sources_for_node,
    get_related_nodes,
    get_route_node_data,
    load_route_nodes_data,
)
from generator import generate_learning_summary
from llm import get_llm_client
from prompts import LONG_MARCH_GUIDE_ROLE_PROMPT, build_route_explain_prompt
from rag import retrieve_knowledge
from utils import DATA_DIR, normalize_answer


def load_route_nodes() -> List[Dict[str, Any]]:
    """读取富内容路线节点。"""
    return [item.copy() for item in load_route_nodes_data()]


def get_route_node(node_id: str) -> Optional[Dict[str, Any]]:
    """按 id 查询节点。"""
    node = get_route_node_data(node_id)
    return node.copy() if node else None


def get_next_route_node(node_id: str) -> Optional[Dict[str, Any]]:
    """获取下一节点。"""
    nodes = load_route_nodes()
    for index, node in enumerate(nodes):
        if node.get("id") == node_id:
            if index + 1 < len(nodes):
                return nodes[index + 1]
            return None
    return nodes[0] if nodes else None


def _static_node_explanation(node: Dict[str, Any], role: str) -> str:
    """在无 LLM 模式下，为节点生成完整讲解摘要。"""
    key_points = node.get("key_points", []) or []
    key_text = "；".join(f"{index + 1}. {item}" for index, item in enumerate(key_points[:4]))
    audience_line = {
        "大学生": "建议你重点把握历史逻辑、路线调整与战略转折之间的关系。",
        "研学团成员": "建议你把这一路段理解为长征主线中的关键展项，关注军民关系与组织决策。",
        "普通参观者": "可以把这一节点理解为长征途中一次具有代表性的重大经历与历史转折。",
    }.get(role, "建议结合时间、地点、人物和意义来理解这一节点。")
    sections = [
        f"【节点摘要】{node.get('summary', '')}",
        f"【历史背景】{node.get('background', '')}",
        f"【事件经过】{node.get('process', '')}",
        f"【历史意义】{node.get('significance', '')}",
    ]
    if key_text:
        sections.append(f"【关键知识点】{key_text}")
    if node.get("figures"):
        sections.append(f"【相关人物】{'、'.join(node.get('figures', []))}")
    sections.append(f"【学习提示】{audience_line}")
    return "\n\n".join(section for section in sections if section.strip())


def _prefer_complete_explanation(generated: str, fallback: str, min_chars: int = 420) -> str:
    """保证节点讲解不会过短。"""
    cleaned = str(generated or "").strip()
    if not cleaned or len(cleaned) < min_chars:
        return fallback
    return cleaned


def fallback_quiz_explanation(node_data: Dict[str, Any]) -> Dict[str, str]:
    """在静态模式下输出完整答题解析。"""
    quiz = node_data.get("quiz", {}) or {}
    explanation = quiz.get("explanation", "").strip()
    if not explanation:
        explanation = (
            f"{node_data.get('title', '该节点')}之所以重要，不仅因为其发生在"
            f"{node_data.get('date', '长征途中')}的关键阶段，更因为它直接影响了红军后续的行军方向、"
            "战略判断与革命力量的保存。理解这一题，不能只记住表面的结论，更要把节点的背景、过程与历史意义联系起来。"
        )
    if len(explanation) < 150:
        explanation = (
            f"{explanation} 从历史背景看，{node_data.get('background', '') or node_data.get('summary', '')}"
            f" 从事件经过看，{node_data.get('process', '') or '红军在复杂形势下完成了关键行动。'}"
            f" 从历史意义看，{node_data.get('significance', '') or '这一节点推动了长征主线继续向前发展。'}"
        )
    extended_note = quiz.get("extended_note", "").strip()
    if not extended_note:
        key_points = node_data.get("key_points", []) or []
        extended_note = (
            "延伸来看，这一节点既是路线推进中的一段经历，也是长征精神形成的重要场景。"
            f"{' 可继续关注：' + '；'.join(key_points[:3]) if key_points else ''}"
        )
    if len(extended_note) < 90:
        extended_note = (
            f"{extended_note} 继续阅读时，可把这一节点与{'、'.join(node_data.get('figures', [])[:3]) or '相关人物'}"
            "以及前后相邻节点放在一起理解，这样更容易把握它在整条长征主线中的位置。"
        )
    return {
        "expected_answer": quiz.get("answer", ""),
        "explanation": explanation,
        "extended_note": extended_note,
    }


def start_game(role: str, provider_config: Dict[str, Any]) -> Dict[str, Any]:
    """初始化闯关状态机。"""
    _ = provider_config
    nodes = load_route_nodes()
    return {
        "phase": "explore",
        "role": role,
        "score": 0,
        "visited_nodes": [],
        "unlocked_nodes": [],
        "available_nodes": [
            {
                "id": node["id"],
                "route_stage": node["route_stage"],
                "title": node["title"],
                "place": node["place"],
                "date": node.get("date", ""),
                "summary": node.get("summary", ""),
                "image": node.get("image", ""),
                "score": node["score"],
            }
            for node in nodes
        ],
        "current_stage": nodes[0]["id"] if nodes else "",
    }


def build_question_options(node: Dict[str, Any]) -> List[str]:
    """优先使用节点内置选项。"""
    quiz = node.get("quiz", {})
    options = quiz.get("options", []) or []
    if options:
        return options
    answer = quiz.get("answer", "")
    return [answer] if answer else []


def generate_node_explanation(
    node_id: str,
    role: str,
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """生成路线节点讲解内容。"""
    node = get_route_node(node_id)
    if not node:
        return {
            "node": {},
            "explanation": "未找到对应的路线节点。",
            "question": "",
            "answer": "",
            "options": [],
            "sources": [],
        }

    retrieval = retrieve_knowledge(
        question=node["title"],
        filters={"route_stage": node.get("route_stage", node["title"])},
        top_k=4,
    )
    hits = retrieval["hits"]
    context_blocks = [
        f"标题：{item['metadata'].get('title', '')}\n内容：{item['text']}" for item in hits
    ]
    prompt = build_route_explain_prompt(node_title=node["title"], role=role, context="\n\n".join(context_blocks))
    static_mode = bool(provider_config.get("static_mode"))
    result: Dict[str, Any] = {}
    if not static_mode:
        client = get_llm_client(provider_config)
        result = client.generate_with_context(
            prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
            context_blocks=context_blocks,
            temperature=0.3,
        )
    quiz = node.get("quiz", {})
    next_node = get_next_route_node(node.get("id", ""))
    explanation_text = result.get("content", "").strip()
    use_static = static_mode or not explanation_text or result.get("fallback_used", False) or result.get("provider") == "mock"
    static_explanation = _static_node_explanation(node, role=role)
    explanation_text = _prefer_complete_explanation("" if use_static else explanation_text, static_explanation, min_chars=420)
    static_details = fallback_quiz_explanation(node)
    sources = [
        {
            "source_file": item["metadata"].get("source_file", "未知文件"),
            "title": item["metadata"].get("title", "未命名"),
            "type": item["metadata"].get("type", "未知"),
            "snippet": item.get("text", "")[:200],
        }
        for item in hits
    ]
    if not sources:
        sources = build_static_sources_for_node(node)
    else:
        sources = build_static_sources_for_node(node)[:1] + sources
    return {
        "node": node,
        "explanation": explanation_text,
        "warning": result.get("warning", ""),
        "fallback_used": bool(use_static and not static_mode),
        "mode_label": "知识导览模式" if use_static else "智能讲解增强",
        "question": quiz.get("question", ""),
        "expected_answer": quiz.get("answer", ""),
        "options": build_question_options(node),
        "score": node.get("score", 10),
        "feedback_title": node.get("title", ""),
        "background": node.get("background", ""),
        "process": node.get("process", ""),
        "significance": node.get("significance", ""),
        "summary": node.get("summary", ""),
        "figures": node.get("figures", []),
        "date": node.get("date", ""),
        "place": node.get("place", ""),
        "image": node.get("image", ""),
        "avatar": node.get("avatar", "assets/avatar/guide_digital_host.png"),
        "quiz_explanation": static_details.get("explanation", ""),
        "extended_note": static_details.get("extended_note", ""),
        "key_points": node.get("key_points", []),
        "next_node": next_node,
        "related_nodes": get_related_nodes(node),
        "sources": sources,
    }


def _is_correct(user_answer: str, expected_answer: str) -> bool:
    """闯关答案的简化判断。"""
    normalized_user = normalize_answer(user_answer)
    expected_parts = [normalize_answer(part) for part in str(expected_answer).replace("、", "/").split("/")]
    return any(part and (part in normalized_user or normalized_user in part) for part in expected_parts)


def submit_choice(
    current_state: Dict[str, Any],
    node_id: str,
    answer: str,
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """处理闯关作答。"""
    node = get_route_node(node_id)
    if not node:
        return {
            "state": current_state,
            "feedback": "未找到对应节点。",
            "correct": False,
            "finished": False,
        }

    state = current_state.copy()
    state.setdefault("visited_nodes", [])
    state.setdefault("unlocked_nodes", [])
    state.setdefault("score", 0)

    if node_id not in state["visited_nodes"]:
        state["visited_nodes"].append(node_id)

    expected_answer = node.get("quiz", {}).get("answer", "")
    correct = _is_correct(answer, expected_answer)
    if correct and node_id not in state["unlocked_nodes"]:
        state["unlocked_nodes"].append(node_id)
        state["score"] += int(node.get("score", 10))

    all_nodes = [item["id"] for item in load_route_nodes()]
    finished = len(state["unlocked_nodes"]) >= len(all_nodes)
    state["phase"] = "summary" if finished else "explore"

    next_node = get_next_route_node(node_id)
    quiz_detail = fallback_quiz_explanation(node)
    feedback = (
        f"回答正确，获得 {node.get('score', 10)} 分。"
        if correct
        else "本次回答未命中全部要点，但你已经完成了这一展项的学习。"
    )

    summary = None
    if finished:
        summary = generate_learning_summary(
            role=state.get("role", "大学生"),
            score=int(state.get("score", 0)),
            unlocked_nodes=[get_route_node(item).get("title", item) for item in state.get("unlocked_nodes", [])],
            provider_config=provider_config,
        )

    return {
        "state": state,
        "feedback": feedback,
        "correct": correct,
        "finished": finished,
        "summary": summary,
        "answer_detail": {
            "expected_answer": quiz_detail.get("expected_answer", expected_answer),
            "explanation": quiz_detail.get("explanation", ""),
            "extended_note": quiz_detail.get("extended_note", ""),
            "next_node": next_node,
        },
    }
