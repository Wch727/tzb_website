"""长征史轻量闯关与节点数据模块。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from generator import generate_learning_summary
from llm import get_llm_client
from prompts import LONG_MARCH_GUIDE_ROLE_PROMPT, build_route_explain_prompt
from rag import retrieve_knowledge
from utils import DATA_DIR, normalize_answer

ROUTE_NODES_FILE = DATA_DIR / "route_nodes.json"
ROUTES_FILE = DATA_DIR / "routes.csv"


def load_route_nodes() -> List[Dict[str, Any]]:
    """读取富内容路线节点。"""
    if ROUTE_NODES_FILE.exists():
        content = json.loads(ROUTE_NODES_FILE.read_text(encoding="utf-8"))
        nodes: List[Dict[str, Any]] = []
        for index, row in enumerate(content):
            item = row.copy()
            item["score"] = int(item.get("score", 10))
            item["order"] = index + 1
            item.setdefault("route_stage", item.get("title", f"节点 {index + 1}"))
            item.setdefault("summary", "")
            item.setdefault("quiz", {})
            item.setdefault("figures", [])
            item.setdefault("avatar", "assets/avatar/guide.svg")
            nodes.append(item)
        return nodes

    nodes: List[Dict[str, Any]] = []
    with Path(ROUTES_FILE).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            nodes.append(
                {
                    "id": row.get("route_stage", f"node-{index + 1}"),
                    "title": row.get("title", ""),
                    "type": row.get("type", "route"),
                    "date": "",
                    "place": row.get("place", ""),
                    "summary": row.get("summary", ""),
                    "background": row.get("summary", ""),
                    "process": row.get("summary", ""),
                    "significance": row.get("summary", ""),
                    "figures": [],
                    "image": "",
                    "audio": "",
                    "avatar": "assets/avatar/guide.svg",
                    "route_stage": row.get("route_stage", ""),
                    "score": int(row.get("score", 10)),
                    "order": index + 1,
                    "quiz": {
                        "question": row.get("question", ""),
                        "options": [],
                        "answer": row.get("answer", ""),
                        "explanation": row.get("summary", ""),
                        "extended_note": "",
                    },
                }
            )
    return nodes


def get_route_node(node_id: str) -> Optional[Dict[str, Any]]:
    """按 id 查询节点。"""
    for node in load_route_nodes():
        if node.get("id") == node_id or node.get("route_stage") == node_id or node.get("title") == node_id:
            return node
    return None


def get_next_route_node(node_id: str) -> Optional[Dict[str, Any]]:
    """获取下一节点。"""
    nodes = load_route_nodes()
    for index, node in enumerate(nodes):
        if node.get("id") == node_id:
            if index + 1 < len(nodes):
                return nodes[index + 1]
            return None
    return nodes[0] if nodes else None


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
    client = get_llm_client(provider_config)
    result = client.generate_with_context(
        prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
        context_blocks=context_blocks,
        temperature=0.3,
    )
    quiz = node.get("quiz", {})
    next_node = get_next_route_node(node.get("id", ""))
    return {
        "node": node,
        "explanation": result.get("content", ""),
        "warning": result.get("warning", ""),
        "fallback_used": result.get("fallback_used", False),
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
        "avatar": node.get("avatar", "assets/avatar/guide.svg"),
        "quiz_explanation": quiz.get("explanation", ""),
        "extended_note": quiz.get("extended_note", ""),
        "next_node": next_node,
        "sources": [
            {
                "source_file": item["metadata"].get("source_file", "未知文件"),
                "title": item["metadata"].get("title", "未命名"),
                "type": item["metadata"].get("type", "未知"),
                "snippet": item.get("text", "")[:200],
            }
            for item in hits
        ],
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
    quiz = node.get("quiz", {})
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
            "expected_answer": expected_answer,
            "explanation": quiz.get("explanation", ""),
            "extended_note": quiz.get("extended_note", ""),
            "next_node": next_node,
        },
    }
