import pandas as pd
import pytest
from xml.etree import ElementTree as ETree

import eurlex


def test_get_prefixes_contains_expected_keys():
    prefixes = eurlex.get_prefixes()
    assert "cdm" in prefixes
    assert prefixes["cdm"].startswith("http")


def test_parse_article_paragraphs_handles_numbered_styles():
    article = "Lead text     1. First para     (2) Second para"
    paragraphs = eurlex.parse_article_paragraphs(article)
    assert paragraphs[None] == "Lead text"
    assert paragraphs["1."] == "First para"
    assert paragraphs["(2)"] == "Second para"


def test_prepend_prefixes_adds_prefix_block():
    query = "SELECT ?name WHERE { ?person rdf:name ?name }"
    with_prefixes = eurlex.prepend_prefixes(query)
    assert "prefix rdf" in with_prefixes
    assert query in with_prefixes


def test_convert_sparql_output_to_dataframe():
    data = {"results": {"bindings": [{"subject": {"value": "cdm:test"}}]}}
    df = eurlex.convert_sparql_output_to_dataframe(data)
    assert df.to_dict() == {"subject": {0: "cdm:test"}}


def test_get_celex_id_and_possibilities():
    assert eurlex.get_celex_id("2019/947") == "32019R0947"
    filtered = eurlex.get_possible_celex_ids("2019/947", document_type="R", sector_id="3")
    assert filtered == ["32019R0947"]


def test_get_tag_name_non_string():
    assert eurlex.get_tag_name(123) == ""


def test_normalized_class_helpers():
    child = ETree.fromstring('<p class="oj-normal other"></p>')
    assert eurlex._get_normalized_classes(child) == ["normal", "other"]
    assert eurlex._has_normalized_class(child, "normal")
    assert eurlex._has_normalized_class_prefix(child, "oth")


def test_get_text_empty_multiple_children():
    child = ETree.fromstring("<p><span></span><span></span></p>")
    assert eurlex._get_text(child) == ""


def test_parse_span_no_class_returns_empty():
    child = ETree.fromstring("<p>Text</p>")
    assert eurlex.parse_span(child) == []


def test_parse_article_table_ref():
    tree = ETree.fromstring(
        "<html><table>"
        "<tbody><tr><td><p>1</p></td><td><p class='normal'>Text</p></td></tr></tbody>"
        "</table></html>"
    )
    results = eurlex.parse_article(tree)
    assert results == [{"text": "Text", "type": "text", "ref": ["1"], "context": {}}]


def test_parse_article_table_no_match():
    tree = ETree.fromstring("<html><table><tbody><tr><td><p>1</p></td></tr></tbody></table></html>")
    assert eurlex.parse_article(tree) == []


def test_parse_article_body_branch():
    tree = ETree.fromstring("<html><body><p class='normal'>Text</p></body></html>")
    results = eurlex.parse_article(tree)
    assert results[0]["text"] == "Text"


def test_parse_article_hr_branch():
    tree = ETree.fromstring("<html><hr /></html>")
    assert eurlex.parse_article(tree) == []


def test_parse_html_basic():
    df = eurlex.parse_html("<html><body><p class='normal'>Text</p></body></html>")
    assert df.to_dict(orient="records") == [
        {"text": "Text", "type": "text", "ref": [], "context": {}}
    ]


def test_parse_html_note_tag_replacement():
    html = (
        "<html><body><p class='normal'>Intro "
        "<a>(<span class=\"super note-tag\">A1</span>)</a> end.</p></body></html>"
    )
    df = eurlex.parse_html(html)
    assert "[LINK = A1]" in df.text.values[0]


def test_parse_html_lxml_fallback():
    html = "<html><p class='normal'>Text</p>"  # invalid XML, triggers lxml fallback
    df = eurlex.parse_html(html)
    assert df.text.values[0] == "Text"


def test_parse_html_lxml_exception(monkeypatch):
    import lxml.html

    def boom(_):
        raise ValueError("boom")

    monkeypatch.setattr(lxml.html, "fromstring", boom)
    df = eurlex.parse_html("<html><p>")
    assert df.empty


def test_get_regulations_uses_run_query(monkeypatch):
    def fake_run_query(_):
        return {
            "results": {
                "bindings": [
                    {"doc": {"value": "http://example.com/cellar/abc"}},
                    {"doc": {"value": "http://example.com/cellar/def"}},
                ]
            }
        }

    monkeypatch.setattr(eurlex, "run_query", fake_run_query)
    assert eurlex.get_regulations() == ["abc", "def"]


def test_get_documents_uses_run_query(monkeypatch):
    def fake_run_query(_):
        return {
            "results": {
                "bindings": [
                    {
                        "celex": {"value": "32019R0947"},
                        "date": {"value": "2019-05-24"},
                        "doc": {"value": "http://example.com/doc/1"},
                        "type": {"value": "http://example.com/type/REG"},
                    }
                ]
            }
        }

    monkeypatch.setattr(eurlex, "run_query", fake_run_query)
    assert eurlex.get_documents(types=["REG"], limit=1) == [
        {
            "celex": "32019R0947",
            "date": "2019-05-24",
            "link": "http://example.com/doc/1",
            "type": "REG",
        }
    ]


def test_process_paragraphs_filters():
    good_text = ("A" * 99) + "."
    paragraphs = [
        {"celex_id": "1", "paragraph": "Done at 2021-11-25."},
        {"celex_id": "1", "paragraph": "It shall apply from 2024-01-01."},
        {"celex_id": "1", "paragraph": good_text},
        {"celex_id": "1", "paragraph": good_text},
        {"celex_id": "1", "paragraph": "lowercase starts here."},
        {"celex_id": "1", "paragraph": "Short."},
    ]
    df = eurlex.process_paragraphs(paragraphs)
    assert df.paragraph.tolist() == [good_text]


def test_process_paragraphs_empty_and_missing_column():
    assert eurlex.process_paragraphs([]).empty
    df = eurlex.process_paragraphs([{"celex_id": "1"}])
    assert "celex_id" in df.columns
