"""查询意图识别与过滤规则。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from knowledge_base import load_card_targets
from utils import normalize_knowledge_type


INTENT_TYPES: Dict[str, List[str]] = {
    "event": ["event"],
    "place": ["place", "route"],
    "figure": ["figure", "event"],
    "route": ["route", "event", "place"],
    "faq": ["faq", "event", "spirit"],
    "spirit": ["spirit", "event", "route"],
    "generate_script": ["event", "route", "figure", "place", "spirit"],
    "guide_script": ["event", "route", "figure", "place", "spirit"],
    "video_script": ["event", "route", "figure", "place", "spirit"],
    "quiz_explanation": ["event", "route", "faq"],
    "timeline": ["route", "event", "place"],
    "general": [],
}


def normalize_filters(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """标准化过滤条件。"""
    normalized: Dict[str, Any] = {}
    if not filters:
        return normalized
    for key in ["type", "route_stage", "place", "source_file", "topic", "intent", "source_type", "title"]:
        value = filters.get(key)
        if value in (None, "", "全部"):
            continue
        if key in {"type", "source_type"}:
            if isinstance(value, list):
                normalized[key] = [normalize_knowledge_type(str(item)) for item in value if str(item).strip()]
            else:
                normalized[key] = normalize_knowledge_type(str(value))
        else:
            normalized[key] = str(value)
    return normalized


def build_where(filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """把过滤条件转换成 Chroma where。"""
    normalized = normalize_filters(filters)
    if not normalized:
        return None

    clauses = []
    for key in ["type", "route_stage", "place", "source_file", "topic", "source_type", "title"]:
        value = normalized.get(key)
        if value in (None, "", "全部") or isinstance(value, list):
            continue
        clauses.append({key: value})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def match_target(question: str) -> Dict[str, str]:
    """识别问题中最可能的目标节点或人物。"""
    text = str(question or "").strip()
    best = {"target": "", "title": "", "type": "", "route_stage": "", "place": "", "alias": ""}
    best_score = -1
    for item in load_card_targets():
        aliases = [item.get("title", ""), item.get("route_stage", ""), item.get("place", "")]
        aliases.extend([part for part in str(item.get("aliases", "") or "").split("||") if part])
        aliases.extend([part for part in str(item.get("keywords", "") or "").split("||") if part])
        for alias in aliases:
            alias = str(alias or "").strip()
            if not alias or alias not in text:
                continue
            score = len(alias)
            item_type = str(item.get("type", "") or "")
            title = str(item.get("title", alias) or alias)
            if alias == title:
                score += 6
            if item_type in {"route", "event", "figure", "place", "spirit"}:
                score += 5
            if item_type == "faq":
                score += 1
            if any(keyword in alias for keyword in ["为什么", "什么", "哪些", "包括", "意义"]):
                score -= 8
            if score > best_score:
                best = {
                    "target": title,
                    "title": title,
                    "type": item_type,
                    "route_stage": item.get("route_stage", ""),
                    "place": item.get("place", ""),
                    "alias": alias,
                }
                best_score = score
    return best


def detect_query_intent(question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """对问题做轻量意图与目标识别。"""
    text = (question or "").strip()
    normalized_filters = normalize_filters(filters)
    target_info = match_target(text)
    lowered = text.lower()

    if normalized_filters.get("intent"):
        intent = str(normalized_filters.get("intent", "general"))
    elif any(keyword in text for keyword in ["讲解稿", "解说稿", "导览讲解", "讲解词", "讲稿"]):
        intent = "guide_script"
    elif any(keyword in text for keyword in ["视频脚本", "短视频", "旁白脚本", "分镜"]):
        intent = "video_script"
    elif any(keyword in text for keyword in ["为什么这题", "题目解析", "为什么选", "答案解析", "为什么选B", "为什么选A"]):
        intent = "quiz_explanation"
    elif any(keyword in text for keyword in ["时间线", "时间轴", "经过哪些地方", "路线图", "沿线", "历程", "路线"]):
        intent = "timeline"
    elif any(keyword in text for keyword in ["长征精神", "精神", "启示", "价值", "理想信念", "艰苦奋斗"]):
        intent = "spirit"
    elif target_info.get("type") == "figure" or any(keyword in text for keyword in ["谁是", "人物", "哪位将领", "毛泽东", "周恩来", "朱德", "张闻天"]):
        intent = "figure"
    elif target_info.get("type") == "place" or any(keyword in text for keyword in ["地点", "哪里", "在哪", "旧址", "桥", "河", "山"]):
        intent = "place"
    elif target_info.get("type") == "route" or any(keyword in text for keyword in ["转兵", "会师", "行军", "北上", "草地", "雪山"]):
        intent = "route"
    elif target_info.get("type") == "faq" or any(keyword in lowered for keyword in ["为什么", "是什么", "怎么理解", "有何意义"]):
        intent = "faq"
    elif target_info.get("type") in {"event", "route"} or any(keyword in text for keyword in ["会议", "战役", "战斗", "出发", "渡河"]):
        intent = "event"
    else:
        intent = "general"

    type_filters = INTENT_TYPES.get(intent, []).copy()
    if target_info.get("type") and target_info.get("type") not in type_filters and intent in {"general", "faq", "quiz_explanation"}:
        type_filters.insert(0, target_info.get("type", "event"))

    return {
        "intent": intent,
        "target": target_info.get("target", ""),
        "target_type": target_info.get("type", ""),
        "target_alias": target_info.get("alias", ""),
        "type_filters": type_filters,
        "route_stage": target_info.get("route_stage", ""),
        "place": target_info.get("place", ""),
        "figure": target_info.get("target", "") if target_info.get("type") == "figure" else "",
    }


def merge_filters(question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """合并用户筛选与意图识别结果。"""
    normalized = normalize_filters(filters)
    intent_info = detect_query_intent(question, filters=normalized)

    merged = normalized.copy()
    if not merged.get("type") and intent_info.get("type_filters"):
        merged["type"] = intent_info["type_filters"]
    if not merged.get("route_stage") and intent_info.get("route_stage"):
        merged["route_stage"] = intent_info["route_stage"]
    if not merged.get("place") and not merged.get("route_stage") and intent_info.get("place"):
        merged["place"] = intent_info["place"]
    return {
        "intent": intent_info["intent"],
        "target": intent_info.get("target", ""),
        "target_type": intent_info.get("target_type", ""),
        "target_alias": intent_info.get("target_alias", ""),
        "filters": merged,
        "entities": {
            "route_stage": intent_info.get("route_stage", ""),
            "place": intent_info.get("place", ""),
            "figure": intent_info.get("figure", ""),
        },
    }


def expand_filter_variants(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将多类型过滤展开为多个查询。"""
    normalized = normalize_filters(filters)
    type_value = normalized.get("type")
    if not isinstance(type_value, list):
        return [normalized]
    variants: List[Dict[str, Any]] = []
    for item in type_value:
        variant = normalized.copy()
        variant["type"] = item
        variants.append(variant)
    return variants or [normalized]
