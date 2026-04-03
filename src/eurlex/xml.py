"""Compatibility wrapper for DOM helpers.

New code should import from `eurlex.markup`.
"""

from __future__ import annotations

from eurlex.markup import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)

__all__ = [
    "get_tag_name",
    "_get_normalized_classes",
    "_has_normalized_class",
    "_has_normalized_class_prefix",
]
