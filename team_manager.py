"""红军小队、支部 PK 与协作战绩管理。"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List

from activity_manager import get_activity
from utils import RUNTIME_DIR, now_text, read_json, write_json

TEAM_PATH = RUNTIME_DIR / "teams.json"


def _load_teams() -> List[Dict[str, Any]]:
    """读取全部小队记录。"""
    return read_json(TEAM_PATH, []) or []


def _save_teams(rows: List[Dict[str, Any]]) -> None:
    """保存全部小队记录。"""
    write_json(TEAM_PATH, rows)


def _member_payload(
    *,
    user_name: str,
    unit_name: str,
    role_name: str,
) -> Dict[str, Any]:
    """构建队员记录。"""
    return {
        "user_name": str(user_name or "匿名学习者"),
        "unit_name": str(unit_name or "未填写单位"),
        "role_name": str(role_name or ""),
        "joined_at": now_text(),
        "contribution_score": 0,
        "contribution_grain": 0,
        "answered_count": 0,
        "correct_count": 0,
        "completed_nodes": [],
    }


def _normalize_team(row: Dict[str, Any]) -> Dict[str, Any]:
    """统一小队结构，兼容旧数据。"""
    members = [item for item in row.get("members", []) if isinstance(item, dict)]
    branch_name = str(row.get("branch_name", "") or row.get("unit_name", "") or "未命名支部")
    normalized = {
        "team_id": str(row.get("team_id", "") or f"team-{secrets.token_hex(4)}"),
        "activity_id": str(row.get("activity_id", "global") or "global"),
        "activity_name": str(row.get("activity_name", "全局活动") or "全局活动"),
        "team_name": str(row.get("team_name", "红军小队") or "红军小队"),
        "branch_name": branch_name,
        "unit_name": str(row.get("unit_name", branch_name) or branch_name),
        "slogan": str(row.get("slogan", "") or ""),
        "captain_name": str(row.get("captain_name", "") or ""),
        "created_by": str(row.get("created_by", "") or ""),
        "created_at": str(row.get("created_at", now_text()) or now_text()),
        "updated_at": str(row.get("updated_at", now_text()) or now_text()),
        "status": str(row.get("status", "进行中") or "进行中"),
        "max_team_size": int(row.get("max_team_size", 6) or 6),
        "members": members,
        "total_score": int(row.get("total_score", 0) or 0),
        "total_grain": int(row.get("total_grain", 0) or 0),
        "answered_count": int(row.get("answered_count", 0) or 0),
        "correct_count": int(row.get("correct_count", 0) or 0),
        "completed_nodes": list(row.get("completed_nodes", []) or []),
        "recent_records": list(row.get("recent_records", []) or []),
    }
    if not normalized["captain_name"] and members:
        normalized["captain_name"] = str(members[0].get("user_name", "") or "")
    return normalized


def list_teams(activity_id: str = "") -> List[Dict[str, Any]]:
    """列出某个活动下的全部红军小队。"""
    rows = [_normalize_team(item) for item in _load_teams()]
    if activity_id:
        rows = [item for item in rows if item.get("activity_id") == activity_id]
    return sorted(rows, key=lambda item: (-int(item.get("total_score", 0)), item.get("team_name", "")))


def get_team(team_id: str = "") -> Dict[str, Any]:
    """按 id 获取小队。"""
    for item in _load_teams():
        normalized = _normalize_team(item)
        if normalized.get("team_id") == team_id:
            return normalized
    return {}


def get_user_team(user_name: str, activity_id: str = "") -> Dict[str, Any]:
    """获取用户当前所在小队。"""
    normalized_user = str(user_name or "").strip()
    if not normalized_user:
        return {}
    for item in list_teams(activity_id):
        for member in item.get("members", []):
            if str(member.get("user_name", "")).strip() == normalized_user:
                return item
    return {}


def create_team(
    *,
    activity_id: str,
    team_name: str,
    branch_name: str,
    slogan: str,
    created_by: str,
    unit_name: str,
    role_name: str,
    max_team_size: int = 6,
) -> Dict[str, Any]:
    """创建红军小队。"""
    activity = get_activity(activity_id) if activity_id else {}
    captain = str(created_by or "匿名学习者").strip() or "匿名学习者"
    branch = str(branch_name or unit_name or "未命名支部").strip() or "未命名支部"
    rows = [_normalize_team(item) for item in _load_teams()]
    for row in rows:
        if row.get("activity_id") != (activity_id or "global"):
            continue
        row["members"] = [
            item for item in row.get("members", []) if str(item.get("user_name", "")).strip() != captain
        ]
    team = {
        "team_id": f"team-{secrets.token_hex(4)}",
        "activity_id": activity_id or "global",
        "activity_name": activity.get("name", "全局活动"),
        "team_name": str(team_name or "红军小队").strip() or "红军小队",
        "branch_name": branch,
        "unit_name": str(unit_name or branch).strip() or branch,
        "slogan": str(slogan or "").strip(),
        "captain_name": captain,
        "created_by": captain,
        "created_at": now_text(),
        "updated_at": now_text(),
        "status": "进行中",
        "max_team_size": max(2, min(int(max_team_size or 6), 20)),
        "members": [
            _member_payload(
                user_name=captain,
                unit_name=unit_name or branch,
                role_name=role_name,
            )
        ],
        "total_score": 0,
        "total_grain": 0,
        "answered_count": 0,
        "correct_count": 0,
        "completed_nodes": [],
        "recent_records": [],
    }
    rows.append(team)
    _save_teams(rows)
    return _normalize_team(team)


def join_team(
    *,
    team_id: str,
    user_name: str,
    unit_name: str,
    role_name: str,
) -> Dict[str, Any]:
    """加入红军小队。"""
    normalized_user = str(user_name or "").strip()
    if not normalized_user:
        return {}
    rows = [_normalize_team(item) for item in _load_teams()]
    target: Dict[str, Any] = {}
    target_activity_id = ""

    for row in rows:
        if row.get("team_id") == team_id:
            target_activity_id = row.get("activity_id", "")
            break

    # 同一活动内只保留一个队伍归属。
    for row in rows:
        if row.get("activity_id") != target_activity_id:
            continue
        row["members"] = [
            item for item in row.get("members", []) if str(item.get("user_name", "")).strip() != normalized_user
        ]

    for row in rows:
        if row.get("team_id") != team_id:
            continue
        members = row.get("members", [])
        if len(members) >= int(row.get("max_team_size", 6)):
            return {}
        members.append(
            _member_payload(
                user_name=normalized_user,
                unit_name=unit_name,
                role_name=role_name,
            )
        )
        row["members"] = members
        row["updated_at"] = now_text()
        target = row
        break

    if target:
        _save_teams(rows)
    return target


def leave_team(team_id: str, user_name: str) -> Dict[str, Any]:
    """退出红军小队。"""
    normalized_user = str(user_name or "").strip()
    rows = [_normalize_team(item) for item in _load_teams()]
    target: Dict[str, Any] = {}
    for row in rows:
        if row.get("team_id") != team_id:
            continue
        row["members"] = [
            item for item in row.get("members", []) if str(item.get("user_name", "")).strip() != normalized_user
        ]
        if row.get("captain_name") == normalized_user and row.get("members"):
            row["captain_name"] = row["members"][0].get("user_name", "")
        row["updated_at"] = now_text()
        target = row
        break
    if target:
        _save_teams(rows)
    return target


def record_team_progress(
    *,
    team_id: str,
    user_name: str,
    unit_name: str,
    role_name: str,
    node_id: str,
    node_title: str,
    score_delta: int,
    grain_delta: int,
    correct: bool,
) -> Dict[str, Any]:
    """记录队伍协作答题结果。"""
    rows = [_normalize_team(item) for item in _load_teams()]
    updated: Dict[str, Any] = {}
    for row in rows:
        if row.get("team_id") != team_id:
            continue
        row["total_score"] = int(row.get("total_score", 0)) + int(score_delta)
        row["total_grain"] = int(row.get("total_grain", 0)) + int(grain_delta)
        row["answered_count"] = int(row.get("answered_count", 0)) + 1
        if correct:
            row["correct_count"] = int(row.get("correct_count", 0)) + 1
        if correct and node_id and node_id not in row.get("completed_nodes", []):
            row["completed_nodes"].append(node_id)

        members = row.get("members", [])
        member = next(
            (
                item
                for item in members
                if str(item.get("user_name", "")).strip() == str(user_name or "").strip()
            ),
            None,
        )
        if not member:
            member = _member_payload(user_name=user_name, unit_name=unit_name, role_name=role_name)
            members.append(member)
        member["unit_name"] = unit_name or member.get("unit_name", "")
        member["role_name"] = role_name or member.get("role_name", "")
        member["contribution_score"] = int(member.get("contribution_score", 0)) + int(score_delta)
        member["contribution_grain"] = int(member.get("contribution_grain", 0)) + int(grain_delta)
        member["answered_count"] = int(member.get("answered_count", 0)) + 1
        if correct:
            member["correct_count"] = int(member.get("correct_count", 0)) + 1
        if correct and node_id and node_id not in member.get("completed_nodes", []):
            member.setdefault("completed_nodes", []).append(node_id)
        row["members"] = members

        record = {
            "timestamp": now_text(),
            "user_name": str(user_name or "匿名学习者"),
            "unit_name": str(unit_name or row.get("unit_name", "") or "未填写单位"),
            "role_name": str(role_name or ""),
            "node_id": str(node_id or ""),
            "node_title": str(node_title or ""),
            "score_delta": int(score_delta or 0),
            "grain_delta": int(grain_delta or 0),
            "correct": bool(correct),
            "team_name": row.get("team_name", ""),
            "branch_name": row.get("branch_name", ""),
            "activity_id": row.get("activity_id", ""),
            "activity_name": row.get("activity_name", ""),
        }
        recent_records = list(row.get("recent_records", []) or [])
        recent_records.append(record)
        row["recent_records"] = recent_records[-80:]
        row["updated_at"] = now_text()
        updated = row
        break
    if updated:
        _save_teams(rows)
    return updated


def _rank_rows(rows: List[Dict[str, Any]], score_key: str, grain_key: str, answered_key: str) -> List[Dict[str, Any]]:
    """统一排序并生成名次。"""
    ranked = sorted(
        rows,
        key=lambda item: (
            -int(item.get(score_key, 0)),
            -int(item.get(grain_key, 0)),
            -int(item.get(answered_key, 0)),
            str(item.get("updated_at", "") or item.get("created_at", "")),
        ),
    )
    results: List[Dict[str, Any]] = []
    for index, item in enumerate(ranked, start=1):
        row = item.copy()
        row["rank"] = index
        results.append(row)
    return results


def get_team_leaderboard(activity_id: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    """获取红军小队排行榜。"""
    rows = list_teams(activity_id)
    results = _rank_rows(rows, "total_score", "total_grain", "answered_count")
    return results[:limit]


def get_branch_pk_board(activity_id: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    """获取支部 PK 榜。"""
    buckets: Dict[str, Dict[str, Any]] = {}
    for team in list_teams(activity_id):
        branch_name = str(team.get("branch_name", "") or team.get("unit_name", "") or "未命名支部")
        bucket = buckets.setdefault(
            branch_name,
            {
                "branch_name": branch_name,
                "activity_id": team.get("activity_id", ""),
                "activity_name": team.get("activity_name", ""),
                "team_names": [],
                "team_count": 0,
                "member_names": set(),
                "total_score": 0,
                "total_grain": 0,
                "answered_count": 0,
                "correct_count": 0,
                "updated_at": "",
            },
        )
        bucket["team_count"] += 1
        bucket["team_names"].append(team.get("team_name", ""))
        bucket["total_score"] += int(team.get("total_score", 0))
        bucket["total_grain"] += int(team.get("total_grain", 0))
        bucket["answered_count"] += int(team.get("answered_count", 0))
        bucket["correct_count"] += int(team.get("correct_count", 0))
        bucket["updated_at"] = max(str(bucket.get("updated_at", "")), str(team.get("updated_at", "")))
        for member in team.get("members", []):
            user_name = str(member.get("user_name", "") or "")
            if user_name:
                bucket["member_names"].add(user_name)
    rows: List[Dict[str, Any]] = []
    for item in buckets.values():
        answer_count = int(item.get("answered_count", 0))
        rows.append(
            {
                "branch_name": item.get("branch_name", ""),
                "activity_id": item.get("activity_id", ""),
                "activity_name": item.get("activity_name", ""),
                "team_count": item.get("team_count", 0),
                "member_count": len(item.get("member_names", set())),
                "total_score": item.get("total_score", 0),
                "total_grain": item.get("total_grain", 0),
                "answered_count": answer_count,
                "correct_rate": round((int(item.get("correct_count", 0)) / answer_count) * 100, 1) if answer_count else 0.0,
                "updated_at": item.get("updated_at", ""),
            }
        )
    results = _rank_rows(rows, "total_score", "total_grain", "answered_count")
    return results[:limit]


def _parse_time(value: str) -> datetime | None:
    """解析时间。"""
    try:
        return datetime.strptime(str(value or ""), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def build_live_feed(activity_id: str = "", limit: int = 20, hours: int = 72) -> List[Dict[str, Any]]:
    """构建实时战绩流。"""
    cutoff = datetime.now() - timedelta(hours=max(1, hours))
    rows: List[Dict[str, Any]] = []
    for team in list_teams(activity_id):
        for record in team.get("recent_records", []):
            ts = _parse_time(record.get("timestamp", ""))
            if ts and ts < cutoff:
                continue
            rows.append(
                {
                    "timestamp": str(record.get("timestamp", "") or ""),
                    "activity_id": team.get("activity_id", ""),
                    "activity_name": team.get("activity_name", ""),
                    "team_id": team.get("team_id", ""),
                    "team_name": team.get("team_name", ""),
                    "branch_name": team.get("branch_name", ""),
                    "user_name": record.get("user_name", ""),
                    "role_name": record.get("role_name", ""),
                    "node_title": record.get("node_title", ""),
                    "score_delta": int(record.get("score_delta", 0)),
                    "grain_delta": int(record.get("grain_delta", 0)),
                    "correct": bool(record.get("correct", False)),
                    "share_text": (
                        f"{record.get('user_name', '匿名学习者')} 在 {team.get('team_name', '红军小队')} "
                        f"完成“{record.get('node_title', '主线节点')}”，"
                        f"{'答对并' if record.get('correct') else '完成作答，'}贡献 {record.get('score_delta', 0)} 分。"
                    ),
                }
            )
    rows.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return rows[:limit]


def build_team_share_text(team_id: str, current_user: str = "") -> str:
    """生成小队分享文案。"""
    team = get_team(team_id)
    if not team:
        return ""
    ranking = get_team_leaderboard(team.get("activity_id", ""), limit=100)
    rank = next((item.get("rank", 0) for item in ranking if item.get("team_id") == team_id), 0)
    latest_record = (team.get("recent_records", []) or [])[-1] if team.get("recent_records") else {}
    actor_name = current_user or latest_record.get("user_name", team.get("captain_name", "红军学员"))
    latest_title = latest_record.get("node_title", "长征主线关卡")
    return (
        f"【红军小队战绩播报】{actor_name} 所在的“{team.get('team_name', '红军小队')}”"
        f"正在参加“{team.get('activity_name', '长征主线活动')}”，"
        f"当前支部为 {team.get('branch_name', '未命名支部')}，"
        f"累计 {team.get('total_score', 0)} 分、粮草 {team.get('total_grain', 0)}，"
        f"小队暂列第 {rank or '--'} 名。最近完成节点：{latest_title}。"
    )


def export_team_rows(activity_id: str = "") -> List[Dict[str, Any]]:
    """导出队伍排行榜数据。"""
    rows = []
    for item in get_team_leaderboard(activity_id, limit=500):
        rows.append(
            {
                "rank": item.get("rank", 0),
                "team_name": item.get("team_name", ""),
                "branch_name": item.get("branch_name", ""),
                "unit_name": item.get("unit_name", ""),
                "activity_name": item.get("activity_name", ""),
                "captain_name": item.get("captain_name", ""),
                "member_count": len(item.get("members", [])),
                "total_score": item.get("total_score", 0),
                "total_grain": item.get("total_grain", 0),
                "answered_count": item.get("answered_count", 0),
                "correct_count": item.get("correct_count", 0),
                "updated_at": item.get("updated_at", ""),
            }
        )
    return rows


def export_branch_rows(activity_id: str = "") -> List[Dict[str, Any]]:
    """导出支部 PK 数据。"""
    return get_branch_pk_board(activity_id, limit=500)


def build_team_member_summary(team_id: str) -> List[Dict[str, Any]]:
    """返回某个小队的成员贡献概览。"""
    team = get_team(team_id)
    members = team.get("members", [])
    rows = sorted(
        members,
        key=lambda item: (
            -int(item.get("contribution_score", 0)),
            -int(item.get("contribution_grain", 0)),
            item.get("user_name", ""),
        ),
    )
    results: List[Dict[str, Any]] = []
    for index, item in enumerate(rows, start=1):
        results.append(
            {
                "rank": index,
                "user_name": item.get("user_name", ""),
                "role_name": item.get("role_name", ""),
                "unit_name": item.get("unit_name", ""),
                "contribution_score": item.get("contribution_score", 0),
                "contribution_grain": item.get("contribution_grain", 0),
                "answered_count": item.get("answered_count", 0),
                "correct_count": item.get("correct_count", 0),
            }
        )
    return results


def summarize_team_presence(activity_id: str = "") -> Dict[str, Any]:
    """汇总队伍、支部与成员规模。"""
    teams = list_teams(activity_id)
    branch_names = set()
    member_names = set()
    for item in teams:
        branch_names.add(str(item.get("branch_name", "") or item.get("unit_name", "")))
        for member in item.get("members", []):
            user_name = str(member.get("user_name", "") or "")
            if user_name:
                member_names.add(user_name)
    return {
        "team_count": len(teams),
        "branch_count": len([item for item in branch_names if item]),
        "team_member_count": len(member_names),
    }
