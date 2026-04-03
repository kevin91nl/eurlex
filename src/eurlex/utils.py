"""Compatibility helpers for legacy imports.

Prefer importing from the focused modules:
- `eurlex.language`
- `eurlex.uri`
- `eurlex.xml`
"""

from __future__ import annotations

from eurlex.language import _normalize_language
from eurlex.markup import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)
from eurlex.uri import _add_query_param, get_prefixes, simplify_iri

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
