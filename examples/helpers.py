from __future__ import annotations

from typing import TypedDict
from xml.etree import ElementTree as ETree

from eurlex.language import _normalize_language
from eurlex.uri import _add_query_param, get_prefixes, simplify_iri
from eurlex.xml import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)


class HelpersExampleResult(TypedDict):
    prefixes: list[str]
    language: dict[str, str]
    url: str
    iri: str
    tag: str
    classes: list[str]
    has_class: bool
    has_prefix: bool


def run_example() -> HelpersExampleResult:
    node = ETree.fromstring('<p class="oj-normal oj-note"></p>')
    return {
        "prefixes": list(get_prefixes())[:2],
        "language": _normalize_language("en-US"),
        "url": _add_query_param("https://example.com/doc", "language", "eng"),
        "iri": simplify_iri("http://publications.europa.eu/resource/cellar/abc"),
        "tag": get_tag_name("{http://www.w3.org/1999/xhtml}p"),
        "classes": _get_normalized_classes(node),
        "has_class": _has_normalized_class(node, "normal"),
        "has_prefix": _has_normalized_class_prefix(node, "no"),
    }


__all__ = ["HelpersExampleResult", "run_example"]
