from __future__ import annotations

import re

import pandas as pd
from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)

from .utils import (
    _get_normalized_classes,
    _has_normalized_class,
    _has_normalized_class_prefix,
    get_tag_name,
)


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
    child: ETree.Element, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    new_context = context.copy()
    if _has_normalized_class(child, "italic"):
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "italic",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    elif _has_normalized_class(child, "signatory"):
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "signatory",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    elif _has_normalized_class(child, "note"):
        output.append(
            {
                "text": _get_text(child),
                "type": "text",
                "modifier": "note",
                "ref": ref,
                "context": new_context.copy(),
            }
        )
    return output


def _get_text(child: ETree.Element) -> str:
    return "".join(child.itertext()).strip()


def _parse_article_link(
    child: ETree.Element, ref: list, context: dict
) -> list[dict[str, object]]:
    return [
        {
            "text": _get_text(child),
            "type": "link",
            "ref": ref,
            "context": context.copy(),
        }
    ]


def _parse_article_text(
    child: ETree.Element, ref: list, context: dict
) -> list[dict[str, object]]:
    text = "".join(child.itertext()).strip()
    if not text:
        return []
    return [
        {
            "text": text,
            "type": "text",
            "ref": ref,
            "context": context.copy(),
        }
    ]


def _parse_article_table(
    child: ETree.Element, ref: list, context: dict
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
    child: ETree.Element, ref: list, context: dict
) -> list[dict[str, object]]:
    tag = get_tag_name(child.tag)
    if tag == "a":
        return _parse_article_link(child, ref, context)
    if tag == "p":
        if "class" in child.attrib:
            return parse_span(child, ref, context)
        return _parse_article_text(child, ref, context)
    if tag == "span":
        return parse_span(child, ref, context)
    if tag == "table":
        return _parse_article_table(child, ref, context)
    if tag == "div":
        return parse_article(child, ref, context)
    if tag in ["head", "hr"]:
        return []
    if tag == "body":
        return parse_article(child, ref, context)
    return []


def parse_span(
    child: ETree.Element, ref: list | None = None, context: dict | None = None
) -> list:
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    if "class" not in child.attrib:
        return output
    if _has_normalized_class(child, "doc-ti"):
        if "document" not in context:
            context["document"] = ""
        context["document"] += _get_text(child)
        output.append(
            {
                "text": _get_text(child),
                "type": "doc-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif _has_normalized_class(child, "sti-art"):
        context["article_subtitle"] = _get_text(child)
        output.append(
            {
                "text": _get_text(child),
                "type": "art-subtitle",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif _has_normalized_class(child, "ti-art"):
        context["article"] = _get_text(child).replace("Article", "").strip()
        output.append(
            {
                "text": _get_text(child),
                "type": "art-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
    elif _has_normalized_class_prefix(child, "ti-grseq-"):
        output.append(
            {
                "text": _get_text(child),
                "type": "group-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
        context["group"] = _get_text(child)
    elif _has_normalized_class_prefix(child, "ti-section-"):
        output.append(
            {
                "text": _get_text(child),
                "type": "section-title",
                "ref": ref,
                "context": context.copy(),
            }
        )
        context["section"] = _get_text(child)
    elif _has_normalized_class(child, "normal"):
        text = _get_text(child)
        if re.match("^[0-9]+[.]", text):
            context["paragraph"] = text.split(".")[0]
            text = ".".join(text.split(".")[1:]).strip()
        output.append(
            {"text": text, "type": "text", "ref": ref, "context": context.copy()}
        )
    else:
        output.extend(parse_modifiers(child, ref, context))
    return output


def parse_article(
    tree: ETree.Element, ref: list | None = None, context: dict | None = None
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
    if "paragraph" not in df_paragraphs.columns:
        return df_paragraphs
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.startswith("Done at")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.startswith("It shall apply from")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is replaced by")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is updated.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is deleted.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is removed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("is hereby repealed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are updated.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are deleted.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.endswith("are removed.")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is amended ")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("is repealed with")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[df_paragraphs.paragraph.str.endswith(".")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[
            df_paragraphs.paragraph.apply(lambda text: text[0].upper() == text[0])
        ]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("‘")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[~df_paragraphs.paragraph.str.contains("’")]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs[df_paragraphs.paragraph.apply(len) >= 100]
        if len(df_paragraphs)
        else df_paragraphs
    )
    df_paragraphs = (
        df_paragraphs.drop_duplicates("paragraph")
        if len(df_paragraphs)
        else df_paragraphs
    )
    return df_paragraphs


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
