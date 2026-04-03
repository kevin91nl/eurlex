from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import pandas as pd
from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)

from eurlex.markup import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)

_ArticleChildHandler = Callable[[Any, list, dict], list[dict[str, object]]]

_PARAGRAPH_START_EXCLUSIONS = ("Done at", "It shall apply from")
_PARAGRAPH_END_EXCLUSIONS = (
    "is updated.",
    "is deleted.",
    "is removed.",
    "is hereby repealed.",
    "are updated.",
    "are deleted.",
    "are removed.",
)
_PARAGRAPH_CONTAINS_EXCLUSIONS = re.compile(
    r"is replaced by|is amended |is repealed with|[‘’]"
)


def _make_record(
    text: str,
    record_type: str,
    ref: list,
    context: dict,
    modifier: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "text": text,
        "type": record_type,
        "ref": ref,
        "context": context.copy(),
    }
    if modifier is not None:
        record["modifier"] = modifier
    return record


def parse_article_paragraphs(article: str) -> dict:
    paragraphs: dict[str | None, list[str]] = {}
    paragraph = None
    article = article.replace("     ", "\n")
    for line in article.split("\n"):
        match = re.match(r"^([0-9]+)[.]", line)
        if match:
            paragraph = match.group(0)
            line = ".".join(line.split(".")[1:]).strip()
        else:
            match = re.match(r"^[(]([0-9]+)[)]", line)
            if match:
                paragraph = match.group(0)
                line = ")".join(line.split(")")[1:]).strip()
        paragraphs.setdefault(paragraph, []).append(line)
    paragraph_texts = {
        paragraph: "\n".join(paragraphs[paragraph]).strip() for paragraph in paragraphs
    }
    return paragraph_texts


def parse_modifiers(
    child: Any, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    text = _get_text(child)
    modifier = next(
        (
            name
            for name in ("italic", "signatory", "note")
            if _has_normalized_class(child, name)
        ),
        None,
    )
    return (
        [_make_record(text, "text", ref, context, modifier=modifier)]
        if modifier is not None
        else []
    )


def _get_text(child: Any) -> str:
    return "".join(child.itertext()).strip()


def _parse_article_link(
    child: Any, ref: list, context: dict
) -> list[dict[str, object]]:
    return [_make_record(_get_text(child), "link", ref, context)]


def _parse_article_text(
    child: Any, ref: list, context: dict
) -> list[dict[str, object]]:
    text = _get_text(child)
    if not text:
        return []
    return [_make_record(text, "text", ref, context)]


def _parse_paragraph(child: Any, ref: list, context: dict) -> list[dict[str, object]]:
    if "class" in child.attrib:
        return parse_span(child, ref, context)
    return _parse_article_text(child, ref, context)


def _parse_article_table(
    child: Any, ref: list, context: dict
) -> list[dict[str, object]]:
    namespaces = {"html": "http://www.w3.org/1999/xhtml"}
    results = child.findall(
        "html:tbody/html:tr/html:td", namespaces=namespaces
    ) + child.findall("tbody/tr/td", namespaces=namespaces)
    if not (
        len(results) == 2
        and len(results[0]) == 1
        and get_tag_name(results[0][0].tag) == "p"
    ):
        return []

    key = None
    for subchild in results[0]:
        key = _get_text(subchild)
    return parse_article(results[1], ref + [key], context)


def _parse_article_child(
    child: Any, ref: list, context: dict
) -> list[dict[str, object]]:
    tag = get_tag_name(child.tag)
    handlers: dict[str, _ArticleChildHandler] = {
        "a": _parse_article_link,
        "p": _parse_paragraph,
        "span": parse_span,
        "table": _parse_article_table,
        "div": parse_article,
        "body": parse_article,
    }
    handler = handlers.get(tag)
    return handler(child, ref, context) if handler is not None else []


def _parse_span_doc_title(
    text: str, ref: list, context: dict
) -> list[dict[str, object]]:
    context["document"] = context.get("document", "") + text
    return [_make_record(text, "doc-title", ref, context)]


def _parse_span_art_subtitle(
    text: str, ref: list, context: dict
) -> list[dict[str, object]]:
    context["article_subtitle"] = text
    return [_make_record(text, "art-subtitle", ref, context)]


def _parse_span_art_title(
    text: str, ref: list, context: dict
) -> list[dict[str, object]]:
    context["article"] = text.replace("Article", "").strip()
    return [_make_record(text, "art-title", ref, context)]


def _parse_span_group_title(
    text: str, ref: list, context: dict
) -> list[dict[str, object]]:
    context["group"] = text
    return [_make_record(text, "group-title", ref, context)]


def _parse_span_section_title(
    text: str, ref: list, context: dict
) -> list[dict[str, object]]:
    context["section"] = text
    return [_make_record(text, "section-title", ref, context)]


def _parse_span_normal(text: str, ref: list, context: dict) -> list[dict[str, object]]:
    if re.match(r"^[0-9]+[.]", text):
        context["paragraph"] = text.split(".")[0]
        text = ".".join(text.split(".")[1:]).strip()
    return [_make_record(text, "text", ref, context)]


_SPAN_RULES = (
    (_has_normalized_class, "doc-ti", _parse_span_doc_title),
    (_has_normalized_class, "sti-art", _parse_span_art_subtitle),
    (_has_normalized_class, "ti-art", _parse_span_art_title),
    (_has_normalized_class_prefix, "ti-grseq-", _parse_span_group_title),
    (_has_normalized_class_prefix, "ti-section-", _parse_span_section_title),
    (_has_normalized_class, "normal", _parse_span_normal),
)


def parse_span(
    child: Any, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    if "class" not in child.attrib:
        return []
    text = _get_text(child)
    for predicate, class_name, handler in _SPAN_RULES:
        if predicate(child, class_name):
            return handler(text, ref, context)
    return parse_modifiers(child, ref, context)


def parse_article(
    tree: Any, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    for child in tree:
        output.extend(_parse_article_child(child, ref, context))
    return output


def parse_html(html: str) -> pd.DataFrame:
    tree = None
    try:
        note_tag_pattern = (
            r'<a[^>]*>\(<span class="(?:(?:oj-)?super) '
            r'(?:(?:oj-)?note-tag)">([^<]*)</span>\)</a>'
        )
        modified_html = re.sub(
            note_tag_pattern,
            r"[LINK = \1]",
            html,
        )
        tree = ETree.fromstring(modified_html)  # nosec B314 - XML is from EUR-Lex and validated via defusedxml/lxml fallback
    except ETree.ParseError:
        try:
            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)
        except Exception:
            return pd.DataFrame()
    records = [{**item, **item["context"]} for item in parse_article(tree)]
    df = pd.DataFrame.from_records(records)
    if "type" in df.columns:
        return df.loc[df["type"] == "text"].copy()
    return df


def process_paragraphs(paragraphs: list) -> pd.DataFrame:
    df_paragraphs = pd.DataFrame.from_records(paragraphs)
    if "paragraph" not in df_paragraphs.columns or df_paragraphs.empty:
        return df_paragraphs

    paragraph_text = df_paragraphs.paragraph.astype(str)
    include_mask = (
        paragraph_text.str.endswith(".")
        & paragraph_text.map(lambda text: str(text)[:1].isupper())
        & (paragraph_text.str.len() >= 100)
        & ~paragraph_text.str.startswith(_PARAGRAPH_START_EXCLUSIONS)
        & ~paragraph_text.str.endswith(_PARAGRAPH_END_EXCLUSIONS)
        & ~paragraph_text.str.contains(_PARAGRAPH_CONTAINS_EXCLUSIONS)
    )

    filtered = df_paragraphs.loc[include_mask].copy()
    return filtered.loc[~filtered["paragraph"].duplicated()].copy()


__all__ = [
    "parse_article_paragraphs",
    "parse_modifiers",
    "_get_text",
    "parse_span",
    "parse_article",
    "parse_html",
    "process_paragraphs",
    "_get_normalized_classes",
    "_has_normalized_class",
    "_has_normalized_class_prefix",
]
