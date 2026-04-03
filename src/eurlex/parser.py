from __future__ import annotations

import re
from xml.etree import ElementTree as ETree

import pandas as pd

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


def parse_span(child: ETree.Element, ref: list | None = None, context: dict | None = None) -> list:
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


def parse_article(tree: ETree.Element, ref: list | None = None, context: dict | None = None) -> list:
    namespaces = {"html": "http://www.w3.org/1999/xhtml"}
    ref = [] if ref is None else ref
    context = {} if context is None else context
    output = []
    new_context = context
    for child in tree:
        if get_tag_name(child.tag) in ["a"]:
            output.append(
                {
                    "text": _get_text(child),
                    "type": "link",
                    "ref": ref,
                    "context": new_context.copy(),
                }
            )
        elif get_tag_name(child.tag) == "p":
            if "class" in child.attrib:
                output.extend(parse_span(child, ref, new_context))
            else:
                text = "".join(child.itertext()).strip()
                if text:
                    output.append(
                        {
                            "text": text,
                            "type": "text",
                            "ref": ref,
                            "context": new_context.copy(),
                        }
                    )
        elif get_tag_name(child.tag) == "span":
            output.extend(parse_span(child, ref, new_context))
        elif get_tag_name(child.tag) == "table":
            results = child.findall(
                "html:tbody/html:tr/html:td", namespaces=namespaces
            ) + child.findall("tbody/tr/td", namespaces=namespaces)
            if (
                len(results) == 2
                and len(results[0]) == 1
                and get_tag_name(results[0][0].tag) == "p"
            ):
                key = None
                for subchild in results[0]:
                    key = _get_text(subchild)
                output.extend(parse_article(results[1], ref + [key], new_context))
        elif get_tag_name(child.tag) == "div":
            output.extend(parse_article(child, ref, new_context))
        elif get_tag_name(child.tag) in ["head", "hr"]:
            pass
        elif get_tag_name(child.tag) == "body":
            output.extend(parse_article(child, ref, context))
    return output


def parse_html(html: str) -> pd.DataFrame:
    tree = None
    try:
        modified_html = re.sub(
            r'<a[^>]*>\(<span class="(?:(?:oj-)?super) (?:(?:oj-)?note-tag)">([^<]*)</span>\)</a>',
            r"[LINK = \1]",
            html,
        )
        tree = ETree.fromstring(modified_html)
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
