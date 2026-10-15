from __future__ import annotations

import functools
import pathlib
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

ICON_DIR = pathlib.Path(__file__).resolve().parent.parent / "icons"

_SVG_OPEN = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
_CLASS_ATTR = re.compile(r'\sclass\s*=\s*"[^"]*"', re.IGNORECASE)


@functools.lru_cache(maxsize=256)
def _load_icon(name: str) -> str | None:
    """Read an icon off disk once and keep it in memory."""
    # Guard against a template passing something like "../../secrets".
    if not re.fullmatch(r"[a-z0-9-]+", name):
        return None
    path = ICON_DIR / f"{name}.svg"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


@register.simple_tag
def icon(name: str, css_class: str = "size-4", label: str = "") -> str:
    """
    Inline a Heroicon by filename.

        {% icon "plus" %}
        {% icon "magnifying-glass" css_class="size-5 text-gray-400" %}
        {% icon "x-mark" label="Close" %}

    To add an icon, download the 24x24 outline SVG from heroicons.com and save
    it into surecom_ui/icons/ as <name>.svg. No code change required.

    An unknown name renders an HTML comment rather than raising, so a missing
    icon can never take a page down.
    """
    svg = _load_icon(name)
    if svg is None:
        return mark_safe(f"<!-- surecom-ui: unknown icon {escape(name)} -->")

    if label:
        extra = f' role="img" aria-label="{escape(label)}"'
    else:
        extra = ' aria-hidden="true" focusable="false"'

    def _rewrite(match: re.Match[str]) -> str:
        attrs = _CLASS_ATTR.sub("", match.group(1))
        return f'<svg{attrs} class="{escape(css_class)}"{extra}>'

    return mark_safe(_SVG_OPEN.sub(_rewrite, svg, count=1))


@register.inclusion_tag("surecom_ui/components/nav_item.html", takes_context=True)
def nav_item(context, url: str, text: str, icon_name: str = "", match: str = ""):
    """
    A single top-level nav link, with active styling applied automatically.

        {% nav_item url_for_sites "Sites" icon_name="map" %}
        {% nav_item changelog_url "Change Log" match="/changes/" %}

    Active when the current path starts with `match`, defaulting to `url`.
    The root path is compared exactly, so "/" does not light up everywhere.
    """
    request = context.get("request")
    path = getattr(request, "path", "") or ""
    target = match or url

    if target == "/":
        active = path == "/"
    else:
        active = bool(target) and path.startswith(target)

    return {"url": url, "text": text, "icon_name": icon_name, "active": active}


@register.filter
def message_variant(tags: str) -> str:
    """
    Map Django's message tags onto this design system's alert variants.

    Django emits "error", "warning", "success", "info" and "debug"; Bootstrap
    names used by older templates ("danger") are accepted too.
    """
    mapping = {
        "debug": "info",
        "info": "info",
        "success": "success",
        "warning": "warning",
        "error": "error",
        "danger": "error",
    }
    for tag in (tags or "").split():
        if tag in mapping:
            return mapping[tag]
    return "info"
