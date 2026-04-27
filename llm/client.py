"""统一的大模型客户端。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .mock_provider import MockProviderAdapter
from .providers import build_adapter


class LLMClient:
    """对外暴露统一调用接口。"""

    def __init__(self, provider_config: Dict[str, Any]) -> None:
        self.provider_config = provider_config
        self.adapter = build_adapter(provider_config)

    def _fallback_to_mock(self, exc: Exception, mode: str, **kwargs: Any) -> Dict[str, Any]:
        """当真实 provider 不可用时，自动回退到本地知识导览。"""
        provider_name = self.provider_config.get("provider_name", "unknown")
        message = str(exc).strip() or exc.__class__.__name__
        if len(message) > 140:
            message = message[:140] + "..."

        mock_config = {
            "provider_name": "mock",
            "provider": "mock",
            "model": "mock-longmarch-v1",
        }
        mock_adapter = MockProviderAdapter(mock_config)
        if mode == "chat":
            result = mock_adapter.chat(
                messages=kwargs.get("messages", []),
                temperature=kwargs.get("temperature", 0.3),
                stream=kwargs.get("stream", False),
            )
        else:
            result = mock_adapter.generate_with_context(
                prompt=kwargs.get("prompt", ""),
                context_blocks=kwargs.get("context_blocks"),
                temperature=kwargs.get("temperature", 0.3),
            )

        result["warning"] = (
            f"{provider_name} 当前不可用，系统已切换到本地知识导览模式。"
            f"原因：{message}"
        )
        result["fallback_used"] = True
        result["original_provider"] = provider_name
        return result

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """统一聊天调用。"""
        try:
            return self.adapter.chat(messages=messages, temperature=temperature, stream=stream)
        except Exception as exc:
            if self.provider_config.get("provider_name") == "mock":
                raise
            return self._fallback_to_mock(
                exc,
                mode="chat",
                messages=messages,
                temperature=temperature,
                stream=stream,
            )

    def generate_with_context(
        self,
        prompt: str,
        context_blocks: Optional[List[str]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """统一带上下文生成调用。"""
        try:
            return self.adapter.generate_with_context(
                prompt=prompt,
                context_blocks=context_blocks,
                temperature=temperature,
            )
        except Exception as exc:
            if self.provider_config.get("provider_name") == "mock":
                raise
            return self._fallback_to_mock(
                exc,
                mode="generate",
                prompt=prompt,
                context_blocks=context_blocks,
                temperature=temperature,
            )


def get_llm_client(provider_config: Dict[str, Any]) -> LLMClient:
    """工厂函数。"""
    return LLMClient(provider_config)
