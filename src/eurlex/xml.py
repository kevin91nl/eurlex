from __future__ import annotations

from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)


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
    "get_tag_name",
    "_get_normalized_classes",
    "_has_normalized_class",
    "_has_normalized_class_prefix",
]
