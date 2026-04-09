"""管理员登录与简化鉴权。"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils import get_admin_password, load_admin_users

security = HTTPBearer(auto_error=False)
TOKEN_TTL_SECONDS = 12 * 60 * 60
ADMIN_TOKENS: Dict[str, Dict[str, Any]] = {}


def hash_password(password: str) -> str:
    """计算密码摘要。"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码摘要。"""
    return hash_password(password) == password_hash


def cleanup_expired_tokens() -> None:
    """清理过期 token。"""
    now = time.time()
    expired = [token for token, payload in ADMIN_TOKENS.items() if payload["expires_at"] <= now]
    for token in expired:
        ADMIN_TOKENS.pop(token, None)


def authenticate_admin(username: str, password: str) -> Optional[Dict[str, Any]]:
    """校验管理员账号密码。"""
    for admin in load_admin_users():
        stored_hash = admin.get("password_hash")
        if admin.get("username") != username:
            continue
        runtime_password = get_admin_password()
        if runtime_password:
            if hmac.compare_digest(password, runtime_password):
                return admin
            continue
        if stored_hash and verify_password(password, stored_hash):
            return admin
    return None


def create_admin_token(username: str) -> str:
    """生成管理员 token。"""
    cleanup_expired_tokens()
    token = secrets.token_urlsafe(24)
    ADMIN_TOKENS[token] = {
        "username": username,
        "role": "admin",
        "expires_at": time.time() + TOKEN_TTL_SECONDS,
    }
    return token


def admin_login(username: str, password: str) -> Dict[str, Any]:
    """管理员登录，返回 token。"""
    if not get_admin_password() and not any(admin.get("password_hash") for admin in load_admin_users()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="尚未配置管理员密码，请在 Streamlit Secrets 或环境变量中设置 ADMIN_PASSWORD。",
        )
    admin = authenticate_admin(username, password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号或密码错误。",
        )
    token = create_admin_token(username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "display_name": admin.get("display_name", username),
    }


def verify_admin_token(token: str) -> Dict[str, Any]:
    """验证管理员 token。"""
    cleanup_expired_tokens()
    payload = ADMIN_TOKENS.get(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员 token 无效或已过期，请重新登录。",
        )
    return payload


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """FastAPI 依赖：获取当前管理员身份。"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少管理员认证信息。",
        )
    return verify_admin_token(credentials.credentials)
