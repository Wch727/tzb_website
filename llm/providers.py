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


class OpenAIResponsesAdapter(OpenAICompatibleAdapter):
    """OpenAI Responses API 适配器，用于推理、规划和 Codex 类模型。"""

    provider_name = "openai_responses"

    def _endpoint(self) -> str:
        base_url = (self.config.get("base_url") or "").rstrip("/")
        if not base_url:
            raise ValueError("当前 provider 未配置 base_url。")
        if base_url.endswith("/responses"):
            return base_url
        return f"{base_url}/responses"

    @staticmethod
    def _response_input(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        for message in messages:
            role = str(message.get("role", "user") or "user").lower()
            content = str(message.get("content", "") or "")
            if not content:
                continue
            if role not in {"system", "user", "assistant", "developer"}:
                role = "user"
            items.append({"role": role, "content": content})
        return items or [{"role": "user", "content": "请基于已有资料完成讲解。"}]

    @staticmethod
    def _extract_output_text(data: Dict[str, Any]) -> str:
        if data.get("output_text"):
            return str(data.get("output_text", ""))
        parts: List[str] = []
        for item in data.get("output", []) or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []) or []:
                if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                    parts.append(str(content.get("text", "")))
        return "".join(parts)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        payload = {
            "model": self.config.get("model", ""),
            "input": self._response_input(messages),
        }
        if temperature is not None:
            payload["temperature"] = temperature
        response = self._post(payload)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"{self.config.get('provider_name', 'provider')} 调用失败：{response.text[:300]}"
            ) from exc
        data = response.json()
        return {
            "provider": self.config.get("provider_name", self.provider_name),
            "model": self.config.get("model", ""),
            "content": self._extract_output_text(data),
            "raw": data,
        }


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


class OpenAIAdapter(OpenAICompatibleAdapter):
    """OpenAI / GPT 适配器。"""

    provider_name = "openai"


class GeminiAdapter(OpenAICompatibleAdapter):
    """Gemini OpenAI-compatible 适配器。"""

    provider_name = "gemini"


class DoubaoAdapter(OpenAICompatibleAdapter):
    """豆包 / 火山方舟 OpenAI-compatible 适配器。"""

    provider_name = "doubao"


class MimoAdapter(OpenAICompatibleAdapter):
    """小米 MiMo OpenAI-compatible 适配器。"""

    provider_name = "mimo"


class ClaudeAdapter(ProviderAdapter):
    """Anthropic Claude Messages API 适配器。"""

    provider_name = "claude"

    def _endpoint(self) -> str:
        base_url = (self.config.get("base_url") or "https://api.anthropic.com/v1").rstrip("/")
        if base_url.endswith("/messages"):
            return base_url
        return f"{base_url}/messages"

    def _headers(self) -> Dict[str, str]:
        api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError("当前 Claude 连接未提供个人 API Key。")
        auth_header = str(self.config.get("auth_header", "") or "").lower()
        if auth_header == "bearer":
            return {
                "Authorization": f"Bearer {api_key}",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _post(self, payload: Dict[str, Any]) -> requests.Response:
        session = requests.Session()
        session.trust_env = False
        try:
            return session.post(
                self._endpoint(),
                headers=self._headers(),
                json=payload,
                timeout=60,
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Claude 服务请求失败：{exc.__class__.__name__}。系统将回退到本地知识导览模式。"
            ) from exc

    @staticmethod
    def _split_messages(messages: List[Dict[str, str]]) -> Dict[str, Any]:
        system_parts: List[str] = []
        chat_messages: List[Dict[str, str]] = []
        for message in messages:
            role = str(message.get("role", "user") or "user").lower()
            content = str(message.get("content", "") or "")
            if not content:
                continue
            if role == "system":
                system_parts.append(content)
            elif role in {"user", "assistant"}:
                chat_messages.append({"role": role, "content": content})
            else:
                chat_messages.append({"role": "user", "content": content})
        if not chat_messages:
            chat_messages.append({"role": "user", "content": "请基于已有资料完成讲解。"})
        return {"system": "\n\n".join(system_parts), "messages": chat_messages}

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False,
    ) -> Dict[str, Any]:
        split = self._split_messages(messages)
        payload: Dict[str, Any] = {
            "model": self.config.get("model", "claude-3-5-sonnet-latest"),
            "messages": split["messages"],
            "max_tokens": int(self.config.get("max_tokens", 2048) or 2048),
            "temperature": temperature,
        }
        if split["system"]:
            payload["system"] = split["system"]
        response = self._post(payload)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"Claude 调用失败：{response.text[:300]}") from exc
        data = response.json()
        content_blocks = data.get("content", [])
        content = "".join(
            str(block.get("text", ""))
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text"
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
                "content": "你是一名正式、准确、口吻自然的红色历史展陈讲解助手。",
            },
            {
                "role": "user",
                "content": f"{prompt}\n\n补充上下文：\n{context}",
            },
        ]
        return self.chat(messages=messages, temperature=temperature, stream=False)


ADAPTER_REGISTRY: Dict[str, Type[ProviderAdapter]] = {
    "moonshot": MoonshotAdapter,
    "kimi": MoonshotAdapter,
    "openai": OpenAIAdapter,
    "gpt": OpenAIAdapter,
    "openai_responses": OpenAIResponsesAdapter,
    "gemini": GeminiAdapter,
    "qwen": QwenAdapter,
    "minimax": MiniMaxAdapter,
    "deepseek": DeepSeekAdapter,
    "doubao": DoubaoAdapter,
    "volcengine": DoubaoAdapter,
    "claude": ClaudeAdapter,
    "anthropic": ClaudeAdapter,
    "mimo": MimoAdapter,
    "xiaomi": MimoAdapter,
    "xai": OpenAICompatibleAdapter,
    "grok": OpenAICompatibleAdapter,
    "zhipu": OpenAICompatibleAdapter,
    "glm": OpenAICompatibleAdapter,
    "baidu": OpenAICompatibleAdapter,
    "qianfan": OpenAICompatibleAdapter,
    "spark": OpenAICompatibleAdapter,
    "iflytek": OpenAICompatibleAdapter,
    "openrouter": OpenAICompatibleAdapter,
    "siliconflow": OpenAICompatibleAdapter,
    "together": OpenAICompatibleAdapter,
    "groq": OpenAICompatibleAdapter,
    "openai_compatible": OpenAICompatibleAdapter,
    "mock": MockProviderAdapter,
}


def build_adapter(config: Dict[str, Any]) -> ProviderAdapter:
    """根据配置创建 adapter。"""
    provider = (config.get("provider") or config.get("provider_name") or "mock").lower()
    adapter_cls = ADAPTER_REGISTRY.get(provider, OpenAICompatibleAdapter)
    if provider == "mock" or not config.get("api_key"):
        return MockProviderAdapter(config)
    return adapter_cls(config)
