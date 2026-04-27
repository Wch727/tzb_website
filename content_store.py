"""仓库内置长征史内容的统一读取与匹配工具。"""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import DATA_DIR, normalize_knowledge_type


ROUTE_CHAPTERS: List[Dict[str, Any]] = [
    {
        "id": "departure_breakthrough",
        "title": "出发与突围",
        "subtitle": "从中央苏区出发，穿越封锁线，在巨大压力下寻找新的战略转移通道。",
        "badge": "第一篇章",
        "node_ids": [
            "ruijin_departure",
            "yudu_crossing",
            "break_four_blockades",
            "xiangjiang_battle",
        ],
    },
    {
        "id": "turning_adjustment",
        "title": "转折与调整",
        "subtitle": "通道转兵、黎平与猴场会议相继展开，最终在遵义实现全局性转折。",
        "badge": "第二篇章",
        "node_ids": [
            "tongdao_turn",
            "liping_meeting",
            "houchang_meeting",
            "zunyi_meeting",
            "loushanguan_battle",
        ],
    },
    {
        "id": "crossing_breakthrough",
        "title": "巧渡与突破",
        "subtitle": "以灵活机动摆脱强敌围追堵截，在赤水、金沙江与大渡河一线打开新局面。",
        "badge": "第三篇章",
        "node_ids": [
            "sidu_chishui",
            "jinshajiang_crossing",
            "daduhe_forcing",
            "luding_bridge",
            "maogong_meeting",
        ],
    },
    {
        "id": "northward_victory",
        "title": "北上与会师",
        "subtitle": "翻雪山、过草地、经榜罗镇与吴起镇北上，最终实现胜利会师。",
        "badge": "第四篇章",
        "node_ids": [
            "snow_mountains",
            "grassland_crossing",
            "bangluo_meeting",
            "wuqi_meeting",
            "zhiluozhen_battle",
            "huining_meeting",
        ],
    },
]

FIGURE_PROFILE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "毛泽东": {
        "role": "中国共产党、中国人民解放军和中华人民共和国的主要缔造者之一",
        "summary": "毛泽东在长征中逐步成为党和红军正确战略方向的重要领导者之一。围绕通道转兵、遵义会议和四渡赤水等关键节点，他提出并坚持从中国实际出发、灵活机动作战的主张，为红军由被动转向主动发挥了决定性作用。",
        "background": "依据中国共产党新闻网和毛主席纪念堂官方资料整理，毛泽东是中国共产党、中国人民解放军和中华人民共和国的主要缔造者之一。长征前后，面对第五次反“围剿”失败和战略转移中的严峻危机，他更加突出强调从实际出发、独立自主判断敌情和路线问题。湘江战役之后，毛泽东关于改变原定行军方向、避免再入敌军重兵区的主张，逐步得到更多同志认同。",
        "long_march_role": "在长征进程中，毛泽东的重要作用集中体现在推动战略方向调整、促进遵义会议实现历史性转折、指挥四渡赤水等关键机动作战，并帮助党和红军逐步走出最危险的被动局面。",
        "significance": "理解长征为什么能够转危为安，毛泽东是绕不开的关键人物。他的历史作用不仅体现在具体战役和会议上，更体现在把马克思主义基本原理同中国革命实际结合起来，推动党在极端复杂形势下形成更加成熟的战略判断。",
        "related_nodes": ["tongdao_turn", "zunyi_meeting", "sidu_chishui", "jinshajiang_crossing"],
        "official_sources": [
            {"title": "毛泽东业绩室第三页--中国共产党新闻--人民网", "url": "https://cpc.people.com.cn/GB/143527/176227/index.html", "publisher": "中国共产党新闻网"},
            {"title": "毛主席纪念堂概况--毛主席纪念堂--人民网", "url": "https://cpc.people.com.cn/GB/143527/143528/10412112.html", "publisher": "中国共产党新闻网"},
        ],
    },
    "周恩来": {
        "role": "中国共产党和中华人民共和国主要领导人之一",
        "summary": "周恩来在长征中承担重要军事、政治和组织协调工作，是红军在危局中维护团结、组织转移和推动战略调整的重要领导者之一。",
        "background": "依据中国共产党新闻网和周恩来纪念网资料整理，周恩来是伟大的无产阶级革命家、政治家、军事家和外交家，也是中国人民解放军主要创建人之一。长征开始时，他在党中央和军队中承担极其重要的责任，既要组织前线作战和中央机关转移，又要处理部队在连续战斗与急剧变化形势中的统一指挥问题。",
        "long_march_role": "湘江战役后，周恩来对形势严峻性有更深认识，并在后续路线调整、会议讨论和领导团结中发挥了关键作用。遵义会议前后，他坚持从全局出发推动形成新的正确方向，是长征由危转安的重要组织者。",
        "significance": "周恩来的突出贡献，在于他既有实际军事与组织能力，又始终坚持维护团结、维护全局。理解遵义会议前后的历史变化，不仅要看到战略主张的变化，也要看到周恩来在凝聚共识和推动落实中的重要作用。",
        "related_nodes": ["xiangjiang_battle", "liping_meeting", "zunyi_meeting", "yudu_crossing"],
        "official_sources": [
            {"title": "周恩来业绩室第二页--中国共产党新闻--人民网", "url": "https://cpc.people.com.cn/GB/143527/175873/index.html", "publisher": "中国共产党新闻网"},
            {"title": "周恩来纪念网--领袖人物纪念馆--人民网", "url": "https://zhouenlai.people.cn/", "publisher": "人民网"},
        ],
    },
    "朱德": {
        "role": "红军总司令，中国共产党和人民军队的重要领导人",
        "summary": "朱德在长征中长期担任红军重要军事领导职务，对部队行军作战、士气稳定和组织协调作出重要贡献，是中央红军主力得以持续前进的重要支柱。",
        "background": "依据中国共产党新闻网资料整理，朱德是中华人民共和国元帅、卓越军事家，也是中国人民解放军的重要创建人之一。长征时期，朱德不仅需要统筹主力部队行动、稳定军心，还要面对连续作战、艰苦行军与复杂敌情带来的巨大压力。",
        "long_march_role": "从中央苏区出发到雪山草地阶段，朱德始终是红军主力的重要统帅者之一。在长征途中，他以稳健坚韧的作风支撑部队连续行军和作战，对部队保持组织性、纪律性和坚持到底的意志具有重要意义。",
        "significance": "朱德的历史作用不是只体现在单一战役，而是贯穿长征全程。理解长征的军事组织、部队整合和主力坚持，就必须看到朱德所发挥的统率和支撑作用。",
        "related_nodes": ["ruijin_departure", "xiangjiang_battle", "snow_mountains", "huining_meeting"],
        "official_sources": [
            {"title": "朱德--资料中心--中国共产党新闻网", "url": "https://cpc.people.com.cn/GB/64162/126778/126780/7489937.html", "publisher": "中国共产党新闻网"},
        ],
    },
    "张闻天": {
        "role": "党的早期重要领导人、理论家",
        "summary": "张闻天在长征转折过程中发挥了重要作用。特别是在遵义会议前后的党内讨论与领导调整中，他是推动形成正确方向的重要人物之一。",
        "background": "依据人民网党史频道公开资料整理，张闻天是中国共产党杰出的革命家和理论家，也是党的早期重要领导人。长征初期，随着湘江战役后危机不断加深，党内对既有军事指导的反思日益加深，张闻天逐步支持更加符合中国实际的战略判断与领导安排。",
        "long_march_role": "遵义会议前后，张闻天在酝酿、召开和落实转折方面都发挥了积极作用。他同毛泽东、王稼祥等人共同推动党内形成新的认识，并在会议之后参与承担重要领导责任，使转折能够真正落实到组织和行动层面。",
        "significance": "理解遵义会议，不能只看少数几位最常被提及的人物，也要看到张闻天等人在党内形成新共识中的重要贡献。张闻天体现的是长征转折过程中党内理论思考与组织调整相互作用的历史特点。",
        "related_nodes": ["houchang_meeting", "zunyi_meeting", "tongdao_turn", "liping_meeting"],
        "official_sources": [
            {"title": "张闻天：遵义会议台前幕后的第一主角--党史频道-人民网", "url": "https://dangshi.people.com.cn/n/2014/0609/c85037-25120853.html", "publisher": "人民网党史频道"},
        ],
    },
    "王稼祥": {
        "role": "党的重要领导干部、理论工作者",
        "summary": "王稼祥在长征危局中支持正确领导和正确路线，对遵义会议形成新的领导格局发挥了重要作用，是长征转折中具有关键意义的重要人物之一。",
        "background": "依据中国共产党新闻网公开资料整理，王稼祥早年赴苏联学习，较早接触和研究马克思主义。长征初期，随着危机不断加深，他对党内既有指导问题的反思逐步加深，并在实际政治立场上支持更加符合中国实际的正确方向。",
        "long_march_role": "遵义会议前后，王稼祥同毛泽东、张闻天等人一道，推动党内形成新的认识和新的领导格局。他的作用不只在于表态支持，更在于增强了正确路线在组织层面的基础和稳定性。",
        "significance": "王稼祥的历史价值说明，长征中的转折并不是由单一个人独立完成，而是通过多位重要领导干部共同推动形成的。通过他，可以更完整地理解遵义会议为何能够真正成为转折点。",
        "related_nodes": ["zunyi_meeting", "houchang_meeting", "liping_meeting"],
        "official_sources": [
            {"title": "王稼祥：不能为了党员数量而降低党的质量、党的水平--中国共产党新闻--中国共产党新闻网", "url": "https://cpc.people.com.cn/GB/34136/2543815.html", "publisher": "中国共产党新闻网"},
        ],
    },
    "刘伯承": {
        "role": "红军重要军事指挥员",
        "summary": "刘伯承在长征中以卓越军事指挥能力著称，特别是在强渡大渡河、飞夺泸定桥等关键行动中发挥了重要作用，是长征军事史上的代表性人物之一。",
        "background": "依据中国共产党新闻网资料整理，刘伯承是中华人民共和国元帅、杰出军事家。长期的军事实践使他兼具理论素养和实战能力。进入长征中段后，红军在贵州、四川等地面临复杂地形和密集敌情，刘伯承的指挥经验在关键行动中得到充分体现。",
        "long_march_role": "在长征关键突破阶段，刘伯承对渡河、突击和快速机动等行动发挥了重要指挥作用。他所代表的，不只是个人军事才能，更是红军在长征中不断形成和强化的机动作战能力。",
        "significance": "通过刘伯承，可以更直观地理解长征为什么不仅是行军史，也是军事史。长征能够不断突破险阻，不仅依靠信念和意志，也依靠一批具有卓越指挥能力的军事领导者。",
        "related_nodes": ["daduhe_forcing", "luding_bridge", "jinshajiang_crossing", "maogong_meeting"],
        "official_sources": [
            {"title": "刘伯承--资料中心--中国共产党新闻网", "url": "https://cpc.people.com.cn/GB/64162/126778/126780/7490151.html", "publisher": "中国共产党新闻网"},
        ],
    },
    "聂荣臻": {
        "role": "红军重要军事领导人",
        "summary": "聂荣臻在长征中参与组织多次关键行动，在西南和川西北地区的作战与部队协调中发挥了积极作用，是红军坚持北上的重要领导者之一。",
        "background": "依据中国共产党新闻网资料整理，聂荣臻是中华人民共和国元帅、杰出军事家。早年赴欧学习并参加革命活动，回国后长期从事党的军事工作。长征进入复杂险峻地形后，部队不仅要面对高强度机动和连续作战，也要保持组织秩序和战斗意志，聂荣臻在这一过程中承担了重要责任。",
        "long_march_role": "在长征的艰苦推进阶段，聂荣臻既要面对敌情和地形压力，也要协调部队行动、保障主线持续推进。他的贡献体现了许多重要军事领导者在具体组织与实战层面所发挥的支撑作用。",
        "significance": "理解长征胜利，不应只看到最耀眼的几个节点，也要看到像聂荣臻这样在长期征途中承担大量组织与作战任务的重要领导者。他代表了一支队伍能够持续前进背后的坚实力量。",
        "related_nodes": ["luding_bridge", "snow_mountains", "grassland_crossing", "wuqi_meeting"],
        "official_sources": [
            {"title": "聂荣臻--资料中心--中国共产党新闻网", "url": "https://cpc.people.com.cn/GB/64162/126778/126780/7490472.html", "publisher": "中国共产党新闻网"},
        ],
    },
    "彭德怀": {
        "role": "红军重要将领",
        "summary": "彭德怀在长征中多次参与重要战斗和部队组织工作，是红军坚持战斗精神和敢打硬仗作风的重要代表人物之一。",
        "background": "依据中国共产党新闻网资料整理，彭德怀出身贫苦农民家庭，早年投身革命，组织平江起义并创建红五军。长征过程中，红军不仅需要战略调整，也需要在连续战斗中保持顽强斗志，彭德怀以作风硬朗、指挥果断著称，在多个高压阶段承担重要职责。",
        "long_march_role": "彭德怀在长征中的作用，集中体现在关键战斗中的顽强作战、部队组织和战斗精神塑造上。通过他，可以看到长征为什么既是战略转移史，也是一部敢打硬仗、不断突围的战斗史。",
        "significance": "彭德怀所体现的，是长征中的勇于担当、敢打硬仗和坚持到底的革命品质。他不仅是重要将领，也代表着千千万万奋战在第一线的红军指战员所共同体现的精神力量。",
        "related_nodes": ["xiangjiang_battle", "break_four_blockades", "wuqi_meeting", "zhiluozhen_battle"],
        "official_sources": [
            {"title": "彭德怀--资料中心--中国共产党新闻网", "url": "https://cpc.people.com.cn/GB/64162/126778/126780/7490066.html", "publisher": "中国共产党新闻网"},
        ],
    },
}


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """读取 JSON 列表文件。"""
    if not path.exists():
        return []
    content = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in content if isinstance(item, dict)] if isinstance(content, list) else []


def _load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    """读取 CSV 行数据。"""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _merge_image_fields(item: Dict[str, Any], mapped: Dict[str, Any]) -> Dict[str, Any]:
    """将图片映射信息补齐到内容记录中。"""
    merged = item.copy()
    for field in ["image", "image_alt", "image_caption", "remote_image_url"]:
        if not merged.get(field) and mapped.get(field):
            merged[field] = mapped[field]
    merged.setdefault("image", "")
    merged.setdefault("image_alt", merged.get("title", "长征史图片"))
    merged.setdefault("image_caption", merged.get("summary", "")[:60])
    merged.setdefault("remote_image_url", "")
    return merged


@lru_cache(maxsize=1)
def load_image_map() -> Dict[str, Any]:
    """读取图片映射配置。"""
    path = DATA_DIR / "image_map.json"
    if not path.exists():
        return {"items": {}, "fallbacks": {}}
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        return {"items": {}, "fallbacks": {}}
    return {
        "items": content.get("items", {}) if isinstance(content.get("items"), dict) else {},
        "fallbacks": content.get("fallbacks", {}) if isinstance(content.get("fallbacks"), dict) else {},
    }


def _image_mapping_for_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """根据标题、节点名和地点查找图片映射。"""
    image_map = load_image_map().get("items", {})
    candidates = [
        item.get("image_key", ""),
        item.get("id", ""),
        item.get("title", ""),
    ]
    for candidate in candidates:
        candidate = str(candidate or "").strip()
        if candidate and candidate in image_map and isinstance(image_map[candidate], dict):
            return image_map[candidate]
    return {}


@lru_cache(maxsize=1)
def load_route_nodes_data() -> List[Dict[str, Any]]:
    """读取主路线节点数据。"""
    path = DATA_DIR / "route_nodes.json"
    rows = _load_json_list(path)
    nodes: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "route"))
        item["order"] = int(item.get("order", index))
        item["score"] = int(item.get("score", 10))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("avatar", "assets/avatar/guide_digital_host.png")
        item.setdefault("summary", "")
        item.setdefault("background", "")
        item.setdefault("process", "")
        item.setdefault("significance", "")
        item.setdefault("figures", [])
        item.setdefault("key_points", [])
        item.setdefault("related_nodes", [])
        item.setdefault("quiz", {})
        nodes.append(item)
    nodes.sort(key=lambda row: int(row.get("order", 0)))
    return nodes


@lru_cache(maxsize=1)
def load_figures_data() -> List[Dict[str, Any]]:
    """读取人物数据。"""
    rows = _load_json_list(DATA_DIR / "figures.json")
    figures: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        override = FIGURE_PROFILE_OVERRIDES.get(str(item.get("title", "") or ""), {})
        if override:
            item.update(override)
        item["type"] = normalize_knowledge_type(item.get("type", "figure"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("background", item.get("summary", ""))
        item.setdefault("significance", "")
        item.setdefault("role", "重要人物")
        item.setdefault("long_march_role", item.get("summary", ""))
        item.setdefault("official_sources", [])
        item.setdefault("related_nodes", [])
        figures.append(item)
    return figures


@lru_cache(maxsize=1)
def load_events_data() -> List[Dict[str, Any]]:
    """读取事件数据。"""
    rows = _load_json_list(DATA_DIR / "events.json")
    events: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "event"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("significance", "")
        events.append(item)
    return events


@lru_cache(maxsize=1)
def load_spirit_topics() -> List[Dict[str, Any]]:
    """读取长征精神专题。"""
    rows = _load_json_list(DATA_DIR / "spirit.json")
    topics: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "spirit"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("detail", "")
        topics.append(item)
    return topics


@lru_cache(maxsize=1)
def load_faq_items() -> List[Dict[str, Any]]:
    """读取 FAQ 数据。"""
    items = []
    for row in _load_csv_rows(DATA_DIR / "faq.csv"):
        row = row.copy()
        row["type"] = normalize_knowledge_type(row.get("type", "faq"))
        row.setdefault("title", row.get("question", "长征史问答"))
        row.setdefault("summary", row.get("answer", ""))
        row.setdefault("extended_note", "")
        items.append(row)
    return items


@lru_cache(maxsize=1)
def load_places_data() -> List[Dict[str, Any]]:
    """读取地点数据。"""
    rows = _load_json_list(DATA_DIR / "places.json")
    places: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "place"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("background", item.get("summary", ""))
        item.setdefault("significance", "")
        places.append(item)
    return places


def get_route_node_data(node_id: str) -> Optional[Dict[str, Any]]:
    """按 id、标题或路线阶段获取节点。"""
    for node in load_route_nodes_data():
        if node_id in [node.get("id"), node.get("title"), node.get("route_stage")]:
            return node
    return None


def get_route_chapters() -> List[Dict[str, Any]]:
    """按展陈篇章组织长征主线节点。"""
    node_index = {item.get("id"): item for item in load_route_nodes_data()}
    chapters: List[Dict[str, Any]] = []
    for chapter in ROUTE_CHAPTERS:
        nodes = [node_index[node_id] for node_id in chapter.get("node_ids", []) if node_id in node_index]
        chapter_item = chapter.copy()
        chapter_item["nodes"] = nodes
        chapter_item["count"] = len(nodes)
        chapters.append(chapter_item)
    return chapters


def get_chapter_for_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """根据节点定位其所属的主线篇章。"""
    node_id = str(node.get("id", "") or "")
    for chapter in get_route_chapters():
        if node_id in chapter.get("node_ids", []):
            return chapter
    return {
        "id": "general",
        "title": "主线展项",
        "subtitle": "沿着长征主线继续深入阅读与学习。",
        "badge": "展项单元",
        "nodes": [],
        "count": 0,
    }


def get_featured_route_nodes(limit: int = 6) -> List[Dict[str, Any]]:
    """返回首页优先展示的代表性节点。"""
    featured_ids = [
        "ruijin_departure",
        "xiangjiang_battle",
        "zunyi_meeting",
        "sidu_chishui",
        "luding_bridge",
        "huining_meeting",
    ]
    node_index = {item.get("id"): item for item in load_route_nodes_data()}
    featured = [node_index[node_id] for node_id in featured_ids if node_id in node_index]
    if len(featured) < limit:
        existing_ids = {item.get("id") for item in featured}
        for node in load_route_nodes_data():
            if node.get("id") not in existing_ids:
                featured.append(node)
            if len(featured) >= limit:
                break
    return featured[:limit]


def build_node_related_questions(node: Dict[str, Any], limit: int = 4) -> List[str]:
    """围绕节点构造相关问题，优先复用 FAQ。"""
    title = str(node.get("title", "") or "")
    place = str(node.get("place", "") or "")
    faq_matches: List[str] = []
    for item in load_faq_items():
        question = str(item.get("question", "") or item.get("title", "") or "").strip()
        keywords = str(item.get("keywords", "") or "")
        if not question:
            continue
        if title and title in question:
            faq_matches.append(question)
            continue
        if title and title in keywords:
            faq_matches.append(question)
            continue
        if place and place.split("、")[0] in question:
            faq_matches.append(question)
    generated = [
        f"{title}发生在什么历史背景下？",
        f"{title}为什么能成为长征中的关键节点？",
        f"{title}与哪些重要人物密切相关？",
        f"从{title}可以理解哪些长征精神内涵？",
    ]
    questions: List[str] = []
    for question in faq_matches + generated:
        if question and question not in questions:
            questions.append(question)
        if len(questions) >= limit:
            break
    return questions[:limit]


def get_recommended_questions(limit: int = 8) -> List[str]:
    """返回首页和知识页通用的推荐问题。"""
    defaults = [
        "长征为什么要开始？",
        "湘江战役为什么重要？",
        "遵义会议意味着什么？",
        "四渡赤水体现了什么战略智慧？",
        "飞夺泸定桥在长征中具有怎样的象征意义？",
        "为什么说长征是战略转移的伟大胜利？",
        "长征精神包括哪些核心内涵？",
        "会宁会师为什么被视为长征胜利的重要标志？",
    ]
    questions: List[str] = []
    for item in load_faq_items():
        candidate = str(item.get("question", "") or item.get("title", "") or "").strip()
        if candidate and candidate not in questions:
            questions.append(candidate)
        if len(questions) >= limit:
            break
    for candidate in defaults:
        if candidate not in questions:
            questions.append(candidate)
        if len(questions) >= limit:
            break
    return questions[:limit]


def get_node_extended_reading(node: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    """围绕节点整理延伸阅读卡片。"""
    reading: List[Dict[str, Any]] = []
    for figure_name in node.get("figures", [])[:3]:
        figure = get_figure_data(figure_name)
        if figure:
            reading.append(figure)
    title = str(node.get("title", "") or "")
    for item in load_faq_items():
        question = str(item.get("question", "") or "")
        if title and title in question:
            reading.append(item)
    for item in load_spirit_topics():
        haystack = f"{node.get('summary', '')}\n{node.get('significance', '')}"
        if item.get("title") and str(item.get("title")) in haystack:
            reading.append(item)
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in reading:
        key = (item.get("type", ""), item.get("title", ""), item.get("question", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def get_figure_data(name: str) -> Optional[Dict[str, Any]]:
    """按人物名称获取人物数据。"""
    for item in load_figures_data():
        if name in [item.get("title"), item.get("name")]:
            return item
    return None


def get_related_nodes_for_figure(figure: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    """获取人物专题关联的路线节点。"""
    nodes = load_route_nodes_data()
    related_ids = [item for item in figure.get("related_nodes", []) if item]
    if related_ids:
        return [node for node in nodes if node.get("id") in related_ids][:limit]

    route_stage = str(figure.get("route_stage", "") or "")
    matched = [node for node in nodes if route_stage and node.get("route_stage") == route_stage]
    if matched:
        return matched[:limit]
    return nodes[:limit]


FIGURE_LECTURE_SCRIPTS: Dict[str, str] = {}


FIGURE_LECTURE_SCRIPTS.update(
    {
        "毛泽东": """《毛泽东》人物专题讲解词

请把视线先放到湘江战役之后。那时的中央红军刚刚经历重大损失，队伍在敌军围追堵截中继续西进，最紧迫的问题已经摆在面前：如果仍然沿着原来的思路走下去，红军还能不能保存下来，中国革命还能不能打开新的局面。

毛泽东在长征中的历史分量，正是在这个关口逐步显现的。他不是凭空出现在转折点上的人物。早在井冈山斗争和中央苏区时期，他就反复思考中国革命道路、根据地建设和人民战争问题。到了长征途中，这些经验与判断开始在更严峻的环境中接受检验。

从通道转兵到黎平会议、猴场会议，再到遵义会议，红军的方向一步步发生调整。毛泽东主张从敌情、地形、部队实际出发，反对机械执行不合实际的作战安排。遵义会议之后，这种战略判断逐渐转化为红军摆脱被动、争取主动的实际能力。

四渡赤水最能说明这一点。红军不是简单地向前硬冲，而是在敌军重兵之间灵活穿插，调动对手，创造战机。毛泽东在这一阶段体现出的，是把现实处境、军事行动和战略目标结合起来的能力。

因此，毛泽东专题讲述的重点，不是重复一个称谓，而是说明中国革命为什么能在最困难的时候重新找到方向。长征中的毛泽东，是把实践经验转化为战略主动的重要人物。资料依据：中国共产党新闻网、人民网党史资料等公开资料。""",
        "周恩来": """《周恩来》人物专题讲解词

周恩来在长征中的形象，不适合只用一个“参与领导”概括。长征是一场极其复杂的行动，中央机关要转移，前线部队要作战，后勤运输要维持，领导关系也要在危局中重新调整。周恩来的重要性，恰恰体现在这些复杂事务交织在一起的时候。

湘江战役以后，红军遭受重大损失，形势已经不能再回避。周恩来面对的，不只是战场压力，还有整个领导集体如何面对错误、如何重新形成共识的问题。他能够在危局中维护团结，推动对军事指导问题的反思，也能在新的方向形成后继续承担落实责任。

遵义会议前后，周恩来的作用尤其关键。他不是旁观会议变化的人，而是处在军事指挥、组织协调和领导调整的交汇点上。会议形成新的判断以后，红军还要继续行军、继续作战、继续处理复杂局势。周恩来在其中发挥的，是把新的方向转化为实际行动的组织能力。

如果说长征需要有人指出方向，也同样需要有人把队伍稳住。周恩来这一人物专题，最应该让人看到的就是这种力量：在局势混乱时守住全局，在压力极大时维护团结，在转折形成后推动执行。

讲周恩来，就是讲长征中的组织韧性。革命队伍能够穿过危机，不只因为有正确判断，也因为有人能把判断变成队伍继续前进的秩序。资料依据：中国共产党新闻网、周恩来纪念网等公开资料。""",
        "朱德": """《朱德》人物专题讲解词

讲朱德，不能只寻找一个最惊险的瞬间。朱德在长征中的作用，更像一条沉稳的主轴，贯穿在红军主力的行军、作战、整合和坚持之中。作为红军总司令，他所承担的是一种长期、持续、全局性的责任。

长征一开始，红军就面临连续突围和长距离转移。部队要打仗，也要行军；要突破敌军封锁，也要保持组织秩序。这样的压力不是一场战斗结束就会消失，而是一路伴随。朱德的威望、经验和沉稳作风，对于维持军心、稳定部队、保障主力继续前进，具有不可替代的意义。

到了雪山草地阶段，这种作用更加明显。那一段征程考验的不是单个指挥动作，而是整支队伍能不能在饥寒、疲惫、自然险阻和不确定局势中坚持下去。朱德所代表的，是红军在长期艰难推进中仍然保持组织、纪律和信心的力量。

会师阶段也不能离开朱德来理解。长征不是某一支部队孤立到达终点，而是多支红军力量经过艰难转移后重新汇合。朱德长期承担的统率与协调责任，正是理解这一历史结果的重要线索。

朱德专题要讲出的，不是一个响亮标签，而是一种稳重的历史分量：长征能走到底，既靠转折会议和经典战例，也靠有人始终把队伍带住，把军心稳住，把前进的秩序维持住。资料依据：中国共产党新闻网等公开资料。""",
        "张闻天": """《张闻天》人物专题讲解词

张闻天这一页，不适合写成普通人物简介。他最值得讲的，是遵义会议前后党内认识怎样发生变化，新的领导方向怎样在危机中形成。很多人记住遵义会议，是因为它成为长征和中国革命的重要转折；而张闻天正是理解这一转折过程的重要人物。

湘江战役之后，红军付出沉重代价，党内对既有军事指导的反思迅速加深。张闻天作为党的早期重要领导人和理论工作者，并不是在会议上突然出现的角色。他长期参与党的理论和领导工作，对形势变化、路线问题和组织调整都有自己的判断。

遵义会议前后，张闻天的作用不在于战场上的冲锋，而在于党内讨论、会议酝酿和领导调整这些关键环节。转折不是一句话就能完成的，它需要有人把问题摆出来，需要有人支持新的判断，也需要在组织层面形成能够执行的新格局。

会议之后，新的方向还要落到行动上。张闻天在中央领导工作中承担重要责任，使遵义会议形成的转折进一步进入组织运行和实际决策。这一点，正是他在长征人物谱系中的独特位置。

讲张闻天，就是讲长征转折背后的思想过程和组织过程。长征不是只靠几个高光时刻推进的，它也依靠党内对错误的纠正、对现实的重新认识，以及对正确方向的共同确认。资料依据：人民网党史频道等公开资料。""",
        "王稼祥": """《王稼祥》人物专题讲解词

王稼祥在长征史中不是最容易被第一眼注意到的人物，但他的意义正在于此。历史转折并不总是由最响亮的名字单独完成，很多时候，它需要在关键时刻有一批人看清问题、支持正确判断，并共同推动新的方向稳定下来。

长征初期的危机，让党内越来越清楚地看到原有军事指导存在严重问题。湘江战役之后，这种反思变得更加迫切。王稼祥在这一时期的重要作用，集中体现在他对正确方向的支持，以及在领导调整中的积极作用。

遵义会议的转折，既是军事路线的转折，也是组织关系和领导格局的转折。王稼祥的价值，不在于前线冲杀，而在于关键会议和党内认识形成过程中，增加了正确方向的组织支撑。没有这种支撑，新的判断就很难真正成为新的领导格局。

从这个角度看，王稼祥专题可以帮助观众理解遵义会议为什么不是一场孤立会议。它背后有危机推动，有现实检验，也有党内重要干部对正确路线的辨认和支持。王稼祥就是这一过程中的代表人物之一。

讲王稼祥，要讲清一种并不喧哗却非常关键的历史作用：在转折关头，能够识别正确方向、支持正确方向，本身就是推动历史前进的重要力量。资料依据：中国共产党新闻网等公开资料。""",
        "刘伯承": """《刘伯承》人物专题讲解词

刘伯承这一人物，最适合放在“怎样把战略变成行动”这个问题里讲。长征不是地图上的一条线，也不是只靠意志就能完成的远行。每一次渡河、突围、穿插、掩护，都需要具体的军事判断和执行能力。

红军进入贵州、四川一带后，面对的地形越来越复杂，敌军部署也不断变化。行动稍有迟缓，就可能被合围；判断稍有偏差，就可能失去突破机会。刘伯承长期积累的军事经验，使他能够在复杂局势中组织部队、判断地形、把握时机。

强渡大渡河、飞夺泸定桥等节点之所以成为经典，不只是因为场面惊险，更因为它们体现了红军在险境中组织行动的能力。渡河不是口号，夺桥也不是传说，它们背后有侦察、部署、突击、协同和指挥。刘伯承这一人物线索，正能把这些具体军事环节呈现出来。

讲刘伯承，不能只说“军事家”三个字。真正要讲清的是，长征为什么既是一场战略转移，也是一部军事行动史。红军能够一步步突破险阻，靠的是坚定信念，也靠一批指挥员把判断落到战场上的能力。

通过刘伯承，观众会看到长征的另一层厚度：它不是单纯走出来的传奇，而是在一次次具体战斗和艰难选择中打出来、闯出来的历史。资料依据：中国共产党新闻网等公开资料。""",
        "聂荣臻": """《聂荣臻》人物专题讲解词

聂荣臻的人物专题，适合从“长征怎样保持组织力量”讲起。长征走到最艰难的时候，考验一支队伍的不只是能不能打下一场仗，而是能不能在长时间行军、饥寒疲惫、敌军压力和自然险阻中，仍然保持秩序、保持信心、保持继续前进的能力。

聂荣臻长期承担重要军事工作。他在长征中的作用，不是靠某一个孤立瞬间来呈现，而是体现在持续的组织、协同和保障之中。部队要快速转移，要面对复杂地形，要在连续作战后继续保持战斗力，这些都离不开稳定可靠的军事领导和政治工作。

翻雪山、过草地这样的阶段，尤其能说明这种人物的重要性。越是极端环境，越能看出组织力量的分量。没有这种力量，队伍可能在自然困难面前被拖垮，也可能在长期疲惫中失去秩序。聂荣臻所代表的，正是把队伍稳住、把行动接续起来的那一类关键人物。

讲聂荣臻，不是为了寻找一个单独的传奇场面，而是为了让人看到长征胜利背后的持续工作。伟大征程并不只由高潮组成，也由许多沉稳、坚韧、连续的组织努力共同托举起来。

聂荣臻专题要讲出的，是一种不喧哗却可靠的力量：在漫长征途中，有人始终把部队的运行、协同和坚持放在心上。资料依据：中国共产党新闻网等公开资料。""",
        "彭德怀": """《彭德怀》人物专题讲解词

彭德怀身上最鲜明的，是敢打硬仗、能扛重压的气质。讲彭德怀，不能把他讲成一个抽象的英雄符号，而要把他放进红军连续作战、突破封锁、到达陕北后继续打开局面的历史现场中去看。

长征途中，红军既要摆脱敌军围追，又要在关键时刻敢于出击。彭德怀长期以作风硬朗、指挥果断著称，在多次重要战斗和部队组织工作中发挥了显著作用。湘江战役前后、北上行军途中，以及到达陕北后的作战中，都可以看到他所代表的一线将领气质。

这种气质并不是简单的勇猛。长征中的勇猛，必须和判断、纪律、组织结合起来，才能真正成为战斗力。面对重压时敢承担，遇到硬仗时顶得上，关键时刻能够组织部队完成任务，这才是彭德怀人物形象中最有力量的部分。

通过彭德怀，可以更直接地理解长征中的革命英雄主义。它不是空泛的赞美，而是在困难面前顶得上去，在压力面前扛得下来，在关键时刻敢于完成任务的真实行动。

彭德怀专题最终要落到这层认识：长征的胜利，不只来自路线调整，也来自一批能打硬仗、敢担重任的红军将领和指战员。资料依据：中国共产党新闻网等公开资料。""",
    }
)


def build_figure_story_script(figure: Dict[str, Any]) -> str:
    """为人物专题页生成正式讲解稿。"""
    title = str(figure.get("title", "") or "重要人物")
    role = str(figure.get("role", "") or "党的重要领导人")
    summary = str(figure.get("summary", "") or "").strip()
    background = str(figure.get("background", "") or "").strip()
    long_march_role = str(figure.get("long_march_role", "") or "").strip()
    significance = str(figure.get("significance", "") or "").strip()
    route_stage = str(figure.get("route_stage", "") or "").strip()
    related_nodes = get_related_nodes_for_figure(figure, limit=4)
    related_titles = "、".join(node.get("title", "") for node in related_nodes if node.get("title"))
    sources = figure.get("official_sources", []) or []
    source_publishers = "、".join(
        item.get("publisher", "") for item in sources[:3] if item.get("publisher")
    ) or "官方党史资料"
    return (
        f"《{title}》人物专题讲解稿\n\n"
        f"在长征历史的叙述中，{title}常常与若干关键节点相联系。{title}是{role}，"
        f"{summary or '也是理解党在革命危局中如何统一思想、调整方向和推动主线前行的重要人物之一。'}\n\n"
        f"如果从人物经历与历史背景进入这一专题，{background or '可以看到他在中国革命的重要阶段长期承担理论、组织或领导责任，并在党的早期发展中留下了鲜明印记。'}"
        f"把这段经历放回当时的时代环境中理解，才能更清楚地认识到他为什么会在长征转折阶段发挥作用。\n\n"
        f"从长征主线看，{long_march_role or '他在长征中的重要作用，主要体现在关键节点中的领导、组织、判断与行动推进。'}"
        f"{'与其密切相关的节点包括' + related_titles + '。' if related_titles else '相关节点可以帮助进一步理解其作用是如何落到具体历史场景中的。'}"
        f"{'这一人物在主线中的位置可概括为“' + route_stage + '”。' if route_stage else ''}\n\n"
        f"如果进一步从历史贡献来把握，{significance or '理解这一人物，有助于把长征放回中国共产党领导中国革命的整体历史进程中加以把握。'}"
        f"因此，人物专题并不是对个体经历的孤立介绍，而是通过人物去理解长征转折、组织调整和历史选择的内在逻辑。\n\n"
        f"综合来看，阅读{title}这一人物专题，既要看到其个人经历、思想和职责，也要看到他与遵义会议前后、路线调整、组织领导和革命转折之间的关系。"
        f"本专题文字依据{source_publishers}等公开资料整理，可与相关节点和官方来源对照阅读。"
    )


FIGURE_LECTURE_FRAMES: Dict[str, Dict[str, str]] = {
    "毛泽东": {
        "opening": "理解毛泽东，不能只停留在“重要领导人”这几个字上。真正把他放回长征最危急的转折关口，才能看清他为什么会成为改变全局走向的关键人物。",
        "background_lead": "如果从长征前后的历史处境来理解这一人物，首先要看到的是：",
        "role_lead": "把目光重新投回长征主线，毛泽东最值得把握的，并不是某一句口号，而是在危局中提出新判断、推动新方向并把战略主动权逐步夺回来的能力。",
        "significance_lead": "因此，毛泽东在长征中的意义，不只是“参加了哪些节点”，而是体现在他如何把党和红军从被动困局中一步步带向主动局面。",
        "closing": "今天回看长征，毛泽东专题真正要讲清楚的，是中国革命为什么能够在极端困难中重新找到方向，以及这种方向感是如何在实践中形成并被证明的。",
    },
    "周恩来": {
        "opening": "讲周恩来，不能只讲他“参与领导”这一层，更要讲他在最复杂、最危险、最需要稳住全局的时候，怎样承担起组织、协调和调整的责任。",
        "background_lead": "周恩来的分量，首先来自他在党和红军中的实际位置：",
        "role_lead": "进入长征主线之后，周恩来的突出之处，在于他既处在实际指挥和组织运转的中心，又能够在危机中推动党内形成新的正确共识。",
        "significance_lead": "所以，理解周恩来，不应只停留在“重要领导人”的概括上，而要看到他在长征转危为安过程中发挥的黏合剂、稳定器和推动者作用。",
        "closing": "周恩来这一人物专题真正要说明的是：在革命最艰难的时候，真正稳住一支队伍、稳住一个领导集体，往往比单纯打赢一场战斗更难，也更关键。",
    },
    "朱德": {
        "opening": "如果说有些人物代表长征中的决策转折，那么朱德更代表长征中的主力部队、军心士气和持续推进的力量。理解朱德，要从“稳住整支队伍”这个角度进入。",
        "background_lead": "朱德的作用之所以重要，首先在于他的身份并不是局部性的，而是贯穿整支红军主力行动过程的：",
        "role_lead": "放到长征主线上看，朱德并不只是某一场战斗中的名字，他更像是一条稳定的主轴，支撑着队伍在连续作战、艰难行军和复杂整合中始终不散、不乱、不垮。",
        "significance_lead": "因此，朱德在长征中的意义，更多体现在“支撑全程”而不是“出现在某一瞬间”。",
        "closing": "讲朱德，最终要让人看到的是：长征的胜利，不只靠转折会议和经典战例，也靠有人始终把主力部队带住、把军心稳住、把前进的秩序维持住。",
    },
    "张闻天": {
        "opening": "提到张闻天，很多人首先想到的是遵义会议。但如果只把他理解成会议中的一个名字，这个人物就被讲窄了。张闻天真正重要的地方，在于他代表了长征转折中党内新认识形成的过程。",
        "background_lead": "从人物经历与历史背景看，张闻天并不是在长征中偶然出现的重要角色，而是在党内理论与领导层面长期发挥作用的关键人物：",
        "role_lead": "进入长征转折阶段以后，张闻天的价值体现在他能够从党内讨论、会议组织和领导调整这些并不“热闹”、却极其关键的环节中，推动新的正确方向落下来。",
        "significance_lead": "所以，理解张闻天，不能只盯着谁在台前讲话，更要看到谁在党内形成新共识、确立新方向的过程中发挥了决定性作用。",
        "closing": "张闻天这一人物专题真正要讲清楚的是：长征的历史转折，并不是单靠一两个人的个人意志完成的，而是党内思想、组织和领导共同调整的结果，张闻天正是这一过程中的关键人物之一。",
    },
    "王稼祥": {
        "opening": "王稼祥在长征史中并不总是最显眼的人物，但正因为如此，他更值得认真讲清。很多关键转折，并不是靠最响亮的名字完成的，而是靠一批能够在关键时刻支持正确方向的人共同推动。",
        "background_lead": "从历史背景看，王稼祥的重要性来自他在党内领导层中的实际影响：",
        "role_lead": "放到长征主线中看，王稼祥的意义主要不在前线冲杀，而在关键会议和领导调整之中。他的判断、支持与表态，为新的正确方向增加了重要的组织力量。",
        "significance_lead": "因此，王稼祥这条人物线索的价值，在于帮助人们理解：长征转折既是思想转折，也是组织转折，正确路线的确立离不开关键人物的集体推动。",
        "closing": "讲王稼祥，最终要落到一点上：历史转折往往不是一声号令完成的，而是在关键节点中，通过一批人对正确方向的支持、辨认和坚持，逐渐形成稳定格局。",
    },
    "刘伯承": {
        "opening": "讲刘伯承，最适合从“军事执行力”切入。长征不仅是一部战略转移史，也是一部高强度军事行动史，而刘伯承正是把战略要求落到战场执行层面的代表人物。",
        "background_lead": "刘伯承之所以在长征人物谱系中占有重要位置，首先因为他兼具丰富军事实践和冷静判断能力：",
        "role_lead": "进入长征中后段之后，刘伯承的价值体现得尤其明显。面对复杂地形、敌军围堵和快速机动需求，他所代表的是把计划变成行动、把判断变成战果的能力。",
        "significance_lead": "所以，刘伯承这一人物专题真正要讲的，不只是“他参加了哪些战斗”，而是要让人看到红军在关键突破阶段背后的军事组织与执行能力。",
        "closing": "通过刘伯承，可以更具体地理解长征为什么不只是艰苦行军，也是充满战术选择、战场决断和军事智慧的一段伟大征程。",
    },
    "聂荣臻": {
        "opening": "聂荣臻这一人物，最值得从“艰苦推进中的组织支撑”来理解。长征走到最艰险的阶段，真正考验的不是一句口号，而是一支队伍能不能在极端条件下继续保持秩序、继续前进。",
        "background_lead": "从人物经历与职责看，聂荣臻长期承担重要军事工作，这使他在长征途中不仅要看战斗本身，也要看部队整体运行：",
        "role_lead": "在长征主线中，聂荣臻所体现的，不只是某一次露脸的胜利，而是在复杂环境下保障部队推进、协同与坚持的能力。这种作用往往不喧哗，却非常关键。",
        "significance_lead": "因此，聂荣臻专题的意义，在于帮助我们理解长征胜利背后那些稳定、坚韧、持续的组织力量。",
        "closing": "讲聂荣臻，最终要让观众意识到：一支部队能够穿过漫长征途，靠的不只是高光时刻，更靠许多关键人物在艰苦条件下持续不断地把队伍托住。",
    },
    "彭德怀": {
        "opening": "彭德怀身上最鲜明的气质，是硬仗气质。讲他，最适合从“敢打硬仗、能扛重压”这个角度展开，因为这正是长征途中最真实、也最能感染人的一面。",
        "background_lead": "彭德怀的重要性，首先来自他在红军中的作战地位和长期形成的战斗作风：",
        "role_lead": "回到长征主线，彭德怀所体现的不是抽象的英雄主义，而是在连续作战、高压推进和关键战斗里真正顶上去、扛起来的那种力量。",
        "significance_lead": "所以，讲彭德怀，不能只讲他勇猛，更要讲这种勇猛为什么重要。它支撑的是整支队伍在困境中的战斗意志，也体现了长征过程中革命英雄主义的现实基础。",
        "closing": "通过彭德怀这条人物线，可以更直接地看到长征为什么不仅是一段艰苦历程，也是一段在极端条件下不断锤炼出战斗精神的历史。",
    },
}


FIGURE_LECTURE_APPENDIX: Dict[str, str] = {
    "毛泽东": "展厅讲到这里，毛泽东这一人物的线索就不再只是个人经历，而是同整条长征主线紧密连在一起：湘江之后的危局、遵义会议的转折、四渡赤水的主动，前后构成一条清晰的历史脉络。沿着这条线索看，才能理解长征为什么不仅保存了革命力量，也推动中国共产党在实践中走向更加成熟。",
    "周恩来": "周恩来的讲解如果只停在姓名和职务上，就会漏掉最重要的一层：他在危机中把队伍、会议和行动连接起来。长征中的很多转折，都需要有人在复杂局势里把不同意见、不同任务和不同部队重新组织到同一个方向上。周恩来的价值，正是在这种细密而艰难的工作中体现出来。",
    "朱德": "朱德这一人物线索，适合与整条长征路线一起看。越是行程漫长，越能看出统率者的分量；越是环境恶劣，越能看出军心和纪律的重要。长征的胜利不是短促爆发出来的，而是在长期坚持中积累出来的。朱德所体现的，正是这种让队伍始终保持前进能力的历史力量。",
    "张闻天": "张闻天专题还有一层值得特别注意：他让人看到长征中的转折不是简单的“换一个办法”，而是党内认识、领导方式和组织责任的深刻调整。遵义会议之所以重要，正在于它把危机中的反思转化为新的领导实践。张闻天的作用，正落在这一历史转换的关键位置上。",
    "王稼祥": "王稼祥这一人物提醒我们，历史上的关键支持并不总是站在最前排，却常常决定转折能否真正形成。遵义会议前后的新格局，需要有人提出判断，也需要有人支持判断、稳定判断。王稼祥的分量，就在于他让正确方向不只是一个意见，而成为可以继续推进的集体选择。",
    "刘伯承": "刘伯承专题适合放在军事路线中继续延展。长征中的许多节点看似是地名和桥梁，实际背后都有复杂的判断：哪里能渡，怎样突击，如何协同，如何在敌人合围前抢出时间。刘伯承这样的指挥员，使这些判断变成行动，也让长征的军事智慧有了更具体的面貌。",
    "聂荣臻": "聂荣臻这一人物的讲解，不追求单一的传奇场面，而强调长征中那些持续运转的力量。越是艰难的征途，越需要稳定的组织工作、政治工作和军事协同。这样的作用不一定总在最显眼的位置，却支撑着队伍穿过最漫长的困难。理解聂荣臻，也是在理解长征胜利背后的耐力与秩序。",
    "彭德怀": "彭德怀专题最能把观众带回红军一线作战的紧张感。长征并不是只有会议和路线，也有连续作战中的压力、牺牲和担当。彭德怀身上体现出的硬仗气质，让人看到红军为什么能在困境中保持战斗意志。这样的英雄主义，不是抽象口号，而是关键时刻顶上去的行动。",
}


def build_figure_story_script(figure: Dict[str, Any]) -> str:
    """生成人物专题页的正式讲解词，按人物分别组织叙述。"""
    title = str(figure.get("title", "") or "重要人物")
    role = str(figure.get("role", "") or "党的重要领导人")
    summary = str(figure.get("summary", "") or "").strip()
    background = str(figure.get("background", "") or "").strip()
    long_march_role = str(figure.get("long_march_role", "") or "").strip()
    significance = str(figure.get("significance", "") or "").strip()
    route_stage = str(figure.get("route_stage", "") or "").strip()
    related_nodes = get_related_nodes_for_figure(figure, limit=4)
    related_titles = "、".join(node.get("title", "") for node in related_nodes if node.get("title"))
    sources = figure.get("official_sources", []) or []
    source_publishers = "、".join(
        item.get("publisher", "") for item in sources[:3] if item.get("publisher")
    ) or "官方党史资料"
    profile = FIGURE_LECTURE_FRAMES.get(
        title,
        {
            "opening": f"{title}并不是长征叙事中可以一笔带过的人物。把他放回具体历史场景中去看，才能真正理解这一人物在革命转折中的位置。",
            "background_lead": "从人物背景进入这一专题，首先要看到的是：",
            "role_lead": "回到长征主线之中，这个人物最值得关注的，是他怎样在关键节点上把自己的职责转化为真实作用。",
            "significance_lead": "因此，讲这一人物，不能只停留在身份概括上，更要看到他在长征历史推进中的具体分量。",
            "closing": "这一人物专题所要说明的，正是历史转折往往由一批不同岗位、不同风格、但都极其关键的人物共同完成。",
        },
    )
    related_clause = (
        f"与他密切相关的长征节点包括{related_titles}，把这些节点联系起来看，会更容易理解这一人物并不是孤立存在的。"
        if related_titles
        else "把这一人物放回相关节点与会议进程中去理解，才能更完整地看见其历史位置。"
    )
    stage_clause = f"从长征主线位置看，他主要出现在“{route_stage}”这一关键阶段。" if route_stage else ""
    parts = [
        f"《{title}》人物专题讲解词",
        f"{profile['opening']}{summary or f'{title}是{role}。'}",
        f"{profile['background_lead']}{background or f'{title}长期承担重要职责，既有理论或组织积累，也在关键历史阶段不断形成更清晰的政治判断。'}",
        f"{profile['role_lead']}{long_march_role or f'{title}在长征中的作用，主要体现在关键节点中的组织、判断、协调或执行层面。'}{stage_clause}{related_clause}",
        f"{profile['significance_lead']}{significance or f'理解{title}，有助于把长征放回中国共产党领导中国革命的整体进程中加以把握。'}",
        f"{profile['closing']}本专题文字依据{source_publishers}等公开党史资料整理。",
    ]
    return "\n\n".join(parts)


_LEGACY_FIGURE_LECTURE_SCRIPTS: Dict[str, str] = {
    "毛泽东": """《毛泽东》人物专题讲解词

讲毛泽东，最重要的不是把他放在一个固定的称谓里，而是把他放回长征途中最危险的历史关口。1934 年底到 1935 年初，中央红军在突围中付出巨大代价，湘江战役以后，队伍面临的已经不只是军事压力，更是方向选择的压力：继续按原定路线行动，还是根据中国革命的实际情况重新作出判断。

毛泽东在这一阶段的历史作用，正是在这种危局中逐步显现出来的。通道转兵、黎平会议、猴场会议到遵义会议，红军的行军方向和领导方式不断调整。毛泽东长期在根据地斗争和军事斗争中形成的经验，使他更加重视从实际出发、避实击虚、灵活机动。遵义会议以后，这种判断不再只是个人意见，而逐步转化为红军摆脱被动局面的战略能力。

四渡赤水是理解毛泽东长征作用的一个典型窗口。红军并不是简单地向前冲，而是在敌军重兵围追中不断调动对手、寻找空隙、创造主动。正是在这样的运动战中，党和红军逐步走出长征初期的沉重困境。

因此，毛泽东专题讲述的重点，是中国革命在极端困难中怎样重新找到方向。长征中的毛泽东，不只是一个出现在会议名单中的人物，更是把革命经验、战略判断和现实处境结合起来的人物。本篇依据中国共产党新闻网、人民网党史资料等公开资料整理。""",
    "周恩来": """《周恩来》人物专题讲解词

讲周恩来，要把他放在长征这部复杂的历史现场中理解。长征不是一次单纯的军事行军，而是一场牵动中央机关、前线部队、后方转移和领导关系调整的巨大行动。在这样的局面下，周恩来承担的不是单一任务，而是贯穿军事、政治、组织和协调多个方面的责任。

湘江战役以后，红军处境极其严峻。队伍遭受重大损失，原有行动方案的弊端也更加明显。周恩来的重要作用，在于他能够面对现实形势，推动党内对错误军事指导进行反思，同时维护领导集体团结，保障红军在危急局面下不至于失去组织重心。

遵义会议前后，周恩来并不是旁观者。他参与重要讨论，也在会议之后继续承担军事指挥和组织协调责任。理解遵义会议，不能只看会议结论本身，还要看这些结论如何落实到之后的行动中。周恩来在这一过程中发挥的，正是把新的方向转化为实际运转的作用。

周恩来专题的重点，是“稳住全局”。在长征这样艰苦的历史进程中，能够作出判断很重要，能够团结队伍、协调行动、推动执行同样重要。周恩来的历史贡献，正体现在这种细密而关键的组织力量之中。本篇依据中国共产党新闻网、周恩来纪念网等公开资料整理。""",
    "朱德": """《朱德》人物专题讲解词

朱德在长征中的形象，不能只用一场战斗来概括。作为红军总司令，他的作用更像贯穿长征全程的一条主轴：部队要走、要打、要整合、要坚持，背后都离不开稳定的军事领导和组织支撑。

长征开始后，中央红军在连续突围中面对的是多重压力。敌军围追堵截，部队疲惫行军，组织系统也要在转移中保持有效运转。在这样的环境里，朱德的意义不只在于发布命令，更在于以长期形成的威望、经验和沉稳作风维系军心，保证主力部队在极端艰苦条件下仍然保持基本秩序。

翻雪山、过草地这样的阶段，尤其能说明朱德这类军事领导人的分量。那不是一两个漂亮战术动作能够解决的难题，而是对整支部队体力、纪律、信念和组织力的全面考验。朱德所代表的，正是红军能够在漫长征途中不散、不乱、继续前进的稳定力量。

讲朱德，最终要看到长征胜利背后的另一种历史逻辑：伟大的转折固然重要，经典战例也令人振奋，但一支队伍能够走到底，还需要有人把军心稳住，把队伍带住，把前进秩序维持住。本篇依据中国共产党新闻网等公开资料整理。""",
    "张闻天": """《张闻天》人物专题讲解词

张闻天的人物专题，最适合从遵义会议前后的党内转折讲起。很多人记住遵义会议，是因为它改变了长征的方向，也改变了中国革命的走向。但这场转折并不是突然发生的，它经历了危机中的反思、讨论中的辨明，以及组织层面的重新调整。张闻天正是这个过程中不可忽视的人物。

长征初期，红军在突围中不断遭遇困难，尤其湘江战役以后，党内对既有军事指导的反思迅速加深。张闻天作为党的早期重要领导人和理论工作者，在这一时期逐步支持更加符合中国实际的战略判断。遵义会议前后，他在党内讨论、会议酝酿和领导调整中发挥了积极作用。

张闻天的特殊价值，不在于某一次战斗中的冲锋，而在于他参与推动了新的政治共识和领导格局的形成。遵义会议之后，转折要真正发生作用，还必须落到组织和行动层面。张闻天在这一过程中承担重要领导责任，使会议形成的方向能够进一步落实。

因此，讲张闻天，就是讲长征转折背后的思想和组织过程。长征不是只靠英雄瞬间完成的，它也依赖党内对错误的纠正、对现实的重新认识，以及对正确方向的共同确认。本篇依据人民网党史频道等公开资料整理。""",
    "王稼祥": """《王稼祥》人物专题讲解词

王稼祥在长征叙事中并不总是最显眼的名字，但他的作用恰恰说明：历史转折往往不是由一个人单独完成，而是由关键时刻一批人共同推动。王稼祥的重要性，集中体现在遵义会议前后对正确方向的支持和推动上。

长征初期的危机，让党内越来越清楚地看到原有军事指导存在严重问题。面对这种局面，是否能够支持新的判断，是否能够在关键会议和领导调整中站到正确方向一边，直接关系到转折能否形成。王稼祥在这一过程中发挥了重要作用。

他的价值不在前线冲杀，而在党内形成新认识、新领导格局的关键环节中。遵义会议之所以能够成为转折点，既因为有新的战略判断，也因为这一判断获得了重要领导干部的支持。王稼祥正是这种集体推动力量中的代表人物。

讲王稼祥，可以帮助人们理解遵义会议不只是一次会议记录上的变化，更是一次思想路线和组织关系的调整。长征转折的形成，需要有人提出方向，也需要有人识别方向、支持方向并共同把它稳定下来。本篇依据中国共产党新闻网等公开资料整理。""",
    "刘伯承": """《刘伯承》人物专题讲解词

讲刘伯承，最适合从军事执行和战场判断进入。长征不仅是一条行军路线，也是一连串艰难的军事行动。战略上要转移，战场上还必须能突破；方向上要正确，执行上还必须能落地。刘伯承正是这种军事执行能力的代表人物之一。

红军进入贵州、四川一带后，地形更加复杂，敌情更加多变。渡河、穿插、突击、掩护，每一步都要求指挥员既能看清全局，又能处理具体战场问题。刘伯承长期积累的军事经验，使他在关键行动中能够冷静判断、组织部队、完成突破。

强渡大渡河、飞夺泸定桥等节点，之所以成为长征史中的经典，不只是因为场面惊险，也因为它们集中体现了红军在险境中组织行动的能力。刘伯承这一人物线索，能让人看到长征胜利背后不只是信念和意志，还有严密的指挥、果断的判断和高水平的军事组织。

因此，刘伯承专题要讲清楚的是：长征不是“走出来”的传奇那么简单，它也是在一次次战场选择中打出来、闯出来的历史。本篇依据中国共产党新闻网等公开资料整理。""",
    "聂荣臻": """《聂荣臻》人物专题讲解词

聂荣臻的人物专题，适合从艰苦环境中的组织支撑来讲。长征走到最困难的时候，真正考验一支队伍的，不只是能不能打一仗，而是能不能在长时间行军、饥寒疲惫和敌军压力之下，仍然保持组织、纪律和继续前进的能力。

聂荣臻长期承担重要军事工作，在长征途中所体现的，不是一时一地的高光，而是持续性的组织与协同作用。部队要快速机动，要面对复杂地形，要在连续作战中保持战斗力，这些都需要稳定可靠的军事领导和政治工作支撑。

在翻越雪山、穿越草地以及北上推进的艰苦阶段，这种支撑尤其重要。越是在极端环境里，越能看出组织工作的分量。聂荣臻代表的，正是那些在漫长征途中不断把队伍稳住、把行动接续起来的重要力量。

讲聂荣臻，不是为了寻找单一的传奇瞬间，而是为了看到长征胜利背后的持续力量。伟大征程并不只由高潮构成，也由许多沉稳、坚韧、连续的工作共同托举起来。本篇依据中国共产党新闻网等公开资料整理。""",
    "彭德怀": """《彭德怀》人物专题讲解词

彭德怀身上最鲜明的，是敢打硬仗、能扛重压的战斗气质。讲彭德怀，就不能把他讲成一个抽象符号，而要把他放进红军连续作战、突破封锁和到达陕北后的新阶段中去看。

长征途中，红军既要摆脱敌军围追，又要在关键时刻敢于出击。彭德怀长期以作风硬朗、指挥果断著称，在多次重要战斗和部队组织工作中发挥了显著作用。湘江战役、北上行军以及到达陕北后的作战，都能看到他所代表的那种一线将领气质。

这种气质并不是简单的“勇猛”。在长征这样的环境里，勇猛必须和判断、纪律、组织结合起来，才能真正成为战斗力。彭德怀的历史作用，正体现了红军在困境中敢于作战、善于坚持、能够承担艰巨任务的精神面貌。

通过彭德怀，可以更直接地理解长征中的革命英雄主义。它不是空泛的赞美，而是在困难面前顶得上去、在压力面前扛得下来、在关键时刻敢于完成任务的真实行动。本篇依据中国共产党新闻网等公开资料整理。""",
}


def build_figure_story_script(figure: Dict[str, Any]) -> str:
    """Return a person-specific exhibit narration script."""
    title = str(figure.get("title", "") or "重要人物")
    if title in FIGURE_LECTURE_SCRIPTS:
        script = FIGURE_LECTURE_SCRIPTS[title]
        appendix = FIGURE_LECTURE_APPENDIX.get(title, "")
        if appendix and "资料依据" in script:
            return script.replace("资料依据", f"{appendix}\n\n资料依据", 1)
        return "\n\n".join(part for part in [script, appendix] if part)

    role = str(figure.get("role", "") or "党的重要领导人")
    summary = str(figure.get("summary", "") or "").strip()
    background = str(figure.get("background", "") or "").strip()
    long_march_role = str(figure.get("long_march_role", "") or "").strip()
    significance = str(figure.get("significance", "") or "").strip()
    return "\n\n".join(
        [
            f"《{title}》人物专题讲解词",
            f"{title}是{role}。{summary}",
            background,
            long_march_role,
            significance,
        ]
    )


def match_route_node(question: str) -> Optional[Dict[str, Any]]:
    """从问题中匹配最相关的路线节点。"""
    text = str(question or "").strip()
    best: Optional[Dict[str, Any]] = None
    best_length = 0
    for node in load_route_nodes_data():
        candidates = [node.get("title", ""), node.get("route_stage", ""), node.get("place", "")]
        for candidate in candidates:
            candidate = str(candidate or "").strip()
            if candidate and candidate in text and len(candidate) > best_length:
                best = node
                best_length = len(candidate)
    return best


def match_faq(question: str) -> Optional[Dict[str, Any]]:
    """从问题中匹配最相关 FAQ。"""
    text = str(question or "").strip()
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for item in load_faq_items():
        score = 0
        title = str(item.get("title", "") or "")
        prompt = str(item.get("question", "") or "")
        keywords = str(item.get("keywords", "") or "")
        for candidate in [title, prompt]:
            if candidate and candidate in text:
                score = max(score, len(candidate) + 20)
        if keywords:
            for keyword in [part.strip() for part in keywords.split("、") if part.strip()]:
                if keyword and keyword in text:
                    score += len(keyword)
        if score > best_score:
            best = item
            best_score = score
    return best


def build_source_card(item: Dict[str, Any], snippet: str = "") -> Dict[str, Any]:
    """将本地内容记录转换为来源卡片。"""
    item_type = normalize_knowledge_type(item.get("type", "event"))
    return {
        "source_file": item.get("source_file", "仓库内置数据"),
        "title": item.get("title", "未命名"),
        "type": item_type,
        "snippet": snippet or item.get("summary", "")[:220],
    }


def get_related_nodes(node: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """获取当前节点附近的相关推荐节点。"""
    nodes = load_route_nodes_data()
    related_ids = [item for item in node.get("related_nodes", []) if item]
    if related_ids:
        related = [candidate for candidate in nodes if candidate.get("id") in related_ids]
        return related[:limit]

    current_order = int(node.get("order", 0))
    related = [
        candidate
        for candidate in nodes
        if candidate.get("id") != node.get("id") and abs(int(candidate.get("order", 0)) - current_order) <= 2
    ]
    return related[:limit]


def build_static_sources_for_node(node: Dict[str, Any], extra_items: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """为静态模式构建来源卡片。"""
    sources = [
        build_source_card(
            {
                "title": node.get("title", "长征节点"),
                "type": node.get("type", "route"),
                "source_file": "data/route_nodes.json",
                "summary": node.get("summary", ""),
            },
            snippet=node.get("summary", ""),
        )
    ]
    for item in extra_items or []:
        if item:
            sources.append(build_source_card(item, snippet=item.get("answer", "") or item.get("summary", "")))
    return sources


def build_node_story_script(node: Dict[str, Any]) -> str:
    """为节点生成可直接展示的正式讲解稿。"""
    title = str(node.get("title", "") or "长征节点")
    audience = "各位参观者"
    summary = str(node.get("summary", "") or "").strip()
    background = str(node.get("background", "") or "").strip()
    process = str(node.get("process", "") or "").strip()
    significance = str(node.get("significance", "") or "").strip()
    figures = "、".join(node.get("figures", [])[:4]) if node.get("figures") else "红军指战员与党的重要领导人"
    key_points = "；".join(node.get("key_points", [])[:4]) if node.get("key_points") else "结合时间、地点、人物与历史意义整体理解这一节点。"
    return (
        f"《{title}》展项讲解稿\n\n"
        f"{audience}，下面我们围绕“{title}”展开讲解。"
        f"{summary or '这一节点处在长征主线的重要位置，是理解战略转移、路线调整与革命精神的重要入口。'}\n\n"
        f"首先看历史背景。{background or '在敌强我弱、形势严峻的条件下，红军必须在保存革命力量与打开新局面之间作出关键抉择。'}\n\n"
        f"再看事件经过。{process or '红军在这一阶段完成了关键行动，并通过严密组织与顽强斗争推动主线继续向前发展。'}\n\n"
        f"从人物线索看，本节点涉及{figures}等重要人物，他们在组织、判断、执行和统一思想等方面发挥了关键作用。\n\n"
        f"最后看历史意义。{significance or '这一节点不仅影响了长征的进程，也深化了党对革命道路、战略方向和群众力量的认识。'}\n\n"
        f"如果把它放回整条长征主线中理解，最值得把握的要点包括：{key_points}"
    )


def build_long_march_story_script() -> str:
    """生成首页可直接展示的《长征故事》总讲解稿。"""
    ruijin = get_route_node_data("ruijin_departure") or {}
    xiangjiang = get_route_node_data("xiangjiang_battle") or {}
    zunyi = get_route_node_data("zunyi_meeting") or {}
    chishui = get_route_node_data("sidu_chishui") or {}
    luding = get_route_node_data("luding_bridge") or {}
    huining = get_route_node_data("huining_meeting") or {}
    return (
        "《长征故事》总讲解稿\n\n"
        f"长征不是一次普通行军，而是在中国革命面临严重危机时作出的一次伟大战略转移。"
        f"{ruijin.get('summary', '1934年，中央红军从中央苏区出发，踏上保存革命力量、寻求新局面的艰难征程。')}"
        f"从瑞金、于都河到突破封锁线，红军在极端复杂的形势下艰难前行，"
        f"{xiangjiang.get('summary', '湘江战役的巨大牺牲，使部队和党中央深刻认识到原有行动方式已难以继续。')}\n\n"
        f"正是在这样的生死关头，通道转兵、黎平会议、猴场会议逐步酝酿出新的方向，"
        f"{zunyi.get('summary', '遵义会议由此成为长征乃至中国革命历史上的重要转折点。')}"
        f"此后，红军在运动战中不断摆脱围追堵截，"
        f"{chishui.get('summary', '四渡赤水集中体现了灵活机动、避实击虚的战略智慧。')}"
        f"{luding.get('summary', '强渡大渡河、飞夺泸定桥则进一步展现了红军在险境中敢打敢拼的英雄气概。')}\n\n"
        f"翻越雪山、穿越草地以后，长征进入最艰苦也最能体现信念与意志的阶段。"
        f"{huining.get('summary', '最终，红军在陕甘地区立足，并实现会宁会师，宣告长征取得伟大胜利。')}"
        "长征留给后人的，不只是一路行军的故事，更是理想信念、实事求是、顾全大局、依靠群众和百折不挠精神的集中体现。"
    )


def build_chapter_story_script(chapter_id: str) -> str:
    """围绕单个篇章生成首页可直接展示的讲述稿。"""
    chapter = next((item for item in get_route_chapters() if item.get("id") == chapter_id), None)
    if not chapter:
        return build_long_march_story_script()

    nodes = chapter.get("nodes", []) or []
    if not nodes:
        return build_long_march_story_script()

    lead_node = nodes[0]
    turning_node = nodes[min(1, len(nodes) - 1)]
    closing_node = nodes[-1]
    node_titles = "、".join(node.get("title", "") for node in nodes[:4] if node.get("title"))
    return (
        f"《{chapter.get('title', '长征篇章')}》篇章讲述\n\n"
        f"{chapter.get('subtitle', '')}"
        f"{lead_node.get('summary', '') or '这一篇章呈现长征主线中的关键阶段。'}\n\n"
        f"沿着这一篇章继续看，可以重点把握{node_titles or lead_node.get('title', '关键节点')}等节点。"
        f"{turning_node.get('background', '') or turning_node.get('summary', '')}\n\n"
        f"从行动推进来看，{closing_node.get('process', '') or closing_node.get('summary', '')}"
        f"把这些节点连起来看，更容易理解这一阶段为什么会成为长征主线中的重要转折。"
        f"{closing_node.get('significance', '') or '这一篇章既展现了红军在危局中的判断与行动，也展现了长征精神在具体历史场景中的形成过程。'}"
    )


def get_storytelling_tracks() -> List[Dict[str, Any]]:
    """返回首页和速览页共用的长征故事讲述入口。"""
    chapters = get_route_chapters()
    tracks: List[Dict[str, Any]] = [
        {
            "id": "overall_story",
            "title": "全线总讲述",
            "subtitle": "从瑞金出发到会宁会师，先把整条长征主线听完整。",
            "script": build_long_march_story_script(),
            "chapter_id": chapters[0].get("id", "") if chapters else "",
            "lead_node_id": "ruijin_departure",
            "questions": [
                "长征为什么要开始？",
                "为什么说长征是战略转移的伟大胜利？",
                "长征精神包括哪些核心内涵？",
            ],
        }
    ]
    for chapter in chapters:
        nodes = chapter.get("nodes", []) or []
        tracks.append(
            {
                "id": str(chapter.get("id", "")),
                "title": str(chapter.get("title", "") or "主线篇章"),
                "subtitle": str(chapter.get("subtitle", "") or ""),
                "script": build_chapter_story_script(str(chapter.get("id", ""))),
                "chapter_id": str(chapter.get("id", "")),
                "lead_node_id": str(nodes[0].get("id", "")) if nodes else "",
                "questions": build_node_related_questions(nodes[0], limit=3) if nodes else get_recommended_questions(limit=3),
            }
        )
    return tracks


def load_all_knowledge_items() -> List[Dict[str, Any]]:
    """汇总全部知识卡片。"""
    items: List[Dict[str, Any]] = []
    items.extend(load_route_nodes_data())
    items.extend(load_events_data())
    items.extend(load_figures_data())
    items.extend(load_places_data())
    items.extend(load_spirit_topics())
    items.extend(load_faq_items())
    return items


def clear_content_caches() -> None:
    """清理内容缓存，便于后台修改后即时生效。"""
    load_image_map.cache_clear()
    load_route_nodes_data.cache_clear()
    load_figures_data.cache_clear()
    load_events_data.cache_clear()
    load_places_data.cache_clear()
    load_spirit_topics.cache_clear()
    load_faq_items.cache_clear()
