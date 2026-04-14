"""答题事件统计与大屏数据接口。"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from activity_manager import list_activities
from leaderboard import get_global_leaderboard, get_unit_leaderboard
from utils import RUNTIME_DIR, now_text, read_json, write_json

ANALYTICS_PATH = RUNTIME_DIR / "analytics_events.json"


def _load_events() -> List[Dict[str, Any]]:
    """读取事件记录。"""
    return read_json(ANALYTICS_PATH, []) or []


def _save_events(events: List[Dict[str, Any]]) -> None:
    """写入事件记录。"""
    write_json(ANALYTICS_PATH, events)


def record_dashboard_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """记录统一事件。"""
    events = _load_events()
    normalized = {
        "event_type": str(event.get("event_type", "unknown") or "unknown"),
        "user_name": str(event.get("user_name", "匿名用户") or "匿名用户"),
        "unit_name": str(event.get("unit_name", "未填写单位") or "未填写单位"),
        "role_name": str(event.get("role_name", "") or ""),
        "activity_id": str(event.get("activity_id", "global") or "global"),
        "activity_name": str(event.get("activity_name", "全局活动") or "全局活动"),
        "node_id": str(event.get("node_id", "") or ""),
        "node_title": str(event.get("node_title", "") or ""),
        "question_type": str(event.get("question_type", "") or ""),
        "correct": bool(event.get("correct", False)),
        "mode_label": str(event.get("mode_label", "") or ""),
        "timestamp": str(event.get("timestamp", now_text()) or now_text()),
    }
    events.append(normalized)
    if len(events) > 5000:
        events = events[-5000:]
    _save_events(events)
    return normalized


def record_participation_event(
    *,
    user_name: str,
    unit_name: str,
    role_name: str,
    activity_id: str,
    activity_name: str,
) -> Dict[str, Any]:
    """记录进入活动或剧情的参与事件。"""
    return record_dashboard_event(
        {
            "event_type": "participant_enter",
            "user_name": user_name,
            "unit_name": unit_name,
            "role_name": role_name,
            "activity_id": activity_id,
            "activity_name": activity_name,
        }
    )


def record_answer_event(
    *,
    user_name: str,
    unit_name: str,
    role_name: str,
    activity_id: str,
    activity_name: str,
    node_id: str,
    node_title: str,
    question_type: str,
    correct: bool,
    mode_label: str = "",
) -> Dict[str, Any]:
    """记录答题事件。"""
    return record_dashboard_event(
        {
            "event_type": "quiz_submit",
            "user_name": user_name,
            "unit_name": unit_name,
            "role_name": role_name,
            "activity_id": activity_id,
            "activity_name": activity_name,
            "node_id": node_id,
            "node_title": node_title,
            "question_type": question_type,
            "correct": correct,
            "mode_label": mode_label,
        }
    )


def _parse_timestamp(value: str) -> datetime | None:
    """解析时间字符串。"""
    try:
        return datetime.strptime(str(value or ""), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _filter_recent_hours(events: List[Dict[str, Any]], hours: int) -> List[Dict[str, Any]]:
    """筛选最近若干小时事件。"""
    cutoff = datetime.now() - timedelta(hours=hours)
    result: List[Dict[str, Any]] = []
    for event in events:
        ts = _parse_timestamp(event.get("timestamp", ""))
        if ts and ts >= cutoff:
            result.append(event)
    return result


def build_dashboard_summary(hours: int = 24) -> Dict[str, Any]:
    """构建大屏摘要数据。"""
    events = _load_events()
    recent_events = _filter_recent_hours(events, hours)
    answer_events = [event for event in recent_events if event.get("event_type") == "quiz_submit"]
    enter_events = [event for event in recent_events if event.get("event_type") == "participant_enter"]
    unique_recent_users = {
        str(event.get("user_name", "")).strip()
        for event in recent_events
        if str(event.get("user_name", "")).strip()
    }
    unique_units = {
        str(event.get("unit_name", "")).strip()
        for event in recent_events
        if str(event.get("unit_name", "")).strip()
    }
    correct_count = len([event for event in answer_events if event.get("correct")])
    correct_rate = round((correct_count / len(answer_events)) * 100, 1) if answer_events else 0.0
    return {
        "time_window_hours": hours,
        "recent_participant_count": len(unique_recent_users),
        "recent_unit_count": len(unique_units),
        "recent_enter_count": len(enter_events),
        "recent_answer_count": len(answer_events),
        "correct_rate": correct_rate,
        "activity_count": len(list_activities()),
        "leaderboard_count": len(get_global_leaderboard(limit=500)),
    }


def build_answer_heat_series(hours: int = 24) -> List[Dict[str, Any]]:
    """按小时汇总答题热度。"""
    events = _filter_recent_hours(_load_events(), hours)
    answer_events = [event for event in events if event.get("event_type") == "quiz_submit"]
    now = datetime.now()
    buckets = defaultdict(int)
    for event in answer_events:
        ts = _parse_timestamp(event.get("timestamp", ""))
        if not ts:
            continue
        label = ts.strftime("%m-%d %H:00")
        buckets[label] += 1
    series: List[Dict[str, Any]] = []
    for offset in range(hours - 1, -1, -1):
        time_point = now - timedelta(hours=offset)
        label = time_point.strftime("%m-%d %H:00")
        series.append({"time_label": label, "answer_count": buckets.get(label, 0)})
    return series


def build_node_heat(limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
    """统计节点答题热度。"""
    events = _filter_recent_hours(_load_events(), hours)
    counter: Counter[str] = Counter()
    title_map: Dict[str, str] = {}
    for event in events:
        if event.get("event_type") != "quiz_submit":
            continue
        node_id = str(event.get("node_id", "") or "")
        if not node_id:
            continue
        counter[node_id] += 1
        title_map[node_id] = str(event.get("node_title", node_id) or node_id)
    return [
        {"node_id": node_id, "node_title": title_map.get(node_id, node_id), "answer_count": count}
        for node_id, count in counter.most_common(limit)
    ]


def build_question_type_distribution(hours: int = 24) -> List[Dict[str, Any]]:
    """统计题型分布。"""
    events = _filter_recent_hours(_load_events(), hours)
    counter: Counter[str] = Counter()
    for event in events:
        if event.get("event_type") != "quiz_submit":
            continue
        counter[str(event.get("question_type", "未知题型") or "未知题型")] += 1
    return [{"question_type": key, "count": value} for key, value in counter.most_common()]


def build_role_distribution(hours: int = 24) -> List[Dict[str, Any]]:
    """统计角色参与分布。"""
    events = _filter_recent_hours(_load_events(), hours)
    counter: Counter[str] = Counter()
    for event in events:
        role_name = str(event.get("role_name", "") or "")
        if role_name:
            counter[role_name] += 1
    return [{"role_name": key, "count": value} for key, value in counter.most_common()]


def build_activity_live_rows(hours: int = 24) -> List[Dict[str, Any]]:
    """统计活动动态表现。"""
    events = _filter_recent_hours(_load_events(), hours)
    bucket: Dict[str, Dict[str, Any]] = {}
    for event in events:
        activity_id = str(event.get("activity_id", "global") or "global")
        row = bucket.setdefault(
            activity_id,
            {
                "activity_id": activity_id,
                "activity_name": str(event.get("activity_name", "全局活动") or "全局活动"),
                "participant_names": set(),
                "answer_count": 0,
                "correct_count": 0,
            },
        )
        user_name = str(event.get("user_name", "") or "")
        if user_name:
            row["participant_names"].add(user_name)
        if event.get("event_type") == "quiz_submit":
            row["answer_count"] += 1
            if event.get("correct"):
                row["correct_count"] += 1
    rows: List[Dict[str, Any]] = []
    for item in bucket.values():
        answer_count = int(item.get("answer_count", 0))
        rows.append(
            {
                "activity_id": item.get("activity_id", ""),
                "activity_name": item.get("activity_name", ""),
                "participant_count": len(item.get("participant_names", set())),
                "answer_count": answer_count,
                "correct_rate": round((int(item.get("correct_count", 0)) / answer_count) * 100, 1) if answer_count else 0.0,
            }
        )
    rows.sort(key=lambda row: (-int(row.get("answer_count", 0)), row.get("activity_name", "")))
    return rows


def build_dashboard_payload(hours: int = 24) -> Dict[str, Any]:
    """输出完整大屏数据。"""
    return {
        "summary": build_dashboard_summary(hours=hours),
        "answer_heat": build_answer_heat_series(hours=hours),
        "node_heat": build_node_heat(limit=10, hours=hours),
        "question_type_distribution": build_question_type_distribution(hours=hours),
        "role_distribution": build_role_distribution(hours=hours),
        "activity_live": build_activity_live_rows(hours=hours),
        "unit_leaderboard": get_unit_leaderboard(limit=8),
    }
