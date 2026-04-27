"""本地知识导览模型。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class MockProviderAdapter:
    """用于无 API Key 场景的本地知识导览 provider。"""

    provider_name = "mock"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def _build_context_summary(self, context_blocks: Optional[List[str]]) -> str:
        """将检索片段整理为导览摘要。"""
        if not context_blocks:
            return "当前未检索到足够资料，以下将依据内置知识卡作概括性说明。"
        previews = []
        for index, block in enumerate(context_blocks[:3], start=1):
            cleaned = block.replace("\n", " ").strip()
            previews.append(f"{index}. {cleaned[:90]}")
        return "知识库要点：\n" + "\n".join(previews)

    def _extract_user_question(self, user_message: str) -> str:
        """从 RAG Prompt 中提取真实用户问题，避免把整段提示词直接展示出去。"""
        text = (user_message or "").strip()
        if not text:
            return ""
        match = re.search(r"用户问题[：:]\s*(.+?)(?:\n\s*\n|\n参考资料[：:]|$)", text, flags=re.S)
        if match:
            return match.group(1).strip()
        return text[:120]

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """返回本地知识导览回答。"""
        _ = (temperature, stream)
        user_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        question = self._extract_user_question(user_message)

        content = (
            "【知识导览回答】\n"
            "当前依据平台内置长征史知识库组织回答。\n\n"
            f"你提出的问题是：{question}\n"
            "可继续结合长征路线、节点展项和人物专题进行延伸阅读。"
        )
        return {
            "provider": "mock",
            "model": self.config.get("model", "mock-longmarch-v1"),
            "content": content,
        }

    def generate_with_context(
        self,
        prompt: str,
        context_blocks: Optional[List[str]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """返回可本地展示的生成结果。"""
        _ = temperature
        context_summary = self._build_context_summary(context_blocks)

        if "短视频脚本" in prompt:
            content = (
                "【短视频脚本】\n"
                "标题：长征史上的关键转折\n"
                "镜头一：瑞金出发，旁白说明战略转移背景。\n"
                "镜头二：湘江血战，突出艰苦与牺牲。\n"
                "镜头三：遵义会议，点明历史转折。\n"
                "镜头四：飞夺泸定桥，强化长征精神。\n"
                "结尾金句：长征不仅是一段路，更是一种信念与担当。\n\n"
                f"{context_summary}"
            )
        elif "讲解稿" in prompt:
            content = (
                "【讲解稿】\n"
                "开场：各位同学，今天我们沿着长征足迹回望中国革命的伟大征程。\n"
                "主体：从瑞金出发，到湘江战役、遵义会议、飞夺泸定桥，再到陕北落脚，"
                "每一个节点都凝结着信仰、组织力与人民立场。\n"
                "结语：长征史提醒我们，理想信念是战胜艰难险阻的根本力量。\n\n"
                f"{context_summary}"
            )
        elif "学习总结" in prompt or "闯关" in prompt:
            content = (
                "【学习总结】\n"
                "你已经完成了本轮长征史闯关，对关键路线节点和重大历史转折有了初步把握。"
                "建议继续深入学习遵义会议、长征精神与群众路线等主题，以形成更完整的历史认识。\n\n"
                f"{context_summary}"
            )
        else:
            content = (
                "【知识导览问答】\n"
                "根据当前知识库内容，系统已整理出与问题相关的若干要点。\n\n"
                f"{context_summary}\n\n"
                "可继续进入对应节点展项，结合图片、讲解词和相关人物专题深入学习。"
            )

        return {
            "provider": "mock",
            "model": self.config.get("model", "mock-longmarch-v1"),
            "content": content,
        }
