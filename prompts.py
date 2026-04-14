"""统一管理 Prompt 模板。"""

from __future__ import annotations

from typing import Iterable


LONG_MARCH_GUIDE_ROLE_PROMPT = """
你是一名“长征史 AI 讲解员”，服务于党史教育、研学导览、比赛答辩与互动学习场景。
请始终使用正式、准确、清晰的中文回答，优先依据检索到的资料进行说明。
如果资料不足，请明确说明“当前知识库中相关信息有限”，不要编造历史事实。
所有回答默认输出完整段落，不要只给一句话。
""".strip()


def format_context_blocks(blocks: Iterable[str]) -> str:
    """把检索片段拼接为上下文。"""
    cleaned = [block.strip() for block in blocks if block and block.strip()]
    return "\n\n".join(f"[资料{i + 1}]\n{block}" for i, block in enumerate(cleaned))


def build_rag_qa_prompt(question: str, context: str) -> str:
    """RAG 问答 Prompt。"""
    return f"""
请基于给定资料回答用户关于《长征史》的问题。
要求：
1. 使用正式中文，适合展陈导览、课堂学习和比赛展示。
2. 回答长度控制在 220 到 380 字之间，不要只给摘要句。
3. 必须包含：历史背景、核心解释、历史意义或延伸理解。
4. 如果问题涉及节点，请尽量说明时间、地点、人物和影响。
5. 如果资料不足，也要优先整合已有事实形成完整段落，再说明信息有限。

用户问题：
{question}

参考资料：
{context}
""".strip()


def build_guide_script_prompt(topic: str, audience: str, duration: str, context: str) -> str:
    """长征讲解稿 Prompt。"""
    return f"""
请围绕“{topic}”生成一篇面向“{audience}”的《长征史》讲解稿。
要求：
1. 预计讲解时长约为 {duration}。
2. 正文控制在 300 到 450 字之间。
3. 必须包含：开场引入、历史背景、事件经过、历史意义、结尾升华。
4. 风格正式、庄重，适合比赛展示与现场导览。
5. 内容必须建立在参考资料基础上，避免空泛抒情。

参考资料：
{context}
""".strip()


def build_short_video_script_prompt(topic: str, audience: str, style: str, context: str) -> str:
    """长征短视频脚本 Prompt。"""
    return f"""
请围绕“{topic}”生成一份适合“{audience}”观看的《长征史》短视频脚本。
要求：
1. 风格为：{style}。
2. 输出结构必须包括：标题、开场、主体分镜、结尾总结。
3. 主体分镜不少于 3 段，整体适合 60 到 90 秒展示。
4. 每段都要有明确画面提示或旁白内容，不要只输出一句话。
5. 历史表达准确，不夸张、不戏说。

参考资料：
{context}
""".strip()


def build_game_summary_prompt(role: str, score: int, unlocked_nodes: str, context: str) -> str:
    """闯关结算总结 Prompt。"""
    return f"""
请为一位参加《长征史》互动闯关的用户生成学习总结。
用户身份：{role}
总分：{score}
已解锁节点：{unlocked_nodes}

要求：
1. 使用正式、鼓励式表达。
2. 总结用户已经掌握的历史要点。
3. 给出 2 到 3 个后续推荐学习主题。

参考资料：
{context}
""".strip()


def build_route_explain_prompt(node_title: str, role: str, context: str) -> str:
    """路线节点讲解 Prompt。"""
    return f"""
请面向“{role}”讲解长征路线节点“{node_title}”。
要求：
1. 控制在 300 到 450 字之间。
2. 必须包含：历史背景、事件经过、历史意义。
3. 风格正式、清晰，适合节点详情页与互动展项展示。
4. 如果资料有限，也要优先整合已有事实形成完整讲解。

参考资料：
{context}
""".strip()
