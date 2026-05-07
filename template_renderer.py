"""Lightweight HTML template helpers for Streamlit pages."""

from __future__ import annotations

from functools import lru_cache
import re
from string import Template
from textwrap import dedent
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


@lru_cache(maxsize=32)
def _read_script(relative_path: str) -> str:
    """Read a JavaScript file from the repository script directory."""
    return (BASE_DIR / "assets" / "scripts" / relative_path).read_text(encoding="utf-8")


def render_template(template_name: str, **context: Any) -> str:
    """Render a local HTML template with pre-escaped context values."""
    values = {key: "" if value is None else str(value) for key, value in context.items()}
    markup = Template(_read_template(template_name)).safe_substitute(values)
    return re.sub(r"(?m)^[ \t]+(?=<)", "", dedent(markup).strip())


def render_template_block(template_name: str, style_name: str = "", **context: Any) -> str:
    """Render HTML with an optional external CSS file."""
    style_block = ""
    if style_name:
        style_block = f"<style>\n{_read_style(style_name)}\n</style>\n"
    markup = dedent(style_block + render_template(template_name, **context)).strip()
    return re.sub(r"(?m)^[ \t]+(?=<)", "", markup)


def render_script(script_name: str, **context: Any) -> str:
    """Render a local JavaScript file with simple placeholders."""
    values = {key: "" if value is None else str(value) for key, value in context.items()}
    return dedent(Template(_read_script(script_name)).safe_substitute(values)).strip()


def render_script_block(script_name: str, **context: Any) -> str:
    """Wrap a repository JavaScript file in a script tag for Streamlit components."""
    return f"<script>\n{render_script(script_name, **context)}\n</script>"
