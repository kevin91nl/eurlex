from __future__ import annotations

import re
from typing import Any

import pandas as pd
from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)

from .xml import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
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
    paragraphs = dict()
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
        if paragraph not in paragraphs:
            paragraphs[paragraph] = []
        paragraphs[paragraph].append(line)
    paragraphs = {
        paragraph: "\n".join(paragraphs[paragraph]).strip() for paragraph in paragraphs
    }
    return paragraphs


def parse_modifiers(
    child: Any, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    text = _get_text(child)
    for modifier in ("italic", "signatory", "note"):
        if _has_normalized_class(child, modifier):
            return [_make_record(text, "text", ref, context, modifier=modifier)]
    return []


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
    handlers = {
        "a": _parse_article_link,
        "p": _parse_paragraph,
        "span": parse_span,
        "table": _parse_article_table,
        "div": parse_article,
        "body": parse_article,
    }
    handler = handlers.get(tag)
    if handler is not None:
        return handler(child, ref, context)
    if tag in {"head", "hr"}:
        return []
    return []


def parse_span(
    child: Any, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    if "class" not in child.attrib:
        return output
    text = _get_text(child)
    if _has_normalized_class(child, "doc-ti"):
        if "document" not in context:
            context["document"] = ""
        context["document"] += text
        output.append(_make_record(text, "doc-title", ref, context))
    elif _has_normalized_class(child, "sti-art"):
        context["article_subtitle"] = text
        output.append(_make_record(text, "art-subtitle", ref, context))
    elif _has_normalized_class(child, "ti-art"):
        context["article"] = text.replace("Article", "").strip()
        output.append(_make_record(text, "art-title", ref, context))
    elif _has_normalized_class_prefix(child, "ti-grseq-"):
        output.append(_make_record(text, "group-title", ref, context))
        context["group"] = text
    elif _has_normalized_class_prefix(child, "ti-section-"):
        output.append(_make_record(text, "section-title", ref, context))
        context["section"] = text
    elif _has_normalized_class(child, "normal"):
        if re.match("^[0-9]+[.]", text):
            context["paragraph"] = text.split(".")[0]
            text = ".".join(text.split(".")[1:]).strip()
        output.append(_make_record(text, "text", ref, context))
    else:
        output.extend(parse_modifiers(child, ref, context))
    return output


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
    records = []
    for item in parse_article(tree):
        for key, value in item["context"].items():
            item[key] = value
        records.append(item)
    df = pd.DataFrame.from_records(records)
    df = df[df.type == "text"] if "type" in df.columns else df
    return df


def process_paragraphs(paragraphs: list) -> pd.DataFrame:
    df_paragraphs = pd.DataFrame.from_records(paragraphs)
    if "paragraph" not in df_paragraphs.columns or df_paragraphs.empty:
        return df_paragraphs

    paragraph_text = df_paragraphs.paragraph.astype(str)
    startswith_exclusions = ("Done at", "It shall apply from")
    endswith_exclusions = (
        "is updated.",
        "is deleted.",
        "is removed.",
        "is hereby repealed.",
        "are updated.",
        "are deleted.",
        "are removed.",
    )
    contains_exclusions = (
        "is replaced by",
        "is amended ",
        "is repealed with",
        "‘",
        "’",
    )

    include_mask = paragraph_text.str.endswith(".")
    include_mask &= paragraph_text.apply(
        lambda text: bool(text) and text[0].upper() == text[0]
    )
    include_mask &= paragraph_text.apply(len) >= 100
    include_mask &= ~paragraph_text.str.startswith(startswith_exclusions)
    include_mask &= ~paragraph_text.str.endswith(endswith_exclusions)
    include_mask &= ~paragraph_text.str.contains(
        "|".join(re.escape(token) for token in contains_exclusions)
    )

    return df_paragraphs[include_mask].drop_duplicates("paragraph")


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
