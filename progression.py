"""成长激励与错题复盘。"""

from __future__ import annotations

from typing import Any, Dict, List

RANK_THRESHOLDS = [
    (0, "红军新兵"),
    (30, "红军班长"),
    (70, "红军排长"),
    (120, "红军连长"),
    (180, "红军营长"),
    (260, "红军团长"),
    (360, "红军师长"),
    (480, "红军军团长"),
]


def default_progress(role_name: str = "侦察兵", starter_grain: int = 5, starter_stars: int = 0) -> Dict[str, Any]:
    """创建默认成长档案。"""
    return {
        "role_name": role_name,
        "red_star_points": starter_stars,
        "grain": starter_grain,
        "correct_count": 0,
        "wrong_count": 0,
        "answered_count": 0,
        "multimedia_types": [],
        "medals": [],
        "wrong_book": [],
        "completed_nodes": [],
        "last_certificate_svg": "",
        "role_mastery_counts": {},
        "streak": 0,
        "best_streak": 0,
        "tactic_success_count": 0,
    }


def get_rank_title(points: int) -> str:
    """根据积分计算军衔。"""
    title = RANK_THRESHOLDS[0][1]
    for threshold, name in RANK_THRESHOLDS:
        if points >= threshold:
            title = name
    return title


def _append_unique(items: List[str], value: str) -> List[str]:
    """向列表中追加唯一值。"""
    if value and value not in items:
        items.append(value)
    return items


def _refresh_medals(progress: Dict[str, Any]) -> None:
    """根据当前状态刷新勋章。"""
    medals: List[str] = list(progress.get("medals", []))
    if progress.get("correct_count", 0) >= 1:
        _append_unique(medals, "初上征程")
    if len(progress.get("completed_nodes", [])) >= 5:
        _append_unique(medals, "转折追光者")
    if len(progress.get("completed_nodes", [])) >= 10:
        _append_unique(medals, "重走长征路")
    if len(set(progress.get("multimedia_types", []))) >= 3:
        _append_unique(medals, "多媒体闯关先锋")
    if progress.get("red_star_points", 0) >= 180:
        _append_unique(medals, "红星进阶者")
    role_counts = progress.get("role_mastery_counts", {}) or {}
    if int(role_counts.get("scout", 0)) >= 2:
        _append_unique(medals, "战地侦察能手")
    if int(role_counts.get("medic", 0)) >= 2:
        _append_unique(medals, "雪线守护者")
    if int(role_counts.get("signal", 0)) >= 2:
        _append_unique(medals, "前线通讯尖兵")
    if int(progress.get("best_streak", 0)) >= 3:
        _append_unique(medals, "连续作战尖兵")
    if int(progress.get("tactic_success_count", 0)) >= 5:
        _append_unique(medals, "战术判断能手")
    progress["medals"] = medals


def record_quiz_result(
    progress: Dict[str, Any],
    *,
    node_id: str,
    node_title: str,
    question: str,
    selected_answer: str,
    expected_answer: str,
    explanation: str,
    correct: bool,
    question_type: str,
    bonus_stars: int = 0,
    bonus_grain: int = 0,
    role_mastery_key: str = "",
    tactic_match: bool = False,
) -> Dict[str, Any]:
    """记录一次答题结果。"""
    updated = progress.copy()
    updated.setdefault("multimedia_types", [])
    updated.setdefault("medals", [])
    updated.setdefault("wrong_book", [])
    updated.setdefault("completed_nodes", [])
    updated.setdefault("role_mastery_counts", {})
    updated.setdefault("streak", 0)
    updated.setdefault("best_streak", 0)
    updated.setdefault("tactic_success_count", 0)
    updated["answered_count"] = int(updated.get("answered_count", 0)) + 1
    _append_unique(updated["multimedia_types"], question_type)

    if correct:
        updated["correct_count"] = int(updated.get("correct_count", 0)) + 1
        updated["red_star_points"] = int(updated.get("red_star_points", 0)) + 10 + int(bonus_stars)
        updated["grain"] = int(updated.get("grain", 0)) + 3 + int(bonus_grain)
        updated["streak"] = int(updated.get("streak", 0)) + 1
        updated["best_streak"] = max(int(updated.get("best_streak", 0)), int(updated.get("streak", 0)))
        _append_unique(updated["completed_nodes"], node_id)
        if role_mastery_key:
            mastery = dict(updated.get("role_mastery_counts", {}) or {})
            mastery[role_mastery_key] = int(mastery.get(role_mastery_key, 0)) + 1
            updated["role_mastery_counts"] = mastery
        if tactic_match:
            updated["red_star_points"] = int(updated.get("red_star_points", 0)) + 2
            updated["grain"] = int(updated.get("grain", 0)) + 1
            updated["tactic_success_count"] = int(updated.get("tactic_success_count", 0)) + 1
    else:
        updated["wrong_count"] = int(updated.get("wrong_count", 0)) + 1
        updated["grain"] = max(0, int(updated.get("grain", 0)) - 1)
        updated["streak"] = 0
        updated["wrong_book"] = [
            item for item in updated["wrong_book"] if item.get("node_id") != node_id
        ]
        updated["wrong_book"].append(
            {
                "node_id": node_id,
                "title": node_title,
                "question": question,
                "selected_answer": selected_answer,
                "expected_answer": expected_answer,
                "explanation": explanation,
            }
        )

    updated["rank_title"] = get_rank_title(int(updated.get("red_star_points", 0)))
    _refresh_medals(updated)
    return updated


def build_progress_summary(progress: Dict[str, Any]) -> Dict[str, Any]:
    """汇总成长信息。"""
    return {
        "red_star_points": int(progress.get("red_star_points", 0)),
        "grain": int(progress.get("grain", 0)),
        "rank_title": progress.get("rank_title") or get_rank_title(int(progress.get("red_star_points", 0))),
        "medals": progress.get("medals", []),
        "wrong_book": progress.get("wrong_book", []),
        "correct_count": int(progress.get("correct_count", 0)),
        "wrong_count": int(progress.get("wrong_count", 0)),
        "answered_count": int(progress.get("answered_count", 0)),
        "completed_nodes": progress.get("completed_nodes", []),
        "role_mastery_counts": progress.get("role_mastery_counts", {}),
        "streak": int(progress.get("streak", 0)),
        "best_streak": int(progress.get("best_streak", 0)),
        "tactic_success_count": int(progress.get("tactic_success_count", 0)),
    }
