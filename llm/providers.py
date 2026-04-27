"""统一的 provider adapter 层。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

import requests

from .mock_provider import MockProviderAdapter


class ProviderAdapter(ABC):
    """统一 provider 抽象基类。"""

    provider_name = "base"

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """统一聊天接口。"""

    @abstractmethod
    def generate_with_context(
        self,
        prompt: str,
        context_blocks: Optional[List[str]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """统一上下文生成接口。"""


class OpenAICompatibleAdapter(ProviderAdapter):
    """兼容 OpenAI 风格接口的 provider。"""

    provider_name = "openai_compatible"

    def _endpoint(self) -> str:
        base_url = (self.config.get("base_url") or "").rstrip("/")
        if not base_url:
            raise ValueError("当前 provider 未配置 base_url。")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError("当前模型未提供 API Key，可切换到本地知识导览模式。")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: Dict[str, Any]) -> requests.Response:
        """发起请求，并默认忽略系统代理环境，减少本地代理误配导致的失败。"""
        session = requests.Session()
        session.trust_env = False
        try:
            return session.post(
                self._endpoint(),
                headers=self._headers(),
                json=payload,
                timeout=60,
            )
        except requests.exceptions.ProxyError as exc:
            raise RuntimeError(
                "当前网络代理不可用，无法连接到模型服务。系统将尝试回退到本地知识导览模式。"
            ) from exc
        except requests.exceptions.ConnectTimeout as exc:
            raise RuntimeError(
                "连接模型服务超时，系统将尝试回退到本地知识导览模式。"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "无法连接到模型服务，请检查网络、Base URL 或防火墙设置。系统将尝试回退到本地知识导览模式。"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"模型服务请求失败：{exc.__class__.__name__}。系统将尝试回退到本地知识导览模式。"
            ) from exc

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """按 provider 规则调整请求体。"""
        normalized = payload.copy()
        provider_name = str(self.config.get("provider_name", "")).lower()
        model_name = str(self.config.get("model", "")).lower()

        # Moonshot 官方文档说明：kimi-k2.5 系列会固定使用特定采样参数，
        # 若手动传入其他 temperature/top_p/n 等值会直接报错。
        if provider_name == "moonshot" and model_name.startswith("kimi-k2"):
            normalized.pop("temperature", None)
            normalized.pop("top_p", None)
            normalized.pop("n", None)
            normalized.pop("presence_penalty", None)
            normalized.pop("frequency_penalty", None)

        return normalized

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        payload = self._normalize_payload(
            {
            "model": self.config.get("model", ""),
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            }
        )
        response = self._post(payload)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"{self.config.get('provider_name', 'provider')} 调用失败：{response.text[:300]}"
            ) from exc
        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return {
            "provider": self.config.get("provider_name", self.provider_name),
            "model": self.config.get("model", ""),
            "content": content,
            "raw": data,
        }

    def generate_with_context(
        self,
        prompt: str,
        context_blocks: Optional[List[str]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        context = "\n\n".join(context_blocks or [])
        messages = [
            {
                "role": "system",
                "content": "你是一名正式、准确的中国革命历史讲解助手。",
            },
            {
                "role": "user",
                "content": f"{prompt}\n\n补充上下文：\n{context}",
            },
        ]
        return self.chat(messages=messages, temperature=temperature, stream=False)


class MoonshotAdapter(OpenAICompatibleAdapter):
    """Moonshot / Kimi 适配器。"""

    provider_name = "moonshot"


class QwenAdapter(OpenAICompatibleAdapter):
    """Qwen / DashScope 适配器。"""

    provider_name = "qwen"


class MiniMaxAdapter(OpenAICompatibleAdapter):
    """MiniMax 适配器。"""

    provider_name = "minimax"


class DeepSeekAdapter(OpenAICompatibleAdapter):
    """DeepSeek 适配器。"""

    provider_name = "deepseek"


ADAPTER_REGISTRY: Dict[str, Type[ProviderAdapter]] = {
    "moonshot": MoonshotAdapter,
    "qwen": QwenAdapter,
    "minimax": MiniMaxAdapter,
    "deepseek": DeepSeekAdapter,
    "mock": MockProviderAdapter,
}


def build_adapter(config: Dict[str, Any]) -> ProviderAdapter:
    """根据配置创建 adapter。"""
    provider = (config.get("provider") or config.get("provider_name") or "mock").lower()
    adapter_cls = ADAPTER_REGISTRY.get(provider, OpenAICompatibleAdapter)
    if provider == "mock" or not config.get("api_key"):
        return MockProviderAdapter(config)
    return adapter_cls(config)
