"""剧情关卡与多媒体答题引擎。"""

from __future__ import annotations

from typing import Any, Dict, List

from activity_manager import get_activity
from content_store import build_chapter_story_script, get_chapter_for_node, get_route_node_data, load_route_nodes_data
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
        "mission_prompt": "请先读材料，再结合图片判断湘江战役为什么会推动长征由被动突围走向战略反思。",
        "material_title": "材料研读：湘江血战与转折压力",
        "material_points": [
            "材料一：湘江战役中，红军为掩护中央机关和主力纵队渡江，在全州、兴安、灌阳一带进行艰苦阻击，付出重大牺牲。",
            "材料二：战役后，党和红军内部对长征初期的军事指挥、行军组织和路线选择进行了更深反思。",
            "设问角度：从“战役结果—问题暴露—后续转折”三层关系理解湘江战役。",
        ],
        "custom_question": "依据材料，若从历史解释角度分析湘江战役，下列判断最准确的是？",
        "custom_options": [
            "A. 湘江战役的意义只在于它是一场局部军事胜利，与后续路线调整关系不大",
            "B. 湘江战役说明红军只要继续沿原计划硬冲，就能自然摆脱敌军合围",
            "C. 湘江战役以沉重代价暴露了原有军事指导和行动方式的问题，推动党和红军加快战略反思",
            "D. 湘江战役主要说明自然地理条件决定战争结果，人的组织与决策作用并不明显",
        ],
        "custom_answer": "C. 湘江战役以沉重代价暴露了原有军事指导和行动方式的问题，推动党和红军加快战略反思",
        "custom_explanation": "这道题考查的不是“湘江战役很惨烈”这一事实记忆，而是要求把材料中的战役结果、问题暴露和后续转折联系起来。湘江战役使红军遭受重大损失，也使原有行军组织和军事指导中的问题更加集中地显现出来。正是在这种压力下，通道转兵、黎平会议、猴场会议和遵义会议前后的反思与调整才更容易被理解。C项能把军事事件放回长征转折链条中分析，符合材料题的历史解释要求。",
    },
    "zunyi_meeting": {
        "question_type": "情境选择题",
        "mission_prompt": "请根据会议材料判断：遵义会议为什么能够成为长征和中国革命史上的关键转折。",
        "material_title": "会议材料辨析：危局中的纠错与调整",
        "material_points": [
            "材料一：湘江战役后，中央红军处境严峻，党内对第五次反“围剿”和长征初期军事指挥问题的反思不断加深。",
            "材料二：通道转兵、黎平会议、猴场会议连续调整行动方向和领导方式，为遵义会议集中解决问题创造了条件。",
            "设问角度：会议不是孤立事件，要把它放在“危局—反思—纠错—行动”的链条中理解。",
        ],
        "custom_question": "依据材料，关于遵义会议历史作用的理解，最符合高中历史材料题要求的是？",
        "custom_options": [
            "A. 遵义会议的作用主要在于确定了长征最终会师地点",
            "B. 遵义会议集中纠正军事和组织上的错误，使党和红军在危急关头形成新的领导和指挥格局",
            "C. 遵义会议只是一次普通行军会议，对后续四渡赤水、巧渡金沙江等行动没有影响",
            "D. 遵义会议说明长征胜利完全取决于地理路线选择，与党的领导和组织调整无关",
        ],
        "custom_answer": "B. 遵义会议集中纠正军事和组织上的错误，使党和红军在危急关头形成新的领导和指挥格局",
        "custom_explanation": "材料把遵义会议放在湘江战役后的危局和连续会议调整之中，提示我们不能孤立记忆会议名称。遵义会议的重要性在于，它集中讨论军事和组织问题，纠正此前错误军事指导，在危急关头推动形成新的领导和指挥格局。正因为有这样的调整，红军此后才能在四渡赤水、巧渡金沙江等行动中更加主动灵活。B项同时回应了会议背景、会议内容和历史影响，是最完整的判断。",
    },
    "sidu_chishui": {
        "question_type": "地图纠错",
        "mission_prompt": "请结合路线变化判断：四渡赤水的“来回机动”到底是被动绕路，还是主动调动敌军。",
        "material_title": "地图材料辨析：路线变化与战略主动",
        "material_points": [
            "材料一：遵义会议后，中央红军在川黔滇边多次转向、渡河、回师，敌军主力多次被调动到错误方向。",
            "材料二：红军通过佯动、急行、回师等方式，在运动中寻找战机，最终为巧渡金沙江创造条件。",
            "设问角度：判断路线变化时，不能只看“绕了几次”，还要看它是否改变了敌我态势。",
        ],
        "custom_question": "依据材料和地图逻辑，下列对四渡赤水的判断最准确的是？",
        "custom_options": [
            "A. 四渡赤水说明红军缺乏明确方向，只能在赤水河两岸被动徘徊",
            "B. 四渡赤水的关键在于以灵活机动调动敌军、避实击虚，从被动局面中争取战略主动",
            "C. 四渡赤水主要依靠兵力优势取胜，与指挥判断和路线设计关系不大",
            "D. 四渡赤水只是一次渡河行动，不能体现遵义会议后指挥方式的变化",
        ],
        "custom_answer": "B. 四渡赤水的关键在于以灵活机动调动敌军、避实击虚，从被动局面中争取战略主动",
        "custom_explanation": "四渡赤水最容易被误解为路线反复，但材料强调的是“路线变化造成的战略效果”。红军并不是盲目绕路，而是在敌军重兵之间不断改变方向，利用佯动、急行和回师调动敌人，使敌军判断失误，红军则在运动中争取主动。它既体现了遵义会议后新的指挥气象，也为巧渡金沙江打开条件。B项抓住了地图材料背后的历史逻辑。",
    },
    "luding_bridge": {
        "question_type": "看图识史",
        "mission_prompt": "请结合桥梁场景、河谷地形和行军节奏，判断飞夺泸定桥为什么成为经典战例。",
        "material_title": "图文材料辨析：天险、时间与突击",
        "material_points": [
            "材料一：泸定桥横跨大渡河，两岸山高水急，桥板被拆后，只剩铁索横悬江上。",
            "材料二：红军必须抢在敌军完成封锁前夺桥，才能打开继续北上的通道。",
            "设问角度：这一战例既要看战术突击，也要看它对整条北上路线的影响。",
        ],
        "custom_question": "依据材料，对飞夺泸定桥历史价值的分析最完整的是？",
        "custom_options": [
            "A. 它只是一次个人英雄行为，与红军北上路线和战略突破没有直接联系",
            "B. 它主要说明桥梁建筑结构特殊，历史意义集中在交通工程层面",
            "C. 它在战术上体现英勇突击，在战略上打开大渡河北上通道，集中呈现红军敢于胜利的精神",
            "D. 它说明红军已经没有任何敌情压力，因此能够轻松通过大渡河",
        ],
        "custom_answer": "C. 它在战术上体现英勇突击，在战略上打开大渡河北上通道，集中呈现红军敢于胜利的精神",
        "custom_explanation": "飞夺泸定桥不能只当作惊险故事来讲。材料提示了三个层次：桥本身是天险，时间上必须抢在敌军封锁完成前行动，结果上关系到红军继续北上的通道。因此，最完整的分析要同时看到战术突击、战略突破和精神象征。C项把“桥”“河”“时间”“路线”连成一个整体，既解释了为什么难，也解释了为什么重要。",
    },
    "snow_mountains": {
        "question_type": "听音辨曲",
        "mission_prompt": "请先播放音频线索，再结合雪山行军处境判断其精神内涵。",
        "material_title": "材料研读：诗句、环境与精神力量",
        "material_points": ["诗句写的是红军面对万水千山时的精神状态。", "判断时要把诗句中的乐观表达与雪山行军的低温、缺氧、缺粮处境联系起来。"],
        "audio_text": "红军不怕远征难，万水千山只等闲。更喜岷山千里雪，三军过后尽开颜。",
        "custom_question": "请先播放音频线索。若把这段诗句与翻越雪山的历史处境结合起来，最合理的理解是？",
        "custom_options": [
            "A. 诗句主要说明自然条件决定历史发展，人的主观努力并不重要",
            "B. 诗句只是在描写山水景色，与长征精神没有关系",
            "C. 诗句体现了革命理想、组织纪律和乐观主义对极端环境的支撑",
            "D. 诗句说明红军已经完全没有物质困难",
        ],
        "custom_answer": "C. 诗句体现了革命理想、组织纪律和乐观主义对极端环境的支撑",
        "custom_explanation": "这道题不能只把诗句当作文学描写来理解。把它放回翻越雪山的历史处境中，低温、缺氧、缺粮等困难越突出，诗句中的乐观表达和坚定信念越能显示精神力量。C项把文本内容、历史环境和长征精神联系起来，符合材料分析题的思路。",
    },
}

TACTIC_LIBRARY: Dict[str, List[Dict[str, Any]]] = {
    "scout": [
        {
            "id": "route_probe",
            "title": "前出侦察",
            "desc": "优先判断路线、地形与敌情变化，适合地图、路线和战场识别类关卡。",
            "match_types": ["地图纠错", "看图识史"],
            "match_stages": ["突围", "转折", "突破"],
        },
        {
            "id": "concealed_move",
            "title": "隐蔽机动",
            "desc": "重视掩护、迂回与避实击虚，适合敌强我弱、需要保存主力的场景。",
            "match_types": ["情境选择题"],
            "match_stages": ["突围", "调整"],
        },
        {
            "id": "terrain_lock",
            "title": "地形锁定",
            "desc": "先抓关键通道、桥梁和渡口，适合泸定桥、金沙江、大渡河等节点。",
            "match_types": ["看图识史", "地图纠错"],
            "match_stages": ["突破", "会师"],
        },
    ],
    "medic": [
        {
            "id": "rescue_cover",
            "title": "伤员掩护",
            "desc": "优先考虑减轻伤亡、维持队伍秩序，适合艰苦环境和情境判断类关卡。",
            "match_types": ["情境选择题", "听音辨曲"],
            "match_stages": ["突围", "会师"],
        },
        {
            "id": "supply_stabilize",
            "title": "补给稳队",
            "desc": "先看粮草、体力和队伍承压能力，适合雪山草地等艰难节点。",
            "match_types": ["情境选择题"],
            "match_stages": ["会师", "突破"],
        },
        {
            "id": "morale_support",
            "title": "军心鼓舞",
            "desc": "强调精神动员和互助支撑，适合体现长征精神的节点。",
            "match_types": ["听音辨曲", "情境选择题"],
            "match_stages": ["调整", "会师"],
        },
    ],
    "signal": [
        {
            "id": "relay_orders",
            "title": "快速传令",
            "desc": "优先保证命令传达和行动统一，适合会议转折、关键决策类节点。",
            "match_types": ["情境选择题", "看图识史"],
            "match_stages": ["转折", "调整"],
        },
        {
            "id": "coordination_first",
            "title": "协同统筹",
            "desc": "重视前后衔接与队伍配合，适合战役推进和跨节点联动作战。",
            "match_types": ["地图纠错", "情境选择题"],
            "match_stages": ["突破", "会师"],
        },
        {
            "id": "decision_focus",
            "title": "决策聚焦",
            "desc": "先抓会议和路线调整中的核心判断，适合理解决策转折的关卡。",
            "match_types": ["看图识史", "情境选择题"],
            "match_stages": ["转折"],
        },
    ],
    "quartermaster": [
        {
            "id": "supply_count",
            "title": "盘点粮草",
            "desc": "先估算队伍消耗和补给压力，适合雪山草地、长途转移和艰苦环境类关卡。",
            "match_types": ["情境选择题", "听音辨曲"],
            "match_stages": ["会师", "突破"],
        },
        {
            "id": "speed_supply",
            "title": "轻装急行",
            "desc": "在补给不足时优先判断何处必须快速通过，适合渡河、突围和行军节奏类节点。",
            "match_types": ["地图纠错", "情境选择题"],
            "match_stages": ["突围", "突破"],
        },
        {
            "id": "reserve_line",
            "title": "保留余粮",
            "desc": "把风险留给最关键路段之前消化，适合连续作战和远距离推进场景。",
            "match_types": ["情境选择题"],
            "match_stages": ["调整", "会师"],
        },
    ],
    "political": [
        {
            "id": "morale_rally",
            "title": "鼓舞军心",
            "desc": "先判断节点体现的理想信念、纪律和群众路线，适合精神专题与意义判断类题目。",
            "match_types": ["听音辨曲", "情境选择题"],
            "match_stages": ["会师", "转折"],
        },
        {
            "id": "mass_work",
            "title": "群众工作",
            "desc": "关注群众支援、纪律执行和军民关系，适合于都河、沿途支前等节点。",
            "match_types": ["情境选择题"],
            "match_stages": ["突围", "调整"],
        },
        {
            "id": "meaning_focus",
            "title": "提炼意义",
            "desc": "把事件经过转化为历史意义，适合会议、会师和关键转折节点。",
            "match_types": ["看图识史", "情境选择题"],
            "match_stages": ["转折", "会师"],
        },
    ],
    "engineer": [
        {
            "id": "bridge_assault",
            "title": "夺桥开路",
            "desc": "优先判断桥梁、渡口和通道控制权，适合泸定桥、大渡河等突破关卡。",
            "match_types": ["看图识史", "地图纠错"],
            "match_stages": ["突破"],
        },
        {
            "id": "river_crossing",
            "title": "测渡通行",
            "desc": "判断渡河条件和敌我位置，适合金沙江、于都河等渡河节点。",
            "match_types": ["地图纠错", "情境选择题"],
            "match_stages": ["突围", "突破"],
        },
        {
            "id": "route_clear",
            "title": "清障开路",
            "desc": "面对山地、草地和险道时先判断通行条件，适合复杂地形类关卡。",
            "match_types": ["情境选择题", "看图识史"],
            "match_stages": ["会师", "突破"],
        },
    ],
}

BOSS_NODE_IDS = {
    "xiangjiang_battle",
    "zunyi_meeting",
    "sidu_chishui",
    "luding_bridge",
    "huining_meeting",
}

BOSS_STAGE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "xiangjiang_battle": {
        "label": "章节攻坚关",
        "title": "湘江血战：生死突围",
        "lead": "这是长征初期最惨烈的一场硬仗。队伍必须在巨大牺牲中保住主力，才能继续把革命火种带向前方。",
        "focus": "这一关要看清的，不只是战斗本身，而是湘江血战怎样把战略转折逼到了历史关口。",
        "orders": ["先判断为什么湘江会成为生死关口。", "再理解巨大牺牲为何推动后续路线调整。", "把湘江放回遵义会议前夜来理解。"],
        "stakes": "如果看不清这一关，就很难理解长征为什么必须从被动突围走向战略转折。",
    },
    "zunyi_meeting": {
        "label": "章节攻坚关",
        "title": "遵义会议：转折前夜",
        "lead": "这里不是一场普通会议，而是长征从危局中转向主动的重要起点。许多后续胜利，都要从这里追溯。",
        "focus": "这一关重点不在记住会议名称，而在理解为什么它能成为中国革命历史上的伟大转折。",
        "orders": ["先看湘江之后的危局。", "再看会议改变了什么。", "最后把它与四渡赤水等后续行动连起来。"],
        "stakes": "如果对这次会议理解太薄，后面所有“为什么能扭转局势”的问题都会变得空泛。",
    },
    "sidu_chishui": {
        "label": "章节攻坚关",
        "title": "四渡赤水：机动制胜",
        "lead": "这是长征途中最能体现战略机动的一段。红军并不是盲目转移，而是在复杂围追堵截中主动调动敌军。",
        "focus": "这一关要理解的核心，是‘机动’怎样成为摆脱被动、争取主动的关键智慧。",
        "orders": ["先看红军为什么不能硬碰硬。", "再看路线变化为什么不是混乱，而是主动设计。", "最后把‘运动战’和全局胜负联系起来。"],
        "stakes": "如果只把四渡赤水看成路线来回变化，就会错过这段历史最核心的战略价值。",
    },
    "luding_bridge": {
        "label": "章节攻坚关",
        "title": "飞夺泸定桥：抢占天险",
        "lead": "这不是一座普通的桥，而是一条生死通道。谁掌握了它，谁就掌握了北上的主动权。",
        "focus": "这一关要看清泸定桥为什么既是战术险关，也是整条长征主线上的关键突破口。",
        "orders": ["先判断桥梁与河谷地形的险要程度。", "再理解为什么必须争分夺秒。", "最后把它与大渡河整体突破联系起来。"],
        "stakes": "如果忽略这道天险背后的全局意义，就无法真正理解飞夺泸定桥为何成为经典战例。",
    },
    "huining_meeting": {
        "label": "终章攻坚关",
        "title": "会宁会师：长征胜利",
        "lead": "当队伍走到这里，长征不再只是一次艰难行军，而已经成为中国革命走向新阶段的伟大转折。",
        "focus": "这一关重点不是记住会师地点，而是理解会宁会师为什么意味着长征胜利完成。",
        "orders": ["先回望整条主线经历了哪些生死关口。", "再理解会师对于保存革命力量的意义。", "最后把长征胜利与长征精神联系起来。"],
        "stakes": "如果看不到会师背后的历史意义，就很难真正把长征理解为一次伟大的战略胜利。",
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
    payload["material_title"] = payload.get("material_title") or quiz.get("material_title") or "材料研读"
    payload["material_points"] = payload.get("material_points") or quiz.get("material_points") or []
    return payload


def _build_tactic_package(role: Dict[str, Any], node: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """生成本关行动策略。"""
    options = TACTIC_LIBRARY.get(role.get("role_id", "scout"), TACTIC_LIBRARY["scout"])
    route_stage = str(node.get("route_stage", "") or "")
    recommended = options[0]
    for item in options:
        stage_hit = any(key and key in route_stage for key in item.get("match_stages", []))
        type_hit = question_type in item.get("match_types", [])
        if stage_hit or type_hit:
            recommended = item
            break
    return {
        "options": options,
        "recommended_id": recommended.get("id", ""),
        "recommended_title": recommended.get("title", ""),
        "recommended_reason": recommended.get("desc", ""),
    }


def _build_stage_briefing(node: Dict[str, Any], role: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    """生成更有剧情感的关卡简报。"""
    title = node.get("title", "长征节点")
    route_stage = node.get("route_stage", "主线阶段")
    summary = str(node.get("summary", "") or "").strip()
    background = str(node.get("background", "") or "").strip()
    process = str(node.get("process", "") or "").strip()
    significance = str(node.get("significance", "") or "").strip()
    opening = (
        f"你所在的小队正在进入“{title}”关卡。此时长征处于“{route_stage}”阶段，"
        f"{summary or '队伍必须在复杂局势中完成判断与推进。'}"
    )
    mission_goals = [
        f"先把握“{title}”发生时的核心处境，而不是只记住结果。",
        f"结合本关的“{question_type}”线索，判断行动逻辑和历史转折。",
        f"以{role.get('name', '侦察兵')}身份完成任务，并争取额外战术奖励。",
    ]
    battle_log = [
        background[:90] + ("..." if len(background) > 90 else "") if background else "先看敌我处境和行军环境。",
        process[:90] + ("..." if len(process) > 90 else "") if process else "再看行动如何推进，关键步骤发生了什么。",
        significance[:90] + ("..." if len(significance) > 90 else "") if significance else "最后回到整条长征主线，理解这一节点的意义。",
    ]
    risk_hint = "如果判断失误，将错过本关的历史转折线索，并影响小队贡献与连续作战节奏。"
    reward_hint = "答对基础题可获得红星积分与粮草；若行动策略匹配本关特征，还能获得额外奖励。"
    return {
        "opening": opening,
        "mission_goals": mission_goals,
        "battle_log": battle_log,
        "risk_hint": risk_hint,
        "reward_hint": reward_hint,
    }


def _build_stage_story_pack(
    state: Dict[str, Any],
    node: Dict[str, Any],
    role: Dict[str, Any],
    question_type: str,
    chapter: Dict[str, Any],
) -> Dict[str, Any]:
    """为关卡补充更有行军叙事感的故事层。"""
    title = str(node.get("title", "") or "长征节点")
    route_stage = str(node.get("route_stage", "") or chapter.get("title", "主线推进"))
    date = str(node.get("date", "") or "长征途中")
    place = str(node.get("place", "") or "行军沿线")
    role_name = str(role.get("name", "") or "侦察兵")
    summary = str(node.get("summary", "") or "").strip()
    background = str(node.get("background", "") or "").strip()
    process = str(node.get("process", "") or "").strip()
    significance = str(node.get("significance", "") or "").strip()
    figures = [str(item).strip() for item in node.get("figures", []) if str(item).strip()]
    figure_text = "、".join(figures[:4]) if figures else "红军指战员与党的重要领导人"
    current_step = int(state.get("current_index", 0)) + 1
    total_steps = len(state.get("node_ids", []))
    node_ids = list(state.get("node_ids", []))
    next_node = {}
    if current_step < total_steps:
        next_node = get_route_node_data(node_ids[current_step]) or {}
    next_title = str(next_node.get("title", "") or "下一阶段主线节点")

    opening = (
        f"{date}，队伍推进到{place}一带。你以{role_name}身份进入“{title}”这一关。"
        f"这是长征“{route_stage}”阶段中的第 {current_step} 关，整条主线仍在持续向前。"
    )
    situation = (
        background
        or "红军正处在敌强我弱、补给紧张、行军环境艰难的局势之中，每一次判断都关系到主力能否继续前进。"
    )
    scene = (
        process
        or "队伍在复杂地形和严密封锁之间寻找生路，既要保存有生力量，又要迅速打开新的战略空间。"
    )
    decision = (
        f"在这一关里，你要理解的不只是“发生了什么”，更要看清为什么必须这样行动。"
        f"围绕{figure_text}等人物的判断与组织，红军在此作出了关键抉择。"
    )
    meaning = (
        significance
        or "把这一节点放回整条长征主线中，它既是一次具体行动，也是理解长征为什么能够由被动转向主动的重要线索。"
    )
    next_hook = f"一旦完成本关，主线将继续向“{next_title}”推进，新的风险与新的机会也会随之出现。"
    story_script = (
        f"《{title}》关前故事\n\n"
        f"开场导入\n{opening}\n\n"
        f"行军处境\n{situation}\n\n"
        f"现场推进\n{scene}\n\n"
        f"关键抉择\n{decision}\n\n"
        f"这一关的意义\n{meaning}\n\n"
        f"继续前进\n{next_hook}"
    )
    story_panels = [
        {"title": "这一刻身在何处", "desc": f"{date} · {place} · {route_stage}"},
        {"title": "队伍面临什么局势", "desc": situation},
        {"title": "这一关真正要看什么", "desc": f"以“{question_type}”为线索，把节点放回主线推进中理解。"},
        {"title": "接下来会走向哪里", "desc": next_hook},
    ]
    return {
        "story_script": story_script,
        "story_panels": story_panels,
        "story_opening": opening,
        "story_next_hook": next_hook,
    }


def _build_boss_stage_pack(
    node: Dict[str, Any],
    role: Dict[str, Any],
    chapter: Dict[str, Any],
) -> Dict[str, Any]:
    """为关键大关生成专属过场信息。"""
    node_id = str(node.get("id", "") or "")
    if node_id not in BOSS_NODE_IDS:
        return {}
    override = BOSS_STAGE_OVERRIDES.get(node_id, {})
    title = str(node.get("title", "") or "关键节点")
    route_stage = str(node.get("route_stage", "") or chapter.get("title", "主线篇章"))
    role_name = str(role.get("name", "") or "侦察兵")
    summary = str(node.get("summary", "") or "").strip()
    return {
        "label": str(override.get("label", "章节攻坚关")),
        "title": str(override.get("title", title)),
        "lead": str(
            override.get(
                "lead",
                f"“{title}”是长征主线中的关键大关。此时队伍已进入“{route_stage}”阶段，必须完成更高强度的判断与推进。"
            )
        ),
        "focus": str(
            override.get(
                "focus",
                summary or f"这一关不只是答题，更要看清“{title}”在长征主线中的决定性意义。"
            )
        ),
        "orders": list(override.get("orders", [])) or [
            f"以{role_name}身份先理解本关局势，再进入作答。",
            f"把“{title}”放回“{route_stage}”阶段来判断。",
            "不要只记结论，更要看清它为什么能改变主线推进。",
        ],
        "stakes": str(
            override.get(
                "stakes",
                f"如果这一关理解过浅，后续整条主线的转折与推进逻辑都会变得单薄。"
            )
        ),
    }


def _build_boss_stage_outcome(
    node: Dict[str, Any],
    next_node: Dict[str, Any],
    correct: bool,
    tactic_match: bool,
) -> Dict[str, Any]:
    """为关键大关生成专属结算语。"""
    node_id = str(node.get("id", "") or "")
    if node_id not in BOSS_NODE_IDS:
        return {}
    override = BOSS_STAGE_OVERRIDES.get(node_id, {})
    title = str(node.get("title", "") or "关键大关")
    next_title = str(next_node.get("title", "") or "下一节点")
    significance = str(node.get("significance", "") or "").strip()
    if correct and tactic_match:
        lead = f"你已经攻下“{title}”这一关键大关，而且行动判断与战术选择同时命中，队伍由此获得更稳定的推进节奏。"
        focus = significance or "这意味着你不仅记住了结论，更真正理解了这一关为什么会改变整条主线的走向。"
        closing = f"完成这道大关后，主线将继续转入“{next_title}”，而这一胜利会成为后续推进的关键基础。"
    elif correct:
        lead = f"“{title}”这道关键大关已经完成，历史判断总体正确，主线得以继续向前。"
        focus = significance or "你已经抓住了这道大关的核心意义，但在战术层面的理解还可以进一步贴近当时的局势。"
        closing = f"接下来队伍将进入“{next_title}”，建议带着这关的历史结论继续往后看。"
    else:
        lead = f"“{title}”这道关键大关没有完全攻下，但这正说明它本身就是长征主线中最值得反复理解的转折节点。"
        focus = significance or "这类大关的价值，不在于背出一个答案，而在于把它放回整条长征主线里重新理解。"
        closing = f"整理完复盘后，队伍仍将向“{next_title}”推进，但最好先把这道大关真正看透。"
    return {
        "label": str(override.get("label", "章节攻坚关")),
        "title": str(override.get("title", title)),
        "lead": lead,
        "focus": focus,
        "closing": closing,
    }


def _build_battle_outcome(
    *,
    node: Dict[str, Any],
    next_node: Dict[str, Any],
    role: Dict[str, Any],
    correct: bool,
    tactic_match: bool,
) -> Dict[str, Any]:
    """生成作战结果反馈。"""
    node_title = node.get("title", "当前节点")
    next_title = next_node.get("title", "下一节点") if next_node else "终点会师"
    role_name = role.get("name", "侦察兵")
    if correct and tactic_match:
        summary = f"{role_name}在“{node_title}”关卡中判断准确，且本关行动策略与场景高度匹配，你不仅完成了作答，还为小队争取到了更稳的推进节奏。"
        bullets = [
            "你抓住了本关最关键的历史线索，没有把节点理解停留在表层事实。",
            "战术选择与关卡环境匹配，获得额外红星积分与粮草奖励。",
            f"队伍可继续向“{next_title}”推进，保持连续作战优势。",
        ]
    elif correct:
        summary = f"{role_name}顺利完成了“{node_title}”关卡作答，历史判断是准确的，但如果行动策略与关卡环境更贴合，还能获得更高奖励。"
        bullets = [
            "本关基础判断正确，主线任务已推进。",
            "战术思路仍有优化空间，下次可结合关卡类型选择更合适的方案。",
            f"下一步建议把注意力转向“{next_title}”的处境与任务变化。",
        ]
    else:
        summary = f"{role_name}在“{node_title}”关卡未能完全命中关键判断，本关内容已进入错题复盘，建议回到背景和过程线索重新梳理。"
        bullets = [
            "本关失误不会阻断主线，但会影响连续作战奖励。",
            "可先看解析与历史小课堂，再重新理解这一步为何重要。",
            f"继续前进前，建议把“{node_title}”与“{next_title}”的衔接关系先看清楚。",
        ]
    return {"summary": summary, "bullets": bullets}


def _build_continuation_story(
    node: Dict[str, Any],
    next_node: Dict[str, Any],
    role: Dict[str, Any],
    correct: bool,
) -> str:
    """生成作答后的行军续报。"""
    title = str(node.get("title", "") or "当前节点")
    next_title = str(next_node.get("title", "") or "下一节点")
    role_name = str(role.get("name", "") or "侦察兵")
    process = str(node.get("process", "") or "").strip()
    significance = str(node.get("significance", "") or "").strip()
    if correct:
        return (
            f"《{title}》行军续报\n\n"
            f"本关完成后，{role_name}所在小队顺利通过了“{title}”这一节点的关键判断。"
            f"{process or '这意味着队伍没有停留在表层事实，而是真正理解了这一阶段行动为什么必须如此推进。'}\n\n"
            f"继续放回主线看，{significance or '这一关的意义，在于它帮助队伍稳住方向，把一次局部行动转化为整条长征主线上的连续推进。'}\n\n"
            f"接下来，队伍将把注意力转向“{next_title}”。新的行军处境已经展开，前方仍然需要判断、组织与坚持。"
        )
    return (
        f"《{title}》行军续报\n\n"
        f"这一关的判断没有完全命中关键点，但队伍不会因此停下。"
        f"{process or '长征中的许多转折，本就不是靠记住一个结果就能看懂，而是要回到当时的局势、路线与行动逻辑中重新理解。'}\n\n"
        f"只要把这一步重新看清，{significance or '就能更好地理解这关为什么会成为后续主线推进的重要铺垫。'}\n\n"
        f"整理完本关复盘后，继续把目光投向“{next_title}”，主线仍会向前推进。"
    )


def _build_stage_meta(
    state: Dict[str, Any],
    node: Dict[str, Any],
    role: Dict[str, Any],
    question_type: str,
) -> Dict[str, Any]:
    """补充章节、难度与过场信息。"""
    chapter = get_chapter_for_node(node)
    node_id = str(node.get("id", "") or "")
    is_boss_stage = node_id in BOSS_NODE_IDS
    current_step = int(state.get("current_index", 0)) + 1
    total_steps = len(state.get("node_ids", []))

    difficulty_stars = 2
    if question_type in ["地图纠错", "看图识史"]:
        difficulty_stars += 1
    if is_boss_stage:
        difficulty_stars += 1
    if str(node.get("route_stage", "") or "") in ["转折", "突破", "会师"]:
        difficulty_stars += 1
    difficulty_stars = min(difficulty_stars, 5)

    key_points = list(node.get("key_points", []) or [])
    squad_orders = key_points[:3] if key_points else [
        "先判断节点在主线中的位置，再进入题目。",
        "留意人物、地点与路线变化之间的关系。",
        "把答案放回整条长征进程中理解。",
    ]
    next_hint = ""
    related_nodes = list(node.get("related_nodes", []) or [])
    if related_nodes:
        related_node = get_route_node_data(str(related_nodes[0])) or {}
        related_title = related_node.get("title", str(related_nodes[0]))
        next_hint = f"完成本关后，可继续关注“{related_title}”与当前节点的衔接关系。"
    elif chapter.get("nodes"):
        next_hint = f"完成本关后，建议继续沿“{chapter.get('title', '主线篇章')}”推进。"

    return {
        "chapter": chapter,
        "stage_badge": "章节攻坚关" if is_boss_stage else "主线推进关",
        "is_boss_stage": is_boss_stage,
        "difficulty_stars": difficulty_stars,
        "difficulty_label": "高强度关卡" if difficulty_stars >= 4 else "主线学习关",
        "campaign_title": f"{chapter.get('badge', '展项单元')} · {chapter.get('title', '长征主线')}",
        "prologue": (
            f"第 {current_step} 关 / 共 {total_steps} 关。"
            f"你正以{role.get('name', '侦察兵')}身份进入“{node.get('title', '长征节点')}”战役单元，"
            f"本关属于“{chapter.get('title', '主线篇章')}”篇章。"
        ),
        "squad_orders": squad_orders,
        "next_hint": next_hint,
    }


def _build_chapter_completion(
    chapter: Dict[str, Any],
    next_chapter: Dict[str, Any],
    progress: Dict[str, Any],
) -> Dict[str, Any]:
    """生成篇章结算信息。"""
    chapter_id = str(chapter.get("id", "") or "")
    chapter_title = str(chapter.get("title", "") or "主线篇章")
    next_title = str(next_chapter.get("title", "") or "会师终章")
    completed_count = len(progress.get("completed_chapters", []))
    return {
        "chapter_id": chapter_id,
        "title": chapter_title,
        "badge": str(chapter.get("badge", "") or "篇章结算"),
        "script": build_chapter_story_script(chapter_id),
        "reward_text": "阶段奖励：红星积分 +3，虚拟粮草 +2。",
        "completed_count": completed_count,
        "next_title": next_title,
        "next_subtitle": (
            f"下一阶段将进入“{next_title}”，建议带着本篇章的关键结论继续推进。"
            if next_chapter
            else "当前已完成全部长征主线篇章，接下来可进入最终结算与全线回顾。"
        ),
    }


def get_stage_package(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取当前关卡的完整展示数据。"""
    node = get_current_node(state)
    if not node:
        return {"node": {}, "finished": True}
    role = get_role(state.get("role_id", "scout"))
    payload = _question_payload(node)
    knowledge_cards = build_related_knowledge_bundle(node)
    tactic_package = _build_tactic_package(role, node, payload.get("question_type", "情境选择题"))
    briefing = _build_stage_briefing(node, role, payload.get("question_type", "情境选择题"))
    stage_meta = _build_stage_meta(state, node, role, payload.get("question_type", "情境选择题"))
    story_pack = _build_stage_story_pack(
        state,
        node,
        role,
        payload.get("question_type", "情境选择题"),
        stage_meta.get("chapter", {}),
    )
    boss_pack = _build_boss_stage_pack(node, role, stage_meta.get("chapter", {}))
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
        "tactic_options": tactic_package.get("options", []),
        "recommended_tactic_id": tactic_package.get("recommended_id", ""),
        "recommended_tactic_title": tactic_package.get("recommended_title", ""),
        "recommended_tactic_reason": tactic_package.get("recommended_reason", ""),
        "chapter": stage_meta.get("chapter", {}),
        "stage_badge": stage_meta.get("stage_badge", "主线推进关"),
        "is_boss_stage": stage_meta.get("is_boss_stage", False),
        "difficulty_stars": stage_meta.get("difficulty_stars", 3),
        "difficulty_label": stage_meta.get("difficulty_label", "主线学习关"),
        "campaign_title": stage_meta.get("campaign_title", "长征主线"),
        "prologue": stage_meta.get("prologue", ""),
        "squad_orders": stage_meta.get("squad_orders", []),
        "next_hint": stage_meta.get("next_hint", ""),
        "opening_brief": briefing.get("opening", ""),
        "mission_goals": briefing.get("mission_goals", []),
        "battle_log": briefing.get("battle_log", []),
        "risk_hint": briefing.get("risk_hint", ""),
        "reward_hint": briefing.get("reward_hint", ""),
        "story_script": story_pack.get("story_script", ""),
        "story_panels": story_pack.get("story_panels", []),
        "story_opening": story_pack.get("story_opening", ""),
        "story_next_hook": story_pack.get("story_next_hook", ""),
        "boss_stage": boss_pack,
        "progress": build_progress_summary(state.get("progress", {})),
        "current_step": int(state.get("current_index", 0)) + 1,
        "total_steps": len(state.get("node_ids", [])),
    }


def submit_stage_answer(state: Dict[str, Any], answer: str, tactic_id: str = "") -> Dict[str, Any]:
    """提交当前关卡答案。"""
    node = get_current_node(state)
    if not node:
        return {"state": state, "finished": True}

    stage = get_stage_package(state)
    expected_answer = str(stage.get("expected_answer", "") or "")
    correct = answer.strip() == expected_answer.strip()
    role = stage.get("role", {})
    current_chapter = stage.get("chapter", {}) or {}
    question_type = stage.get("question_type", "情境选择题")
    tactic_match = bool(tactic_id and tactic_id == stage.get("recommended_tactic_id", ""))
    bonus_stars = 0
    bonus_grain = 0
    if correct:
        if question_type == "地图纠错" and role.get("role_id") == "scout":
            bonus_grain += 2
        if question_type == "情境选择题" and role.get("role_id") == "medic":
            bonus_stars += 2
        if node.get("type") == "event" and role.get("role_id") == "signal":
            bonus_stars += 2
        if role.get("role_id") == "quartermaster" and question_type in ["情境选择题", "听音辨曲"]:
            bonus_grain += 2
        if role.get("role_id") == "political" and question_type in ["听音辨曲", "情境选择题"]:
            bonus_stars += 2
        if role.get("role_id") == "engineer" and question_type in ["地图纠错", "看图识史"]:
            bonus_stars += 1
            bonus_grain += 1
    role_mastery_key = ""
    if correct:
        if role.get("role_id") == "scout" and question_type in ["地图纠错", "看图识史"]:
            role_mastery_key = "scout"
        elif role.get("role_id") == "medic" and question_type in ["情境选择题", "听音辨曲"]:
            role_mastery_key = "medic"
        elif role.get("role_id") == "signal" and node.get("type") == "event":
            role_mastery_key = "signal"
        elif role.get("role_id") == "quartermaster" and question_type in ["情境选择题", "听音辨曲"]:
            role_mastery_key = "quartermaster"
        elif role.get("role_id") == "political" and question_type in ["听音辨曲", "情境选择题"]:
            role_mastery_key = "political"
        elif role.get("role_id") == "engineer" and question_type in ["地图纠错", "看图识史"]:
            role_mastery_key = "engineer"

    updated_state = state.copy()
    updated_state["history"] = list(state.get("history", []))
    updated_state["history"].append(
        {
            "node_id": node.get("id", ""),
            "title": node.get("title", ""),
            "question_type": question_type,
            "correct": correct,
            "selected_answer": answer,
            "selected_tactic": tactic_id,
        }
    )
    next_index = int(state.get("current_index", 0)) + 1
    node_ids = list(state.get("node_ids", []))
    predicted_next_node = get_route_node_data(node_ids[next_index]) if next_index < len(node_ids) else {}
    next_chapter = get_chapter_for_node(predicted_next_node) if predicted_next_node else {}
    chapter_completed = bool(
        current_chapter
        and current_chapter.get("id")
        and (not predicted_next_node or next_chapter.get("id") != current_chapter.get("id"))
    )
    if chapter_completed:
        bonus_stars += 3
        bonus_grain += 2
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
        tactic_match=tactic_match,
        chapter_completion_id=str(current_chapter.get("id", "")) if chapter_completed else "",
        collectible_rarity="传说" if node.get("id", "") in BOSS_NODE_IDS else "",
    )

    updated_state["current_index"] = next_index
    updated_state["finished"] = updated_state["current_index"] >= len(updated_state.get("node_ids", []))
    next_node = get_current_node(updated_state) if not updated_state["finished"] else {}
    next_chapter = get_chapter_for_node(next_node) if next_node else {}
    outcome = _build_battle_outcome(
        node=node,
        next_node=next_node,
        role=role,
        correct=correct,
        tactic_match=tactic_match,
    )
    progress_summary = build_progress_summary(updated_state.get("progress", {}))
    stage_rating = int(
        (progress_summary.get("level_stars", {}) or {}).get(node.get("id", ""), 0) or 0
    )
    review_manual = [
        {
            "title": "你的判断",
            "desc": f"你选择了：{answer or '未作答'}",
        },
        {
            "title": "标准答案",
            "desc": expected_answer or "当前未配置标准答案。",
        },
        {
            "title": "战术复盘",
            "desc": (
                "所选行动策略与本关环境匹配，战术加成已生效。"
                if tactic_match
                else f"本关更推荐采用“{stage.get('recommended_tactic_title', '默认推进')}”思路。"
            ),
        },
        {
            "title": "继续推进",
            "desc": stage.get("next_hint", "完成复盘后继续沿主线推进。"),
        },
    ]
    chapter_completion = (
        _build_chapter_completion(current_chapter, next_chapter, progress_summary)
        if chapter_completed
        else {}
    )
    reward_delta = {
        "score_delta": int(progress_summary.get("red_star_points", 0))
        - int(state.get("progress", {}).get("red_star_points", 0)),
        "grain_delta": int(progress_summary.get("grain", 0))
        - int(state.get("progress", {}).get("grain", 0)),
    }
    unlocked_card = {}
    if correct:
        unlocked_cards = progress_summary.get("unlocked_cards", []) or []
        unlocked_card = next(
            (
                item
                for item in reversed(unlocked_cards)
                if isinstance(item, dict) and item.get("node_id") == node.get("id", "")
            ),
            {},
        )
    return {
        "state": updated_state,
        "correct": correct,
        "feedback": "回答正确，已推进到下一关。" if correct else "本题未答对，已收录到错题复盘。",
        "answered_node": node,
        "next_node": next_node,
        "finished": updated_state["finished"],
        "role_feedback": build_role_feedback(role, correct, question_type),
        "tactic_match": tactic_match,
        "selected_tactic": tactic_id,
        "answer_detail": {
            "expected_answer": expected_answer,
            "explanation": stage.get("explanation", ""),
            "extended_note": stage.get("extended_note", ""),
            "question_type": question_type,
        },
        "battle_outcome": outcome.get("summary", ""),
        "after_action_report": outcome.get("bullets", []),
        "continuation_story": _build_continuation_story(node, next_node, role, correct),
        "boss_stage_outcome": _build_boss_stage_outcome(node, next_node, correct, tactic_match),
        "review_manual": review_manual,
        "chapter_completion": chapter_completion,
        "knowledge_cards": stage.get("knowledge_cards", []),
        "progress": progress_summary,
        "reward_delta": reward_delta,
        "unlocked_card": unlocked_card,
        "stage_rating": stage_rating,
    }
