import sys
import types
from xml.etree import ElementTree as ETree

import eurlex
import eurlex.sparql as eurlex_sparql


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


def test_simplify_iri_converts_known_prefix():
    assert (
        eurlex.simplify_iri("http://publications.europa.eu/resource/cellar/abc")
        == "cellar:abc"
    )


def test_run_query_uses_sparqlwrapper(monkeypatch):
    fake_module = types.ModuleType("SPARQLWrapper")

    class FakeQueryResult:
        def convert(self):
            return {"results": "ok"}

    class FakeWrapper:
        def __init__(self, endpoint):
            self.endpoint = endpoint
            self.query_text = None
            self.format = None

        def setQuery(self, query):
            self.query_text = query

        def setReturnFormat(self, fmt):
            self.format = fmt

        def query(self):
            return FakeQueryResult()

    fake_module.JSON = object()
    fake_module.SPARQLWrapper = FakeWrapper
    monkeypatch.setitem(sys.modules, "SPARQLWrapper", fake_module)
    assert eurlex.run_query("SELECT * WHERE {}") == {"results": "ok"}


def test_get_celex_dataframe_builds_dataframe(monkeypatch):
    class FakeGraph:
        def parse(self, url):
            self.url = url
            return [
                ("http://example.com/s", "http://example.com/o", "http://example.com/p")
            ]

    monkeypatch.setattr(eurlex.rdflib, "Graph", FakeGraph)
    df = eurlex.get_celex_dataframe("32019R0947")
    assert df.to_dict(orient="records") == [
        {
            "s": "http://example.com/s",
            "o": "http://example.com/o",
            "p": "http://example.com/p",
        }
    ]


def test_guess_celex_ids_via_eurlex_uses_package_facade(monkeypatch):
    monkeypatch.setattr(
        eurlex_sparql, "get_possible_celex_ids", lambda *args, **kwargs: ["32019R0947"]
    )
    monkeypatch.setattr(eurlex, "prepend_prefixes", lambda query: query)
    monkeypatch.setattr(
        eurlex,
        "run_query",
        lambda _: {
            "results": {
                "bindings": [
                    {
                        "o": {
                            "value": "http://publications.europa.eu/resource/celex/abc"
                        }
                    },
                    {
                        "o": {
                            "value": "http://publications.europa.eu/resource/celex/def"
                        }
                    },
                ]
            }
        },
    )
    assert set(eurlex_sparql.guess_celex_ids_via_eurlex("2019/947")) == {"abc", "def"}


def test_get_celex_id_and_possibilities():
    assert eurlex.get_celex_id("2019/947") == "32019R0947"
    assert eurlex.get_celex_id("947/2019") == "32019R0947"
    filtered = eurlex.get_possible_celex_ids(
        "2019/947", document_type="R", sector_id="3"
    )
    assert filtered == ["32019R0947"]


def test_get_tag_name_non_string():
    assert eurlex.get_tag_name(123) == ""


def test_parse_modifiers_cover_all_modifiers():
    assert eurlex.parse_modifiers(ETree.fromstring('<p class="italic">Text</p>')) == [
        {"text": "Text", "type": "text", "modifier": "italic", "ref": [], "context": {}}
    ]
    assert eurlex.parse_modifiers(
        ETree.fromstring('<p class="signatory">Text</p>')
    ) == [
        {
            "text": "Text",
            "type": "text",
            "modifier": "signatory",
            "ref": [],
            "context": {},
        }
    ]
    assert eurlex.parse_modifiers(ETree.fromstring('<p class="note">Text</p>')) == [
        {"text": "Text", "type": "text", "modifier": "note", "ref": [], "context": {}}
    ]


def test_parse_span_delegates_to_modifiers():
    assert eurlex.parse_span(ETree.fromstring('<p class="italic">Text</p>')) == [
        {"text": "Text", "type": "text", "modifier": "italic", "ref": [], "context": {}}
    ]


def test_normalized_class_helpers():
    child = ETree.fromstring('<p class="oj-normal other"></p>')
    assert eurlex._get_normalized_classes(child) == ["normal", "other"]
    assert eurlex._has_normalized_class(child, "normal")
    assert eurlex._has_normalized_class_prefix(child, "oth")


def test_normalize_language_handles_empty_hyphenated_and_iso3_codes():
    assert eurlex._normalize_language(None) == {
        "header": "",
        "query": "",
        "stream": "",
    }
    assert eurlex._normalize_language("") == {"header": "", "query": "", "stream": ""}
    assert eurlex._normalize_language("en-US") == {
        "header": "en",
        "query": "eng",
        "stream": "EN",
    }
    assert eurlex._normalize_language("eng") == {
        "header": "en",
        "query": "eng",
        "stream": "EN",
    }


def test_normalize_language_handles_unrecognized_codes():
    assert eurlex._normalize_language("abcde") == {
        "header": "abcde",
        "query": "",
        "stream": "",
    }


def test_add_query_param_handles_missing_and_existing_values():
    base_url = "https://example.com/doc"
    assert eurlex._add_query_param(base_url, "language", "") == base_url
    assert (
        eurlex._add_query_param(
            "https://example.com/doc?language=eng", "language", "eng"
        )
        == "https://example.com/doc?language=eng"
    )
    assert eurlex._add_query_param(base_url, "language", "eng") == (
        "https://example.com/doc?language=eng"
    )


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
    tree = ETree.fromstring(
        "<html><table><tbody><tr><td><p>1</p></td></tr></tbody></table></html>"
    )
    assert eurlex.parse_article(tree) == []


def test_parse_article_span_branch():
    tree = ETree.fromstring("<html><span class='normal'>Text</span></html>")
    assert eurlex.parse_article(tree) == [
        {"text": "Text", "type": "text", "ref": [], "context": {}}
    ]


def test_parse_article_link_branch():
    tree = ETree.fromstring("<html><a>Link</a></html>")
    assert eurlex.parse_article(tree) == [
        {"text": "Link", "type": "link", "ref": [], "context": {}}
    ]


def test_parse_article_body_branch():
    tree = ETree.fromstring("<html><body><p class='normal'>Text</p></body></html>")
    results = eurlex.parse_article(tree)
    assert results[0]["text"] == "Text"


def test_parse_article_hr_branch():
    tree = ETree.fromstring("<html><hr /></html>")
    assert eurlex.parse_article(tree) == []


def test_parse_article_plain_paragraph_empty_returns_no_records():
    tree = ETree.fromstring("<html><p>   </p></html>")
    assert eurlex.parse_article(tree) == []


def test_parse_article_unknown_tag_returns_empty():
    tree = ETree.fromstring("<html><custom>Text</custom></html>")
    assert eurlex.parse_article(tree) == []


def test_parse_html_basic():
    df = eurlex.parse_html("<html><body><p class='normal'>Text</p></body></html>")
    assert df.to_dict(orient="records") == [
        {"text": "Text", "type": "text", "ref": [], "context": {}}
    ]


def test_parse_html_note_tag_replacement():
    html = (
        "<html><body><p class='normal'>Intro "
        '<a>(<span class="super note-tag">A1</span>)</a> end.</p></body></html>'
    )
    df = eurlex.parse_html(html)
    assert "[LINK = A1]" in df.text.values[0]


def test_parse_html_modern_note_tag_replacement():
    html = (
        "<html><body><p class='oj-normal'>Intro "
        "<a href='#n'>(<span class=\"oj-super oj-note-tag\">1</span>)</a> end.</p>"
        "</body></html>"
    )
    df = eurlex.parse_html(html)
    assert df.to_dict(orient="records") == [
        {"text": "Intro [LINK = 1] end.", "type": "text", "ref": [], "context": {}}
    ]


def test_parse_html_modern_markup_integration():
    html = (
        "<html><body>"
        "<p class='oj-doc-ti'>Modern Regulation</p>"
        "<p class='oj-ti-art'>Article 1</p>"
        "<p class='oj-sti-art'>Scope</p>"
        "<p class='oj-ti-grseq-1'>CHAPTER I</p>"
        "<p class='oj-ti-section-1'>General provisions</p>"
        "<p class='oj-normal'>1. Modern text</p>"
        "</body></html>"
    )
    df = eurlex.parse_html(html)
    assert df.to_dict(orient="records") == [
        {
            "text": "Modern text",
            "type": "text",
            "ref": [],
            "context": {
                "document": "Modern Regulation",
                "article": "1",
                "article_subtitle": "Scope",
                "group": "CHAPTER I",
                "section": "General provisions",
                "paragraph": "1",
            },
            "document": "Modern Regulation",
            "article": "1",
            "article_subtitle": "Scope",
            "group": "CHAPTER I",
            "section": "General provisions",
            "paragraph": "1",
        }
    ]


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


def test_parse_html_legacy_plain_paragraphs():
    html = (
        "<html><body><div id='TexteOnly'>"
        "<p>COUNCIL DIRECTIVE of 26 January 1965</p>"
        "<p>Article 1</p>"
        "<p>The specific criteria of purity are given in the Annex.</p>"
        "</div></body></html>"
    )
    df = eurlex.parse_html(html)
    assert df.to_dict(orient="records") == [
        {
            "text": "COUNCIL DIRECTIVE of 26 January 1965",
            "type": "text",
            "ref": [],
            "context": {},
        },
        {
            "text": "Article 1",
            "type": "text",
            "ref": [],
            "context": {},
        },
        {
            "text": "The specific criteria of purity are given in the Annex.",
            "type": "text",
            "ref": [],
            "context": {},
        },
    ]


def test_parse_multichoice_html_and_selection():
    html = (
        "<html><head><title>300 Multiple-Choice Response</title></head><body>"
        'List of URI\'s:<ul><li title="manifestation">cellar:test<ul>'
        '<li title="item"><a href="http://example.com/DOC_1">'
        '<span class="url">(http://example.com/DOC_1)</span></a>'
        '<ul><li title="stream_name">1_EN_ACT_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order" id="streamOrder">1</li></ul></li>'
        '<li title="item"><a href="http://example.com/DOC_3">'
        '<span class="url">(http://example.com/DOC_3)</span></a>'
        '<ul><li title="stream_name">1_EN_annexe_proposition_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order" id="streamOrder">3</li></ul></li>'
        "</ul></li></ul></body></html>"
    )
    items = eurlex._parse_multichoice_html(html)
    assert len(items) == 2
    selected = eurlex._select_multichoice_url(items, language="en")
    assert selected == "http://example.com/DOC_1"


def test_parse_multichoice_html_handles_missing_href_and_bad_order():
    html = (
        "<html><body><ul>"
        "<li title='item'><ul>"
        "<li title='stream_name'>BROKEN.html</li>"
        "<li title='stream_label'>act</li>"
        "<li title='stream_order'>abc</li>"
        "</ul></li>"
        "<li title='item'><a href='http://example.com/DOC_2'></a><ul>"
        "<li title='stream_name'>1_EN_ACT_part1_v7.html</li>"
        "<li title='stream_label'>act</li>"
        "<li title='stream_order'>abc</li>"
        "</ul></li>"
        "</ul></body></html>"
    )
    items = eurlex._parse_multichoice_html(html)
    assert items == [
        {
            "href": "http://example.com/DOC_2",
            "label": "act",
            "name": "1_EN_ACT_part1_v7.html",
            "order": None,
        }
    ]


def test_parse_multichoice_html_regex_fallback(monkeypatch):
    import lxml.html

    def boom(_):
        raise ValueError("boom")

    monkeypatch.setattr(lxml.html, "fromstring", boom)
    html = (
        '<li title="item"><a href="http://example.com/fallback"></a>'
        '<li title="stream_name">1_EN_ACT_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order">3</li>'
    )
    items = eurlex._parse_multichoice_html(html)
    assert items == [
        {
            "href": "http://example.com/fallback",
            "label": "act",
            "name": "1_EN_ACT_part1_v7.html",
            "order": 3,
        }
    ]


def test_parse_multichoice_html_regex_fallback_handles_bad_order(monkeypatch):
    import lxml.html

    def boom(_):
        raise ValueError("boom")

    monkeypatch.setattr(lxml.html, "fromstring", boom)
    html = (
        '<li title="item"><a href="http://example.com/fallback"></a>'
        '<li title="stream_name">1_EN_ACT_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order">abc</li>'
    )
    items = eurlex._parse_multichoice_html(html)
    assert items == [
        {
            "href": "http://example.com/fallback",
            "label": "act",
            "name": "1_EN_ACT_part1_v7.html",
            "order": None,
        }
    ]


def test_parse_multichoice_html_href_only_fallback(monkeypatch):
    import lxml.html

    def boom(_):
        raise ValueError("boom")

    monkeypatch.setattr(lxml.html, "fromstring", boom)
    items = eurlex._parse_multichoice_html(
        '<div><a href="http://example.com/only"></a></div>'
    )
    assert items == [
        {"href": "http://example.com/only", "label": "", "name": "", "order": None}
    ]


def test_select_multichoice_url_handles_empty_items():
    assert eurlex._select_multichoice_url([]) == ""


def test_normalize_language_maps_sv():
    norm = eurlex._normalize_language("sv")
    assert norm["header"] == "sv"
    assert norm["query"] == "swe"
    assert norm["stream"] == "SV"


def test_get_html_by_celex_id_multichoice_language_param(monkeypatch):
    multichoice_html = (
        "<html><head><title>300 Multiple-Choice Response</title></head><body>"
        'List of URI\'s:<ul><li title="manifestation">cellar:test<ul>'
        '<li title="item"><a href="http://example.com/DOC_1">'
        '<span class="url">(http://example.com/DOC_1)</span></a>'
        '<ul><li title="stream_name">1_EN_ACT_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order" id="streamOrder">1</li></ul></li>'
        '<li title="item"><a href="http://example.com/DOC_2">'
        '<span class="url">(http://example.com/DOC_2)</span></a>'
        '<ul><li title="stream_name">1_SV_ACT_part1_v7.html</li>'
        '<li title="stream_label">act</li>'
        '<li title="stream_order" id="streamOrder">1</li></ul></li>'
        "</ul></li></ul></body></html>"
    )
    calls = []

    class FakeResponse:
        def __init__(self, content: str, status_code: int = 200):
            self.content = content.encode("utf-8")
            self.status_code = status_code

    def fake_get(url, allow_redirects=True, timeout=None, headers=None):
        calls.append((url, headers))
        if "resource/celex/" in url:
            return FakeResponse(multichoice_html, status_code=300)
        return FakeResponse("<html><body><p class='normal'>Hej</p></body></html>")

    monkeypatch.setattr(eurlex.requests, "get", fake_get)
    html = eurlex.get_html_by_celex_id("52021PC0206", language="sv")
    assert "Hej" in html
    assert any(
        url.startswith("http://example.com/DOC_2") and "language=swe" in url
        for url, _ in calls
    )


def test_get_html_by_cellar_id_uses_language_and_prefix_stripping(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, content: str, status_code: int = 200):
            self.content = content.encode("utf-8")
            self.status_code = status_code

    def fake_get(url, allow_redirects=True, timeout=None, headers=None):
        calls.append((url, headers))
        return FakeResponse("<html><body><p class='normal'>Hej</p></body></html>")

    monkeypatch.setattr(eurlex.requests, "get", fake_get)
    html = eurlex.get_html_by_cellar_id("cellar:ABC", language="sv")
    assert "Hej" in html
    assert calls == [
        (
            "http://publications.europa.eu/resource/cellar/ABC?language=swe",
            {
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "sv",
            },
        )
    ]


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
