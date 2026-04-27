"""Lightweight HTML template helpers for Streamlit pages."""

from __future__ import annotations

from functools import lru_cache
from string import Template
from typing import Any

from utils import BASE_DIR


@lru_cache(maxsize=32)
def _read_template(relative_path: str) -> str:
    """Read a template file from the repository template directory."""
    return (BASE_DIR / "templates" / relative_path).read_text(encoding="utf-8")


@lru_cache(maxsize=32)
def _read_style(relative_path: str) -> str:
    """Read a CSS file from the repository style directory."""
    return (BASE_DIR / "assets" / "styles" / relative_path).read_text(encoding="utf-8")


def render_template(template_name: str, **context: Any) -> str:
    """Render a local HTML template with pre-escaped context values."""
    values = {key: "" if value is None else str(value) for key, value in context.items()}
    return Template(_read_template(template_name)).safe_substitute(values)


def render_template_block(template_name: str, style_name: str = "", **context: Any) -> str:
    """Render HTML with an optional external CSS file."""
    style_block = ""
    if style_name:
        style_block = f"<style>\n{_read_style(style_name)}\n</style>\n"
    return style_block + render_template(template_name, **context)
