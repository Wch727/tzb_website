"""API 与配置的数据模型。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, Field


class ProviderConfigModel(BaseModel):
    """统一 provider 配置。"""

    provider_name: str
    display_name: str = ""
    provider: str
    base_url: str = ""
    api_key: str = ""
    api_key_secret_name: str = ""
    model: str = ""
    enabled: bool = False
    visible_to_users: bool = True
    allow_user_key: bool = False
    description: str = ""


class AdminLoginRequest(BaseModel):
    """管理员登录请求。"""

    username: str
    password: str


class ProviderUpsertRequest(BaseModel):
    """管理员新增或编辑 provider。"""

    provider_name: str
    display_name: str = ""
    provider: str
    base_url: str = ""
    api_key: str = ""
    api_key_secret_name: str = ""
    model: str = ""
    enabled: bool = False
    visible_to_users: bool = True
    allow_user_key: bool = False
    description: str = ""


class ProviderFlagRequest(BaseModel):
    """布尔开关型 provider 设置。"""

    value: bool = Field(..., description="要设置的布尔值。")


class RetrievalTestRequest(BaseModel):
    """管理员检索调试请求。"""

    question: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    top_k: Optional[int] = None


class UserProviderSelection(BaseModel):
    """普通用户当前会话选择的模型信息。"""

    provider_name: str = "mock"
    api_key: str = ""


class UserSelectModelRequest(UserProviderSelection):
    """普通用户选择模型请求。"""


class AskRequest(UserProviderSelection):
    """RAG 问答请求。"""

    question: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    top_k: Optional[int] = None


class GenerateGuideRequest(UserProviderSelection):
    """讲解稿生成请求。"""

    topic: str
    audience: str = "大学生"
    duration: str = "3分钟"


class GenerateVideoRequest(UserProviderSelection):
    """短视频脚本生成请求。"""

    topic: str
    audience: str = "大学生"
    style: str = "正式讲述"


class GameStartRequest(UserProviderSelection):
    """闯关开始请求。"""

    role: str = "大学生"


class GameChoiceRequest(UserProviderSelection):
    """闯关作答请求。"""

    current_state: Dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("current_state", "state"))
    node_id: str = ""
    route_stage: str = ""
    answer: str
