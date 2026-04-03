"""Central public API surface for the EUR-Lex package.

This module keeps the package facade easy to scan for new contributors while
allowing the package root to stay tiny.
"""

from __future__ import annotations

# ruff: noqa: F401

import pandas as pd
import rdflib
import requests
from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)
from SPARQLWrapper import JSON, SPARQLWrapper

from eurlex.celex import get_celex_id, get_possible_celex_ids
from eurlex.constants import ISO2_TO_ISO3, ISO3_TO_ISO2, PREFIXES
from eurlex.fetch import (
    DEFAULT_REQUEST_TIMEOUT,
    _build_multichoice_item,
    _build_request_headers,
    _get_html,
    _parse_multichoice_html,
    _parse_optional_int,
    _select_multichoice_url,
    get_html_by_celex_id,
    get_html_by_cellar_id,
)
from eurlex.language import _normalize_language
from eurlex.markup import get_tag_name
from eurlex.parser import (
    _get_normalized_classes,
    _get_text,
    _has_normalized_class,
    _has_normalized_class_prefix,
    parse_article,
    parse_article_paragraphs,
    parse_html,
    parse_modifiers,
    parse_span,
    process_paragraphs,
)
from eurlex.sparql import (
    convert_sparql_output_to_dataframe,
    get_celex_dataframe,
    get_documents,
    get_regulations,
    guess_celex_ids_via_eurlex,
    prepend_prefixes,
    run_query,
)
from eurlex.uri import _add_query_param, get_prefixes, simplify_iri

__all__ = [
    "pd",
    "rdflib",
    "requests",
    "ETree",
    "JSON",
    "SPARQLWrapper",
    "get_celex_id",
    "get_possible_celex_ids",
    "PREFIXES",
    "ISO2_TO_ISO3",
    "ISO3_TO_ISO2",
    "DEFAULT_REQUEST_TIMEOUT",
    "_build_multichoice_item",
    "_build_request_headers",
    "_get_html",
    "_parse_multichoice_html",
    "_parse_optional_int",
    "_select_multichoice_url",
    "get_html_by_cellar_id",
    "get_html_by_celex_id",
    "_normalize_language",
    "_get_normalized_classes",
    "_get_text",
    "_has_normalized_class",
    "_has_normalized_class_prefix",
    "parse_article",
    "parse_article_paragraphs",
    "parse_html",
    "parse_modifiers",
    "parse_span",
    "process_paragraphs",
    "convert_sparql_output_to_dataframe",
    "guess_celex_ids_via_eurlex",
    "get_celex_dataframe",
    "get_documents",
    "get_regulations",
    "prepend_prefixes",
    "run_query",
    "_add_query_param",
    "get_prefixes",
    "simplify_iri",
    "get_tag_name",
]
