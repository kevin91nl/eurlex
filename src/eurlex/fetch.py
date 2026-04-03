from __future__ import annotations

import re

import requests

from .utils import _add_query_param, _normalize_language

DEFAULT_REQUEST_TIMEOUT = 30


def get_html_by_cellar_id(
    cellar_id: str, language: str = "en", timeout: int | float = DEFAULT_REQUEST_TIMEOUT
) -> str:
    lang = _normalize_language(language)
    url = "http://publications.europa.eu/resource/cellar/" + str(
        cellar_id.split(":")[1] if ":" in cellar_id else cellar_id
    )
    url = _add_query_param(url, "language", lang["query"])
    response = requests.get(
        url,
        allow_redirects=True,
        timeout=timeout,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": f"{lang['header']}",
        },
    )
    return response.content.decode("utf-8")


def _parse_multichoice_html(html: str) -> list:
    items = []
    try:
        from lxml import html as lxml_html

        tree = lxml_html.fromstring(html)
        for li in tree.xpath("//li[@title='item']"):
            hrefs = li.xpath(".//a/@href")
            if not hrefs:
                continue
            href = hrefs[0]
            label = "".join(li.xpath(".//li[@title='stream_label']/text()"))
            name = "".join(li.xpath(".//li[@title='stream_name']/text()"))
            order_text = "".join(li.xpath(".//li[@title='stream_order']/text()"))
            try:
                order = int(order_text) if order_text else None
            except ValueError:
                order = None
            items.append({"href": href, "label": label, "name": name, "order": order})
        if items:
            return items
    except Exception:  # nosec B110 - intentional fallback to a regex parser for malformed HTML
        pass

    pattern = re.compile(
        r"<li\s+title=\"item\">.*?<a\s+href=\"(?P<href>[^\"]+)\".*?"
        r"<li\s+title=\"stream_name\">(?P<name>[^<]*)</li>.*?"
        r"<li\s+title=\"stream_label\">(?P<label>[^<]*)</li>.*?"
        r"<li\s+title=\"stream_order\"[^>]*>(?P<order>[^<]*)</li>",
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        order_text = match.group("order")
        try:
            order = int(order_text) if order_text else None
        except ValueError:
            order = None
        items.append(
            {
                "href": match.group("href"),
                "label": match.group("label"),
                "name": match.group("name"),
                "order": order,
            }
        )
    if items:
        return items

    for href in re.findall(r"href=\"([^\"]+)\"", html):
        items.append({"href": href, "label": "", "name": "", "order": None})
    return items


def _select_multichoice_url(items: list, language: str = "en") -> str:
    if not items:
        return ""
    lang = _normalize_language(language)["stream"]

    def sort_key(item: dict) -> tuple:
        label = (item.get("label") or "").lower()
        name = item.get("name") or ""
        order = item.get("order")
        lang_match = bool(lang) and f"_{lang}_" in name.upper()
        is_html = name.lower().endswith(".html")
        return (
            0 if label == "act" else 1,
            0 if lang_match else 1,
            0 if is_html else 1,
            order if order is not None else 999,
            name,
        )

    return sorted(items, key=sort_key)[0].get("href", "")


def get_html_by_celex_id(
    celex_id: str, language: str = "en", timeout: int | float = DEFAULT_REQUEST_TIMEOUT
) -> str:
    lang = _normalize_language(language)
    url = "http://publications.europa.eu/resource/celex/" + str(celex_id)
    url = _add_query_param(url, "language", lang["query"])
    response = requests.get(
        url,
        allow_redirects=True,
        timeout=timeout,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": f"{lang['header']}",
        },
    )
    html = response.content.decode("utf-8")
    if response.status_code == 300 or "Multiple-Choice Response" in html:
        items = _parse_multichoice_html(html)
        selected = _select_multichoice_url(items, language=language)
        if selected:
            selected = _add_query_param(selected, "language", lang["query"])
            response = requests.get(
                selected,
                allow_redirects=True,
                timeout=timeout,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Accept-Language": f"{lang['header']}",
                },
            )
            html = response.content.decode("utf-8")
    return html


__all__ = [
    "get_html_by_cellar_id",
    "_parse_multichoice_html",
    "_select_multichoice_url",
    "get_html_by_celex_id",
    "DEFAULT_REQUEST_TIMEOUT",
]
