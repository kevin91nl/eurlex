from __future__ import annotations

from typing import TypedDict
from xml.etree import ElementTree as ETree

import eurlex.parser as parser


class ParsingExampleResult(TypedDict):
    records: list[dict[str, object]]
    paragraphs: dict[str | None, str]
    processed: list[dict[str, object]]
    article_rows: list[dict[str, object]]
    no_modifier: list[dict[str, object]]
    empty_processed: bool
    missing_column_processed: list[str]


def run_example() -> ParsingExampleResult:
    structured_html = (
        "<html><body>"
        "<p class='oj-doc-ti'>Modern Regulation</p>"
        "<p class='oj-ti-art'>Article 1</p>"
        "<p class='oj-sti-art'>Scope</p>"
        "<p class='oj-ti-grseq-1'>CHAPTER I</p>"
        "<p class='oj-ti-section-1'>General provisions</p>"
        "<p class='oj-normal'>1. Modern text</p>"
        "</body></html>"
    )
    df = parser.parse_html(structured_html)
    paragraphs = parser.parse_article_paragraphs(
        "Lead text     1. First para     (2) Second para"
    )
    processed = parser.process_paragraphs(
        [
            {"paragraph": "Done at 2021-11-25."},
            {"paragraph": "" + ("A" * 99) + "."},
        ]
    )
    article_rows = parser.parse_article(
        ETree.fromstring(
            "<html><body><p class='normal'>Text</p><a>Link</a></body></html>"
        )
    )
    no_modifier = parser.parse_modifiers(ETree.fromstring("<p class='plain'>Text</p>"))
    empty_processed = parser.process_paragraphs([]).empty
    missing_column_processed = parser.process_paragraphs(
        [{"celex_id": "1"}]
    ).columns.tolist()

    return {
        "records": df.to_dict(orient="records"),
        "paragraphs": paragraphs,
        "processed": processed.to_dict(orient="records"),
        "article_rows": article_rows,
        "no_modifier": no_modifier,
        "empty_processed": empty_processed,
        "missing_column_processed": missing_column_processed,
    }


__all__ = ["ParsingExampleResult", "run_example"]
