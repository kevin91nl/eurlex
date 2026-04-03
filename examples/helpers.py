from __future__ import annotations

from xml.etree import ElementTree as ETree

from eurlex.language import _normalize_language
from eurlex.uri import _add_query_param, get_prefixes, simplify_iri
from eurlex.xml import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)


def run_example() -> dict[str, object]:
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


__all__ = ["run_example"]
