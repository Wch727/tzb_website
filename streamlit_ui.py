"""Streamlit 多页面共享 UI 工具。"""

from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from activity_manager import get_activity
from utils import (
    BASE_DIR,
    get_default_provider_name,
    get_settings,
    get_visible_user_models,
    is_user_key_allowed,
    now_text,
    resolve_provider_config,
)

APP_TITLE = "长征精神·沉浸式云端答题互动平台"
ROLE_OPTIONS = ["大学生", "研学团成员", "普通参观者"]
CONTENT_MODE_OPTIONS = [
    ("auto", "自动判断"),
    ("static", "知识导览模式"),
    ("ai", "智能讲解增强"),
]
TOPIC_FILTERS = [
    ("综合导览", {}),
    ("重大事件", {"type": "event"}),
    ("重要人物", {"type": "figure"}),
    ("重要地点", {"type": "place"}),
    ("路线节点", {"type": "route"}),
    ("长征精神", {"type": "spirit"}),
    ("常见问答", {"type": "faq"}),
]


def _background_image_uri() -> str:
    """读取背景素材并转换为 data URI。"""
    candidates = [
        BASE_DIR / "assets" / "images" / "route_map.svg",
        BASE_DIR / "assets" / "images" / "changzheng_route_map.jpg",
    ]
    for path in candidates:
        if not path.exists():
            continue
        return _asset_to_data_uri(path)
    return ""


def _asset_to_data_uri(path_like: Any) -> str:
    """将本地素材转换为 data URI。"""
    path = path_like if isinstance(path_like, str) else str(path_like)
    candidate = BASE_DIR / path if not str(path).startswith(str(BASE_DIR)) else Path(path)
    if not candidate.exists():
        candidate = BASE_DIR / str(path).lstrip("./")
    if not candidate.exists():
        return ""
    mime, _ = mimetypes.guess_type(str(candidate))
    if candidate.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime or 'application/octet-stream'};base64,{encoded}"


def inject_custom_css() -> None:
    """注入统一的产品化样式。"""
    css = """
        <style>
        .stApp {
            background: #f5eeeb;
            color: #211815;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #5b0f2b 0%, #7b1736 100%);
        }
        [data-testid="stSidebar"] * {
            color: #fff6f3;
        }
        .hero-banner {
            padding: 1.6rem 1.8rem;
            border-radius: 26px;
            background: linear-gradient(135deg, rgba(92, 13, 41, 0.98) 0%, rgba(132, 22, 56, 0.96) 52%, rgba(168, 41, 73, 0.94) 100%);
            color: #fff7f4;
            box-shadow: 0 18px 46px rgba(78, 16, 33, 0.22);
            border: 1px solid rgba(255, 238, 234, 0.16);
            margin-bottom: 1rem;
        }
        .masthead-shell {
            margin: 0.2rem 0 1rem;
            border-radius: 28px;
            padding: 1rem 1.2rem 1.1rem;
            background: linear-gradient(180deg, rgba(255, 251, 249, 0.92), rgba(249, 240, 236, 0.88));
            border: 1px solid rgba(129, 25, 53, 0.12);
            box-shadow: 0 14px 34px rgba(78, 16, 33, 0.08);
            backdrop-filter: blur(6px);
        }
        .masthead-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 0.9rem;
        }
        .masthead-kicker {
            color: #8a2947;
            font-size: 0.82rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .masthead-title {
            color: #5b112d;
            font-size: 1.55rem;
            font-weight: 700;
            margin-bottom: 0.18rem;
        }
        .masthead-subtitle {
            color: #6e5555;
            font-size: 0.95rem;
            line-height: 1.75;
            max-width: 780px;
        }
        .masthead-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
        }
        .masthead-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.34rem 0.8rem;
            border-radius: 999px;
            background: rgba(128, 18, 52, 0.08);
            border: 1px solid rgba(128, 18, 52, 0.16);
            color: #7b1736;
            font-size: 0.84rem;
        }
        .masthead-divider {
            height: 1px;
            background: linear-gradient(90deg, rgba(128, 18, 52, 0.26), rgba(128, 18, 52, 0));
            margin: 0.25rem 0 0.9rem;
        }
        .nav-section-label {
            color: #8a2947;
            font-size: 0.84rem;
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            line-height: 1.8;
            color: rgba(255, 249, 240, 0.92);
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-bottom: 0.85rem;
        }
        .badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
            background: rgba(255, 246, 244, 0.12);
            border: 1px solid rgba(255, 241, 238, 0.18);
            font-size: 0.86rem;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.95rem;
            margin: 0.8rem 0 1.2rem;
        }
        .card-grid.timeline-grid {
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        }
        .info-card, .source-card, .status-card {
            background: rgba(255, 252, 250, 0.92);
            border: 1px solid rgba(139, 38, 66, 0.14);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 28px rgba(78, 16, 33, 0.08);
        }
        .script-sheet {
            position: relative;
            border-radius: 24px;
            padding: 1.35rem 1.45rem 1.25rem;
            margin: 0.4rem 0 0.95rem;
            background:
                linear-gradient(180deg, rgba(255, 252, 249, 0.98) 0%, rgba(248, 240, 237, 0.95) 100%);
            border: 1px solid rgba(139, 38, 66, 0.18);
            box-shadow: 0 16px 34px rgba(78, 16, 33, 0.10);
            overflow: hidden;
        }
        .script-sheet::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(128, 18, 52, 0.05) 0, rgba(128, 18, 52, 0.05) 1px, transparent 1px, transparent 100%);
            background-size: 100% 2.15rem;
            opacity: 0.18;
            pointer-events: none;
        }
        .script-kicker {
            position: relative;
            color: #8a2947;
            font-size: 0.84rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }
        .script-title {
            position: relative;
            color: #5b112d;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .script-meta {
            position: relative;
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.95rem;
        }
        .script-meta-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.26rem 0.72rem;
            border-radius: 999px;
            background: rgba(128, 18, 52, 0.08);
            border: 1px solid rgba(128, 18, 52, 0.12);
            color: #7b1736;
            font-size: 0.83rem;
        }
        .script-block {
            position: relative;
            margin-bottom: 0.95rem;
        }
        .script-section-title {
            color: #7d1738;
            font-size: 1.02rem;
            font-weight: 700;
            margin-bottom: 0.32rem;
        }
        .script-paragraph {
            color: #332a23;
            line-height: 1.95;
            font-size: 1rem;
            text-indent: 2em;
            margin: 0;
        }
        .script-paragraph + .script-paragraph {
            margin-top: 0.4rem;
        }
        .card-label, .source-label {
            color: #7b6147;
            font-size: 0.9rem;
        }
        .card-title, .source-title {
            color: #4b2119;
            font-size: 1.05rem;
            font-weight: 700;
            margin: 0.18rem 0 0.42rem;
        }
        .card-desc, .source-desc {
            color: #4c433d;
            line-height: 1.72;
            font-size: 0.93rem;
        }
        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #4b2119;
            margin: 1rem 0 0.35rem;
        }
        .section-subtitle {
            color: #7a6350;
            margin-bottom: 0.8rem;
        }
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.8rem;
            margin: 0.8rem 0 1rem;
        }
        .metric-box {
            border-radius: 18px;
            padding: 0.9rem 1rem;
            background: rgba(255, 252, 250, 0.88);
            border: 1px solid rgba(139, 38, 66, 0.14);
        }
        .metric-name {
            color: #8a2947;
            font-size: 0.88rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #7b1736;
        }
        .game-status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.9rem;
            margin: 0.7rem 0 1.1rem;
        }
        .game-status-card {
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 1rem 1.05rem 0.95rem;
            background: linear-gradient(180deg, rgba(255, 252, 250, 0.96), rgba(247, 238, 234, 0.93));
            border: 1px solid rgba(139, 38, 66, 0.18);
            box-shadow: 0 12px 30px rgba(78, 16, 33, 0.08);
            min-height: 148px;
        }
        .game-status-card::before {
            content: "";
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, rgba(123, 23, 54, 0.95), rgba(181, 87, 112, 0.68));
        }
        .game-status-kicker {
            color: #8a2947;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
            margin-bottom: 0.75rem;
        }
        .game-status-value {
            color: #4b2119;
            font-size: 1.9rem;
            line-height: 1.1;
            font-weight: 800;
            margin-bottom: 0.2rem;
            word-break: break-word;
        }
        .game-status-label {
            color: #7b1736;
            font-size: 0.94rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .game-status-note {
            color: #6a5952;
            font-size: 0.86rem;
            line-height: 1.65;
        }
        .notice-card {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: rgba(255, 248, 246, 0.88);
            border: 1px solid rgba(139, 38, 66, 0.18);
            margin: 0.8rem 0 1rem;
        }
        .curator-note {
            border-radius: 24px;
            padding: 1.1rem 1.2rem;
            background: linear-gradient(135deg, rgba(255, 250, 247, 0.96), rgba(248, 240, 237, 0.94));
            border: 1px solid rgba(139, 38, 66, 0.20);
            box-shadow: 0 10px 26px rgba(78, 16, 33, 0.08);
            margin: 0.6rem 0 1rem;
        }
        .curator-label {
            color: #8a2947;
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .curator-title {
            color: #5b112d;
            font-size: 1.15rem;
            font-weight: 700;
            margin: 0.25rem 0 0.4rem;
        }
        .curator-desc {
            color: #4c433d;
            line-height: 1.78;
            font-size: 0.95rem;
        }
        .chapter-strip {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.95rem;
            margin: 0.9rem 0 1.2rem;
        }
        .chapter-card {
            background: rgba(255, 252, 250, 0.94);
            border: 1px solid rgba(139, 38, 66, 0.16);
            border-radius: 24px;
            padding: 1rem 1.1rem;
            box-shadow: 0 12px 30px rgba(78, 16, 33, 0.08);
        }
        .chapter-card.active {
            border-color: rgba(128, 18, 52, 0.42);
            box-shadow: 0 18px 34px rgba(78, 16, 33, 0.12);
            background: linear-gradient(180deg, rgba(255, 247, 244, 0.97), rgba(247, 236, 233, 0.94));
        }
        .chapter-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.65rem;
            border-radius: 999px;
            background: rgba(128, 18, 52, 0.10);
            color: #7b1736;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 0.55rem;
        }
        .chapter-title {
            color: #5b112d;
            font-size: 1.08rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .chapter-subtitle {
            color: #675646;
            font-size: 0.92rem;
            line-height: 1.7;
            margin-bottom: 0.55rem;
        }
        .chapter-meta {
            color: #8b6b4d;
            font-size: 0.84rem;
            line-height: 1.6;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 0.95rem;
            margin: 0.8rem 0 1rem;
        }
        .detail-panel {
            background: rgba(255, 252, 247, 0.9);
            border: 1px solid rgba(154, 113, 61, 0.18);
            border-radius: 22px;
            padding: 1rem 1.1rem;
        }
        .detail-panel-title {
            color: #4b2119;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .detail-panel-desc {
            color: #4c433d;
            line-height: 1.8;
            font-size: 0.94rem;
        }
        .boss-intro {
            margin: 0.75rem 0 1.2rem;
            padding: 1.15rem 1.2rem 1.05rem;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(115, 16, 41, 0.96), rgba(152, 35, 63, 0.9));
            color: #fff8f4;
            box-shadow: 0 18px 42px rgba(84, 12, 31, 0.22);
            border: 1px solid rgba(255, 240, 230, 0.12);
        }
        .boss-intro-label {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(255, 236, 225, 0.76);
            margin-bottom: 0.35rem;
        }
        .boss-intro-title {
            font-size: 2rem;
            line-height: 1.15;
            font-weight: 800;
            margin-bottom: 0.55rem;
            color: #fff9f6;
        }
        .boss-intro-lead {
            font-size: 1.02rem;
            line-height: 1.9;
            color: rgba(255, 245, 239, 0.95);
            margin-bottom: 0.9rem;
        }
        .boss-intro-focus {
            border-left: 3px solid rgba(255, 228, 205, 0.55);
            padding-left: 0.95rem;
            margin-bottom: 0.95rem;
            color: rgba(255, 243, 237, 0.92);
            line-height: 1.85;
        }
        .boss-order-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.85rem;
            margin-bottom: 0.9rem;
        }
        .boss-order-card {
            border-radius: 18px;
            padding: 0.85rem 0.95rem;
            background: rgba(255, 248, 243, 0.1);
            border: 1px solid rgba(255, 235, 224, 0.15);
        }
        .boss-order-title {
            color: #ffe1cc;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .boss-order-desc {
            color: #fff7f2;
            line-height: 1.7;
            font-size: 0.92rem;
        }
        .boss-intro-stakes {
            padding-top: 0.75rem;
            border-top: 1px solid rgba(255, 234, 224, 0.18);
            color: rgba(255, 243, 237, 0.88);
            line-height: 1.8;
            font-size: 0.92rem;
        }
        .boss-outcome {
            margin: 0.85rem 0 1.25rem;
            padding: 1rem 1.1rem 0.95rem;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(255, 250, 248, 0.96), rgba(245, 233, 228, 0.94));
            border: 1px solid rgba(139, 38, 66, 0.15);
            box-shadow: 0 14px 32px rgba(78, 16, 33, 0.08);
        }
        .boss-outcome-label {
            color: #8a2947;
            font-size: 0.78rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.28rem;
        }
        .boss-outcome-title {
            color: #5b112d;
            font-size: 1.35rem;
            line-height: 1.2;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }
        .boss-outcome-lead {
            color: #4c433d;
            line-height: 1.85;
            font-size: 0.98rem;
            margin-bottom: 0.78rem;
        }
        .boss-outcome-focus {
            color: #5a5047;
            line-height: 1.8;
            border-left: 3px solid rgba(123, 23, 54, 0.25);
            padding-left: 0.9rem;
            margin-bottom: 0.78rem;
        }
        .boss-outcome-closing {
            color: #6d554f;
            line-height: 1.78;
        }
        .feature-ribbon {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1rem;
            margin: 0.85rem 0 1.2rem;
        }
        .feature-shell {
            background: linear-gradient(180deg, rgba(255, 252, 250, 0.95), rgba(247, 239, 236, 0.92));
            border: 1px solid rgba(139, 38, 66, 0.16);
            border-radius: 24px;
            padding: 1rem 1.05rem;
            box-shadow: 0 14px 34px rgba(78, 16, 33, 0.08);
        }
        .feature-kicker {
            color: #8a2947;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.32rem;
        }
        .feature-headline {
            color: #5b112d;
            font-size: 1.08rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .feature-body {
            color: #5a5047;
            line-height: 1.72;
            font-size: 0.92rem;
        }
        .gallery-frame {
            border-radius: 28px;
            padding: 1rem 1.05rem;
            background: linear-gradient(180deg, rgba(255, 251, 248, 0.90), rgba(246, 237, 234, 0.88));
            border: 1px solid rgba(139, 38, 66, 0.14);
            box-shadow: 0 14px 34px rgba(78, 16, 33, 0.06);
            margin: 0.85rem 0 1.2rem;
        }
        .gallery-title {
            color: #5b112d;
            font-size: 1.08rem;
            font-weight: 700;
            margin-bottom: 0.18rem;
        }
        .gallery-subtitle {
            color: #6f5c4c;
            font-size: 0.92rem;
            line-height: 1.72;
            margin-bottom: 0.85rem;
        }
        .exhibition-hero {
            position: relative;
            overflow: hidden;
            border-radius: 34px;
            min-height: 460px;
            padding: 2rem 2rem 1.75rem;
            margin: 0.4rem 0 1.1rem;
            background:
                linear-gradient(110deg, rgba(55, 21, 16, 0.88) 0%, rgba(92, 34, 24, 0.84) 42%, rgba(138, 71, 41, 0.56) 72%, rgba(248, 234, 212, 0.12) 100%),
                linear-gradient(180deg, rgba(0,0,0,0.08), rgba(0,0,0,0.22));
            border: 1px solid rgba(255, 240, 220, 0.16);
            box-shadow: 0 26px 64px rgba(67, 29, 20, 0.22);
            color: #fff9f0;
        }
        .exhibition-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background-image: var(--hero-image);
            background-size: cover;
            background-position: center center;
            opacity: 0.3;
            transform: scale(1.04);
            filter: saturate(0.96) contrast(1.02);
            z-index: 0;
        }
        .exhibition-hero::after {
            content: "";
            position: absolute;
            inset: auto -80px -80px auto;
            width: 340px;
            height: 340px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255, 214, 147, 0.22) 0%, rgba(255,214,147,0.04) 60%, transparent 72%);
            z-index: 0;
        }
        .exhibition-hero-inner {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.85fr);
            gap: 1.2rem;
            align-items: stretch;
        }
        .exhibition-kicker {
            color: rgba(255, 233, 199, 0.92);
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-size: 0.82rem;
            margin-bottom: 0.55rem;
        }
        .exhibition-title {
            font-size: 2.7rem;
            line-height: 1.16;
            font-weight: 800;
            margin-bottom: 0.75rem;
            max-width: 760px;
        }
        .exhibition-subtitle {
            color: rgba(255, 246, 232, 0.92);
            font-size: 1rem;
            line-height: 1.92;
            max-width: 760px;
            margin-bottom: 1rem;
        }
        .exhibition-tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-bottom: 1.1rem;
        }
        .exhibition-tag {
            display: inline-flex;
            align-items: center;
            padding: 0.36rem 0.82rem;
            border-radius: 999px;
            background: rgba(255, 248, 236, 0.12);
            border: 1px solid rgba(255, 244, 228, 0.22);
            font-size: 0.86rem;
        }
        .exhibition-storyline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.7rem;
        }
        .exhibition-story-card {
            padding: 0.85rem 0.95rem;
            border-radius: 20px;
            background: rgba(255, 248, 236, 0.1);
            border: 1px solid rgba(255, 244, 228, 0.16);
            backdrop-filter: blur(4px);
        }
        .exhibition-story-label {
            font-size: 0.82rem;
            color: rgba(255, 226, 191, 0.88);
            margin-bottom: 0.24rem;
        }
        .exhibition-story-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.18rem;
        }
        .exhibition-story-desc {
            font-size: 0.88rem;
            line-height: 1.68;
            color: rgba(255, 246, 232, 0.9);
        }
        .exhibition-side-panel {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 0.9rem;
        }
        .exhibition-side-card {
            padding: 1rem 1rem 0.95rem;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(255, 248, 236, 0.14), rgba(255, 248, 236, 0.08));
            border: 1px solid rgba(255, 243, 223, 0.18);
            backdrop-filter: blur(6px);
        }
        .exhibition-side-kicker {
            color: rgba(255, 226, 191, 0.86);
            font-size: 0.8rem;
            margin-bottom: 0.2rem;
        }
        .exhibition-side-title {
            font-size: 1.18rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        .exhibition-side-text {
            color: rgba(255, 245, 231, 0.92);
            font-size: 0.92rem;
            line-height: 1.78;
        }
        .exhibition-side-points {
            margin-top: 0.55rem;
            padding-left: 1rem;
        }
        .exhibition-side-points li {
            margin-bottom: 0.28rem;
            color: rgba(255, 245, 231, 0.9);
        }
        .ledger-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.7rem;
            margin: 0.8rem 0 1rem;
        }
        .ledger-card {
            background: rgba(255, 249, 239, 0.88);
            border: 1px solid rgba(166, 130, 85, 0.24);
            border-radius: 18px;
            padding: 0.8rem 0.95rem;
        }
        .ledger-index {
            color: #8b6b4d;
            font-size: 0.82rem;
            margin-bottom: 0.25rem;
        }
        .ledger-title {
            color: #4b2119;
            font-size: 0.98rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .ledger-text {
            color: #5a5047;
            font-size: 0.88rem;
            line-height: 1.6;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.9rem;
        }
        div[data-baseweb="tab-list"] button {
            background: rgba(255, 251, 244, 0.76);
            border-radius: 14px;
            border: 1px solid rgba(142, 103, 61, 0.18);
            padding: 0.45rem 0.95rem;
        }
        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            background: linear-gradient(135deg, #7c2a22 0%, #a44b3b 100%);
            color: #fff8ef;
            border-color: rgba(124, 42, 34, 0.6);
        }
        .small-muted {
            color: #7d6650;
            font-size: 0.88rem;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def scroll_page_to_top() -> None:
    """在页面重渲染后把视角拉回顶部。"""
    components.html(
        """
        <script>
        const parentWindow = window.parent;
        try {
          parentWindow.scrollTo({ top: 0, behavior: "instant" });
          const appView = parentWindow.document.querySelector("[data-testid='stAppViewContainer']");
          if (appView) {
            appView.scrollTo({ top: 0, behavior: "instant" });
          }
          const mainSection = parentWindow.document.querySelector("section.main");
          if (mainSection) {
            mainSection.scrollTo({ top: 0, behavior: "instant" });
          }
        } catch (error) {
          parentWindow.scrollTo(0, 0);
        }
        </script>
        """,
        height=0,
    )


def _clean_html(markup: str) -> str:
    """清理多行 HTML 的缩进，避免被 Markdown 误判为代码块。"""
    return dedent(markup).strip()


def init_session_state() -> None:
    """初始化前端会话状态。"""
    default_provider = get_default_provider_name()
    defaults = {
        "user_name": "红色学习者",
        "unit_name": "体验组",
        "user_role": "大学生",
        "selected_figure_name": "毛泽东",
        "selected_provider_name": default_provider,
        "selected_topic_label": "综合导览",
        "session_api_keys": {},
        "qa_messages": [],
        "game_state": {},
        "game_started": False,
        "game_explanations": {},
        "admin_authenticated": False,
        "admin_profile": {},
        "admin_token": "",
        "content_mode_preference": "auto",
        "selected_role_id": "scout",
        "selected_role_name": "侦察兵",
        "current_activity_id": "knowledge-contest",
        "current_team_id": "",
        "current_team_name": "",
        "current_branch_name": "",
        "story_state": {},
        "progress_snapshot": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    ensure_user_model_selection()


def sync_activity_from_query() -> None:
    """从查询参数中同步活动选择。"""
    try:
        activity_id = str(st.query_params.get("activity_id", "") or "").strip()
    except Exception:
        activity_id = ""
    if activity_id:
        st.session_state["current_activity_id"] = activity_id


def setup_page(page_title: str, icon: str = "🏔️") -> None:
    """设置页面基础配置。"""
    st.set_page_config(
        page_title=f"{page_title} | {APP_TITLE}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_custom_css()
    init_session_state()
    bootstrap_repository_content()
    sync_activity_from_query()
    if st.session_state.pop("_scroll_to_top_once", False):
        scroll_page_to_top()
    render_minimal_sidebar()


def render_minimal_sidebar() -> None:
    """在侧边栏仅保留导航与少量状态。"""
    current_model = get_selected_model_info()
    activity_info = get_activity(st.session_state.get("current_activity_id", ""))
    with st.sidebar:
        st.markdown("### 页面导航")
        st.page_link("app.py", label="应用入口")
        st.page_link("pages/1_首页.py", label="首页")
        st.page_link("pages/2_角色选择.py", label="角色选择")
        st.page_link("pages/3_长征路线.py", label="长征路线")
        st.page_link("pages/4_剧情答题.py", label="剧情答题")
        st.page_link("pages/5_知识库.py", label="知识百问")
        st.page_link("pages/6_活动中心.py", label="活动中心")
        st.page_link("pages/7_排行榜.py", label="排行榜")
        st.page_link("pages/8_配置页.py", label="使用设置")
        st.page_link("pages/9_管理员后台.py", label="内容运营")
        st.page_link("pages/10_测试体验.py", label="导览速览")
        st.page_link("pages/11_讲解生成.py", label="讲解工坊")
        st.page_link("pages/12_数据大屏.py", label="数据大屏")
        st.page_link("pages/13_人物专题.py", label="人物专题")
        st.divider()
        st.caption(f"当前角色：{st.session_state.get('selected_role_name', '侦察兵')}")
        if activity_info:
            st.caption(f"当前活动：{activity_info.get('name', '')}")
        if st.session_state.get("current_team_name"):
            st.caption(f"当前小队：{st.session_state.get('current_team_name', '')}")
        if st.session_state.get("current_branch_name"):
            st.caption(f"支部归属：{st.session_state.get('current_branch_name', '')}")
        if current_model:
            st.caption(f"当前模型：{current_model.get('display_name', '未选择')}")
        st.caption(f"更新时间：{now_text()}")


def ensure_user_model_selection() -> None:
    """确保当前会话中的模型选择仍然有效。"""
    visible_models = get_visible_user_models()
    if not visible_models:
        st.session_state["selected_provider_name"] = "mock"
        return

    allowed_names = [item["provider_name"] for item in visible_models]
    current = st.session_state.get("selected_provider_name", "")
    if current not in allowed_names:
        default_model = next((item for item in visible_models if item.get("is_default")), visible_models[0])
        st.session_state["selected_provider_name"] = default_model["provider_name"]


def get_selected_model_info() -> Dict[str, Any]:
    """获取当前选中的用户模型信息。"""
    ensure_user_model_selection()
    current = st.session_state.get("selected_provider_name", "")
    visible_models = get_visible_user_models()
    for item in visible_models:
        if item["provider_name"] == current:
            return item
    return visible_models[0] if visible_models else {}


def set_selected_provider(provider_name: str) -> None:
    """更新当前会话选择的模型。"""
    st.session_state["selected_provider_name"] = provider_name
    if not is_user_key_allowed(provider_name):
        st.session_state.setdefault("session_api_keys", {})
        st.session_state["session_api_keys"][provider_name] = ""


def get_runtime_api_key(provider_name: str) -> str:
    """获取当前会话中某个 provider 的临时 Key。"""
    return st.session_state.get("session_api_keys", {}).get(provider_name, "")


def set_runtime_api_key(provider_name: str, api_key: str) -> None:
    """保存当前会话中某个 provider 的临时 Key。"""
    st.session_state.setdefault("session_api_keys", {})
    st.session_state["session_api_keys"][provider_name] = api_key


def build_current_provider_config() -> Dict[str, Any]:
    """构造当前页面使用的 provider 配置。"""
    model_info = get_selected_model_info()
    provider_name = model_info.get("provider_name", "mock")
    runtime_key = get_runtime_api_key(provider_name) if model_info.get("allow_user_key") else ""
    config = resolve_provider_config(provider_name=provider_name, runtime_api_key=runtime_key)
    preference = st.session_state.get("content_mode_preference", "auto")
    has_real_key = config.get("provider_name") != "mock" and config.get("api_key_source") != "missing"
    static_mode = preference == "static" or not has_real_key
    if preference == "ai" and has_real_key:
        static_mode = False
    config["content_mode_preference"] = preference
    config["static_mode"] = static_mode
    config["mode_label"] = "知识导览模式" if static_mode else "智能讲解增强"
    if preference == "static":
        config["mode_reason"] = "当前已切换为知识导览模式，系统将优先依据内置史料与知识卡组织内容。"
    elif static_mode and not has_real_key:
        config["mode_reason"] = "当前未检测到可用模型密钥，系统将依据内置史料与知识卡完成导览与讲解。"
    else:
        config["mode_reason"] = "当前将结合知识检索结果进行智能讲解与生成。"
    return config


def bootstrap_repository_content() -> None:
    """确保应用启动时完成默认知识库初始化。"""
    if st.session_state.get("_repository_content_ready"):
        return
    try:
        from rag import ensure_default_knowledge_base

        with st.spinner("正在加载仓库内置内容..."):
            st.session_state["_repository_content_status"] = ensure_default_knowledge_base()
    except Exception as exc:
        st.session_state["_repository_content_status"] = {
            "message": "站点内置知识内容加载失败，请稍后刷新页面或联系维护人员检查环境配置。",
            "error": str(exc),
            "initialized": False,
        }
    st.session_state["_repository_content_ready"] = True


def _nav_action(label: str, target: str, current_page: str, current_aliases: List[str] | None = None) -> None:
    """渲染顶部导航按钮。"""
    aliases = {current_page}
    for item in current_aliases or []:
        aliases.add(item)
    is_current = label in aliases or target in aliases
    if st.button(label, key=f"topnav::{target}", width="stretch", type="primary" if is_current else "secondary", disabled=is_current):
        st.switch_page(target)


def render_top_nav(current_page: str) -> None:
    """渲染页内顶部导航。"""
    current_model = get_selected_model_info()
    current_role = st.session_state.get("selected_role_name", "侦察兵")
    current_activity = get_activity(st.session_state.get("current_activity_id", "")) or {}
    current_activity_name = current_activity.get("name", "")
    subtitle_map = {
        "首页": "从主展入口进入路线、人物、精神与互动学习内容。",
        "角色选择": "以不同角色视角进入长征叙事与任务导览。",
        "长征路线": "按四大篇章浏览长征主线展项，进入单节点深度阅读。",
        "剧情答题": "在历史情境中完成互动学习，以题带学。",
        "知识百问": "围绕长征史问题进入问答、延伸阅读与依据检索。",
        "讲解工坊": "围绕节点与专题生成讲解稿和短视频脚本。",
        "活动中心": "查看活动、分享入口、协作方式与参与路径。",
        "排行榜": "查看个人、小队、单位与活动排行。",
        "使用设置": "调整导览模式、模型选择与访问会话设置。",
        "内容运营": "维护内容、活动与知识库运行状态。",
        "导览速览": "从重点问题、展项与讲解入口快速进入长征主线。",
        "数据大屏": "集中呈现参与情况、热度变化与榜单数据。",
    }
    chips = [
        f"<span class='masthead-chip'>身份：{html.escape(current_role)}</span>",
    ]
    if current_activity_name:
        chips.append(f"<span class='masthead-chip'>活动：{html.escape(current_activity_name)}</span>")
    if current_model and current_page in {"知识百问", "讲解工坊", "使用设置"}:
        chips.append(f"<span class='masthead-chip'>模型：{html.escape(current_model.get('display_name', '知识导览模式'))}</span>")
    st.markdown(
        _clean_html(
            f"""
            <div class="masthead-shell">
                <div class="masthead-top">
                    <div>
                        <div class="masthead-kicker">长征主题数字展</div>
                        <div class="masthead-title">{html.escape(APP_TITLE)}</div>
                        <div class="masthead-subtitle">{html.escape(subtitle_map.get(current_page, '沿着长征主线浏览展项、知识与互动学习内容。'))}</div>
                    </div>
                    <div class="masthead-meta">{''.join(chips)}</div>
                </div>
                <div class="masthead-divider"></div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<div class='nav-section-label'>主展导航</div>", unsafe_allow_html=True)
    row1 = st.columns(6)
    with row1[0]:
        _nav_action("首页", "pages/1_首页.py", current_page)
    with row1[1]:
        _nav_action("长征路线", "pages/3_长征路线.py", current_page)
    with row1[2]:
        _nav_action("知识百问", "pages/5_知识库.py", current_page)
    with row1[3]:
        _nav_action("剧情答题", "pages/4_剧情答题.py", current_page)
    with row1[4]:
        _nav_action("讲解工坊", "pages/11_讲解生成.py", current_page)
    with row1[5]:
        _nav_action("活动中心", "pages/6_活动中心.py", current_page)

    st.markdown("<div class='nav-section-label'>辅助入口</div>", unsafe_allow_html=True)
    row2 = st.columns(5)
    with row2[0]:
        _nav_action("角色选择", "pages/2_角色选择.py", current_page)
    with row2[1]:
        _nav_action("排行榜", "pages/7_排行榜.py", current_page)
    with row2[2]:
        _nav_action("导览速览", "pages/10_测试体验.py", current_page)
    with row2[3]:
        _nav_action("数据大屏", "pages/12_数据大屏.py", current_page)
    with row2[4]:
        _nav_action("使用设置", "pages/8_配置页.py", current_page)

    if st.session_state.get("admin_authenticated"):
        st.markdown("<div class='nav-section-label'>运营入口</div>", unsafe_allow_html=True)
        admin_cols = st.columns(2)
        with admin_cols[0]:
            _nav_action("内容运营", "pages/9_管理员后台.py", current_page)
        with admin_cols[1]:
            _nav_action("使用设置", "pages/8_配置页.py", current_page)


def render_hero(title: str, subtitle: str, badges: List[str] | None = None) -> None:
    """渲染主视觉区。"""
    badge_html = "".join(
        f"<span class='badge-pill'>{html.escape(item)}</span>" for item in (badges or []) if item
    )
    st.markdown(
        _clean_html(
            f"""
        <div class="hero-banner">
          <div class="badge-row">{badge_html}</div>
          <div class="hero-title">{html.escape(title)}</div>
          <div class="hero-subtitle">{html.escape(subtitle)}</div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_metrics(items: List[Dict[str, str]]) -> None:
    """渲染指标条。"""
    cards = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
            <div class="metric-box">
                <div class="metric-name">{html.escape(str(item.get('label', '')))}</div>
                <div class="metric-value">{html.escape(str(item.get('value', '')))}</div>
            </div>
            """
            )
        )
    st.markdown(f"<div class='metric-strip'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_game_status_board(items: List[Dict[str, str]]) -> None:
    """渲染更像网页 HUD 的状态面板。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
                <div class="game-status-card">
                    <div class="game-status-kicker">{html.escape(str(item.get('kicker', '状态')))}</div>
                    <div class="game-status-value">{html.escape(str(item.get('value', '')))}</div>
                    <div class="game-status-label">{html.escape(str(item.get('label', '')))}</div>
                    <div class="game-status-note">{html.escape(str(item.get('note', '')))}</div>
                </div>
                """
            )
        )
    if cards:
        st.markdown(f"<div class='game-status-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_cards(items: List[Dict[str, str]], timeline: bool = False) -> None:
    """渲染信息卡片。"""
    class_name = "card-grid timeline-grid" if timeline else "card-grid"
    cards = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
            <div class="info-card">
                <div class="card-label">{html.escape(str(item.get('label', '')))}</div>
                <div class="card-title">{html.escape(str(item.get('title', '')))}</div>
                <div class="card-desc">{html.escape(str(item.get('desc', '')))}</div>
            </div>
            """
            )
        )
    st.markdown(f"<div class='{class_name}'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_section(title: str, subtitle: str = "") -> None:
    """渲染区块标题。"""
    st.markdown(f"<div class='section-title'>{html.escape(title)}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-subtitle'>{html.escape(subtitle)}</div>", unsafe_allow_html=True)


def render_curatorial_note(title: str, body: str, label: str = "专题导语") -> None:
    """渲染策展导语卡。"""
    st.markdown(
        _clean_html(
            f"""
            <div class="curator-note">
                <div class="curator-label">{html.escape(label)}</div>
                <div class="curator-title">{html.escape(title)}</div>
                <div class="curator-desc">{html.escape(body)}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_chapter_overview_cards(chapters: List[Dict[str, Any]], active_id: str = "") -> None:
    """渲染篇章总览卡。"""
    cards: List[str] = []
    for chapter in chapters:
        class_name = "chapter-card active" if chapter.get("id") == active_id else "chapter-card"
        node_titles = " · ".join(node.get("title", "") for node in chapter.get("nodes", [])[:3])
        cards.append(
            _clean_html(
                f"""
                <div class="{class_name}">
                    <div class="chapter-badge">{html.escape(str(chapter.get('badge', '主线篇章')))}</div>
                    <div class="chapter-title">{html.escape(str(chapter.get('title', '未命名篇章')))}</div>
                    <div class="chapter-subtitle">{html.escape(str(chapter.get('subtitle', '')))}</div>
                    <div class="chapter-meta">节点数量：{html.escape(str(chapter.get('count', len(chapter.get('nodes', [])))))}</div>
                    <div class="chapter-meta">代表节点：{html.escape(node_titles or '沿线展项')}</div>
                </div>
                """
            )
        )
    if cards:
        st.markdown(f"<div class='chapter-strip'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_detail_panels(items: List[Dict[str, str]]) -> None:
    """渲染展项信息板。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
                <div class="detail-panel">
                    <div class="detail-panel-title">{html.escape(str(item.get('title', '')))}</div>
                    <div class="detail-panel-desc">{html.escape(str(item.get('desc', '')))}</div>
                </div>
                """
            )
        )
    if cards:
        st.markdown(f"<div class='detail-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_boss_stage_intro(data: Dict[str, Any]) -> None:
    """渲染大关专属过场。"""
    if not data:
        return
    orders_html = "".join(
        _clean_html(
            f"""
            <div class="boss-order-card">
                <div class="boss-order-title">任务 {index}</div>
                <div class="boss-order-desc">{html.escape(str(item))}</div>
            </div>
            """
        )
        for index, item in enumerate(data.get("orders", []), start=1)
        if str(item).strip()
    )
    st.markdown(
        _clean_html(
            f"""
            <div class="boss-intro">
                <div class="boss-intro-label">{html.escape(str(data.get('label', '章节攻坚关')))}</div>
                <div class="boss-intro-title">{html.escape(str(data.get('title', '关键大关')))}</div>
                <div class="boss-intro-lead">{html.escape(str(data.get('lead', '')))}</div>
                <div class="boss-intro-focus">{html.escape(str(data.get('focus', '')))}</div>
                <div class="boss-order-grid">{orders_html}</div>
                <div class="boss-intro-stakes">{html.escape(str(data.get('stakes', '')))}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_boss_stage_outcome(data: Dict[str, Any]) -> None:
    """渲染大关答题后的专属结算语。"""
    if not data:
        return
    st.markdown(
        _clean_html(
            f"""
            <div class="boss-outcome">
                <div class="boss-outcome-label">{html.escape(str(data.get('label', '章节攻坚关')))}</div>
                <div class="boss-outcome-title">{html.escape(str(data.get('title', '关键大关')))} · 战役复盘</div>
                <div class="boss-outcome-lead">{html.escape(str(data.get('lead', '')))}</div>
                <div class="boss-outcome-focus">{html.escape(str(data.get('focus', '')))}</div>
                <div class="boss-outcome-closing">{html.escape(str(data.get('closing', '')))}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_formal_script(
    script: str,
    *,
    title: str = "",
    label: str = "正式讲解词",
    meta: List[str] | None = None,
) -> None:
    """将讲解内容统一渲染为正式讲解词样式。"""
    content = (script or "").strip()
    if not content:
        st.info("当前暂无可展示的讲解内容。")
        return

    blocks = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
    resolved_title = title.strip()
    if blocks:
        first_line = blocks[0].replace("：", "").replace(":", "").strip()
        if not resolved_title and len(first_line) <= 26 and any(
            marker in first_line for marker in ["讲解稿", "讲解词", "讲述稿", "脚本"]
        ):
            resolved_title = blocks.pop(0)

    section_patterns = (
        r"^[一二三四五六七八九十]+、",
        r"^[（(][一二三四五六七八九十0-9]+[)）]",
        r"^第[一二三四五六七八九十0-9]+部分",
        r"^第[一二三四五六七八九十0-9]+段",
        r"^(开场引入|历史背景|事件经过|历史意义|结尾升华|开场|主体|结尾|镜头[一二三四五六七八九十0-9]+)",
    )

    html_blocks: List[str] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        first = lines[0]
        is_section = any(re.match(pattern, first) for pattern in section_patterns)
        if is_section:
            paragraphs = "".join(
                f"<p class='script-paragraph'>{html.escape(line)}</p>" for line in lines[1:] if line
            )
            html_blocks.append(
                _clean_html(
                    f"""
                    <div class="script-block">
                        <div class="script-section-title">{html.escape(first)}</div>
                        {paragraphs or f"<p class='script-paragraph'>{html.escape(block)}</p>"}
                    </div>
                    """
                )
            )
        else:
            paragraphs = "".join(f"<p class='script-paragraph'>{html.escape(line)}</p>" for line in lines)
            html_blocks.append(f"<div class='script-block'>{paragraphs}</div>")

    meta_markup = ""
    if meta:
        chips = "".join(
            f"<span class='script-meta-chip'>{html.escape(item)}</span>" for item in meta if item and item.strip()
        )
        if chips:
            meta_markup = f"<div class='script-meta'>{chips}</div>"

    st.markdown(
        _clean_html(
            f"""
            <div class="script-sheet">
                <div class="script-kicker">{html.escape(label)}</div>
                <div class="script-title">{html.escape(resolved_title or '长征主题讲解')}</div>
                {meta_markup}
                {''.join(html_blocks)}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_feature_ribbon(items: List[Dict[str, str]]) -> None:
    """渲染首页或篇章摘要带。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
                <div class="feature-shell">
                    <div class="feature-kicker">{html.escape(str(item.get('label', '')))}</div>
                    <div class="feature-headline">{html.escape(str(item.get('title', '')))}</div>
                    <div class="feature-body">{html.escape(str(item.get('desc', '')))}</div>
                </div>
                """
            )
        )
    if cards:
        st.markdown(f"<div class='feature-ribbon'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_ledger_cards(items: List[Dict[str, str]]) -> None:
    """渲染路线或展项清单卡。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
                <div class="ledger-card">
                    <div class="ledger-index">{html.escape(str(item.get('label', '')))}</div>
                    <div class="ledger-title">{html.escape(str(item.get('title', '')))}</div>
                    <div class="ledger-text">{html.escape(str(item.get('desc', '')))}</div>
                </div>
                """
            )
        )
    if cards:
        st.markdown(f"<div class='ledger-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_gallery_frame(title: str, subtitle: str = "") -> None:
    """渲染展厅框架标题。"""
    st.markdown(
        _clean_html(
            f"""
            <div class="gallery-frame">
                <div class="gallery-title">{html.escape(title)}</div>
                <div class="gallery-subtitle">{html.escape(subtitle)}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_exhibition_hero(
    *,
    title: str,
    subtitle: str,
    background_path: str,
    tags: List[str],
    storyline_items: List[Dict[str, str]],
    side_title: str,
    side_text: str,
    side_points: List[str],
) -> None:
    """渲染更具展厅感的首页第一屏。"""
    background_uri = _asset_to_data_uri(background_path)
    tag_markup = "".join(
        f"<span class='exhibition-tag'>{html.escape(item)}</span>" for item in tags if item
    )
    story_markup = "".join(
        _clean_html(
            f"""
            <div class="exhibition-story-card">
                <div class="exhibition-story-label">{html.escape(str(item.get('label', '展线')))}</div>
                <div class="exhibition-story-title">{html.escape(str(item.get('title', '')))}</div>
                <div class="exhibition-story-desc">{html.escape(str(item.get('desc', '')))}</div>
            </div>
            """
        )
        for item in storyline_items
    )
    point_markup = "".join(f"<li>{html.escape(item)}</li>" for item in side_points if item)
    st.markdown(
        _clean_html(
            f"""
            <div class="exhibition-hero" style="--hero-image: url('{background_uri}');">
                <div class="exhibition-hero-inner">
                    <div>
                        <div class="exhibition-kicker">长征主题展入口</div>
                        <div class="exhibition-title">{html.escape(title)}</div>
                        <div class="exhibition-subtitle">{html.escape(subtitle)}</div>
                        <div class="exhibition-tag-row">{tag_markup}</div>
                        <div class="exhibition-storyline">{story_markup}</div>
                    </div>
                    <div class="exhibition-side-panel">
                        <div class="exhibition-side-card">
                            <div class="exhibition-side-kicker">主线提要</div>
                            <div class="exhibition-side-title">{html.escape(side_title)}</div>
                            <div class="exhibition-side-text">{html.escape(side_text)}</div>
                            <ul class="exhibition-side-points">{point_markup}</ul>
                        </div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_model_banner() -> None:
    """渲染当前模型说明。"""
    model_info = get_selected_model_info()
    provider_config = build_current_provider_config()
    description = model_info.get("description") or "该模型用于导览问答、讲解生成与学习辅助。"
    allow_key_text = "允许输入个人 API Key" if model_info.get("allow_user_key") else "使用管理员统一配置"
    readiness_text = "该模型可用于智能讲解与内容生成。"
    if provider_config.get("provider_name") != "mock" and provider_config.get("api_key_source") == "missing":
        readiness_text = "未检测到可用模型密钥，系统将自动切换到知识导览模式。"
    elif provider_config.get("api_key_source") == "streamlit_secrets":
        readiness_text = "已接入平台统一配置的模型密钥。"
    elif provider_config.get("api_key_source") == "environment":
        readiness_text = "已接入可用模型密钥。"
    elif provider_config.get("api_key_source") == "session":
        readiness_text = "正在使用本次访问会话中提供的个人密钥。"
    st.markdown(
        _clean_html(
            f"""
        <div class="notice-card">
            <strong>模型：</strong>{html.escape(model_info.get('display_name', '知识导览模式'))}
            <br/>
            <span class="small-muted">模型标识：{html.escape(model_info.get('model', '未配置'))}</span>
            <br/>
            <span class="small-muted">内容模式：{html.escape(provider_config.get('mode_label', '知识导览模式'))}</span>
            <br/>
            <span class="small-muted">接入方式：{html.escape(allow_key_text)}，展示范围以平台已开放模型为准。</span>
            <br/>
            <span class="small-muted">{html.escape(provider_config.get('mode_reason', readiness_text))}</span>
            <br/>
            <span class="small-muted">{html.escape(description)}</span>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_runtime_notice(result: Dict[str, Any]) -> None:
    """展示模型运行时提示。"""
    if result.get("mode_label"):
        st.info(f"讲解模式：{result['mode_label']}")
    if result.get("warning"):
        st.warning(result["warning"])


def render_sources(sources: List[Dict[str, Any]], title: str = "本次回答依据") -> None:
    """渲染依据来源卡片。"""
    if not sources:
        st.info("暂无可展示的依据片段。")
        return
    with st.expander(title, expanded=False):
        cards = []
        for item in sources:
            meta_bits = [f"类型：{html.escape(str(item.get('type', '未知')))}"]
            if item.get("chapter_title"):
                meta_bits.append(f"章节：{html.escape(str(item.get('chapter_title', '')))}")
            if item.get("section_title"):
                meta_bits.append(f"小节：{html.escape(str(item.get('section_title', '')))}")
            if item.get("source_page"):
                meta_bits.append(f"页码：{html.escape(str(item.get('source_page', '')))}")
            cards.append(
                _clean_html(
                    f"""
                <div class="source-card">
                    <div class="source-label">来源文件：{html.escape(str(item.get('source_file', '未知文件')))}</div>
                    <div class="source-title">{html.escape(str(item.get('title', '未命名')))}</div>
                    <div class="source-desc">
                        {' | '.join(meta_bits)}<br/>
                        摘要片段：{html.escape(str(item.get('snippet', '')))}
                    </div>
                </div>
                """
                )
            )
        st.markdown("".join(cards), unsafe_allow_html=True)


def admin_is_logged_in() -> bool:
    """判断管理员是否已在前端登录。"""
    return bool(st.session_state.get("admin_authenticated"))


def render_admin_badge() -> None:
    """渲染管理员状态提示。"""
    if admin_is_logged_in():
        profile = st.session_state.get("admin_profile", {})
        st.success(f"管理员已登录：{profile.get('display_name', profile.get('username', 'admin'))}")
    else:
        st.info("当前未登录管理员账号。管理员相关配置仅在管理员登录后可用。")


def get_topic_filter_options() -> List[str]:
    """返回主题过滤标签。"""
    return [item[0] for item in TOPIC_FILTERS]


def get_content_mode_options() -> List[str]:
    """返回内容模式标签。"""
    return [item[1] for item in CONTENT_MODE_OPTIONS]


def get_content_mode_label(value: str) -> str:
    """把内容模式值转换成中文。"""
    for key, label in CONTENT_MODE_OPTIONS:
        if key == value:
            return label
    return "自动判断"


def content_mode_key_from_label(label: str) -> str:
    """把内容模式中文标签转回键值。"""
    for key, item_label in CONTENT_MODE_OPTIONS:
        if item_label == label:
            return key
    return "auto"


def get_filters_by_label(label: str) -> Dict[str, Any]:
    """根据标签获取过滤条件。"""
    for item_label, filters in TOPIC_FILTERS:
        if item_label == label:
            return filters.copy()
    return {}
