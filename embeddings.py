"""向量嵌入提供者接口。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List

from utils import get_settings


@dataclass
class EmbeddingProvider:
    """统一的 embedding provider 基类。"""

    provider_name: str
    dimension: int = 192

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    """本地哈希向量，兼容现有轻量演示模式。"""

    def __init__(self, dimension: int = 192) -> None:
        super().__init__(provider_name="hash", dimension=dimension)

    def _tokens(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        tokens: List[str] = []
        buffer = ""
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                if buffer:
                    tokens.append(buffer.lower())
                    buffer = ""
                tokens.append(char)
            elif char.isalnum():
                buffer += char
            else:
                if buffer:
                    tokens.append(buffer.lower())
                    buffer = ""
        if buffer:
            tokens.append(buffer.lower())
        return tokens or list(text)

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class LocalEmbeddingProvider(HashEmbeddingProvider):
    """本地 embedding 预留实现。当前默认回退到 hash。"""

    def __init__(self, dimension: int = 192) -> None:
        super().__init__(dimension=dimension)
        self.provider_name = "local"


class RemoteEmbeddingProvider(HashEmbeddingProvider):
    """远程 embedding API 预留实现。当前默认回退到 hash。"""

    def __init__(self, dimension: int = 192) -> None:
        super().__init__(dimension=dimension)
        self.provider_name = "remote"


def get_embedding_provider(config: Dict[str, Any] | None = None) -> EmbeddingProvider:
    """按配置读取 embedding provider。"""

    settings = get_settings()
    merged = {}
    merged.update(settings)
    merged.update(config or {})

    provider_name = str(merged.get("embedding_provider", "hash") or "hash").strip().lower()
    dimension = int(merged.get("embedding_dimension", 192) or 192)

    if provider_name == "local":
        return LocalEmbeddingProvider(dimension=dimension)
    if provider_name == "remote":
        return RemoteEmbeddingProvider(dimension=dimension)
    return HashEmbeddingProvider(dimension=dimension)
