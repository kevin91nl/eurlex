from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)

from .constants import ISO2_TO_ISO3, ISO3_TO_ISO2, PREFIXES


def get_prefixes() -> dict:
    return PREFIXES


def _normalize_language(language: str) -> dict:
    if not isinstance(language, str) or not language.strip():
        return {"header": "", "query": "", "stream": ""}
    lang = language.strip().lower()
    if "-" in lang:
        lang = lang.split("-")[0]

    if len(lang) == 2:
        header = lang
        query = ISO2_TO_ISO3.get(lang, "")
        stream = lang.upper()
    elif len(lang) == 3:
        header = ISO3_TO_ISO2.get(lang, lang)
        query = lang
        stream = ISO3_TO_ISO2.get(lang, "").upper()
    else:
        header = lang
        query = ""
        stream = ""
    return {"header": header, "query": query, "stream": stream}


def _add_query_param(url: str, key: str, value: str) -> str:
    if not value:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    if query.get(key) == value:
        return url
    query[key] = value
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def simplify_iri(iri: str) -> str:
    for prefix, url in PREFIXES.items():
        if iri.startswith(url):
            return prefix + ":" + iri[len(url) :]
    return iri


def get_tag_name(raw_tag_name: str) -> str:
    if not isinstance(raw_tag_name, str):
        return ""
    return raw_tag_name.split("}")[1] if "}" in raw_tag_name else raw_tag_name


def _get_normalized_classes(child: ETree.Element) -> list[str]:
    raw = child.attrib.get("class", "")
    classes = raw.split()
    return [name[3:] if name.startswith("oj-") else name for name in classes]


def _has_normalized_class(child: ETree.Element, class_name: str) -> bool:
    return class_name in _get_normalized_classes(child)


def _has_normalized_class_prefix(child: ETree.Element, prefix: str) -> bool:
    return any(name.startswith(prefix) for name in _get_normalized_classes(child))


__all__ = [
    "get_prefixes",
    "_normalize_language",
    "_add_query_param",
    "simplify_iri",
    "get_tag_name",
    "_get_normalized_classes",
    "_has_normalized_class",
    "_has_normalized_class_prefix",
]
