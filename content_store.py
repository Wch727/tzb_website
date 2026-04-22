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


def build_figure_story_script(figure: Dict[str, Any]) -> str:
    """为人物专题页生成正式讲解稿。"""
    title = str(figure.get("title", "") or "重要人物")
    role = str(figure.get("role", "") or "党的重要领导人")
    summary = str(figure.get("summary", "") or "").strip()
    background = str(figure.get("background", "") or "").strip()
    long_march_role = str(figure.get("long_march_role", "") or "").strip()
    significance = str(figure.get("significance", "") or "").strip()
    return (
        f"《{title}》人物专题讲解稿\n\n"
        f"{title}是{role}。{summary}\n\n"
        f"从人物经历与历史背景看，{background or '他在中国革命的关键阶段承担了重要责任，并在党的历史发展中留下了深刻印记。'}\n\n"
        f"从长征主线看，{long_march_role or '他在长征中的重要作用，主要体现在关键节点中的领导、组织、判断与行动推进。'}\n\n"
        f"从历史贡献看，{significance or '理解这一人物，有助于把长征放回中国共产党领导中国革命的整体历史进程中加以把握。'}"
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
