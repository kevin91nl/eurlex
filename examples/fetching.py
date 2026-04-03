from __future__ import annotations

from contextlib import contextmanager

import eurlex.fetch as fetch


class _FakeResponse:
    def __init__(self, content: str, status_code: int = 200):
        self.content = content.encode("utf-8")
        self.status_code = status_code


@contextmanager
def _patched_requests_get(fake_get):
    original = fetch.requests.get
    fetch.requests.get = fake_get
    try:
        yield
    finally:
        fetch.requests.get = original


def run_example() -> dict[str, object]:
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
    final_html = "<html><body><p class='normal'>Hej</p></body></html>"
    calls: list[str] = []

    def fake_get(url, allow_redirects=True, timeout=None, headers=None):
        calls.append(url)
        if "resource/celex/" in url:
            return _FakeResponse(multichoice_html, status_code=300)
        return _FakeResponse(final_html)

    with _patched_requests_get(fake_get):
        celex_html = fetch.get_html_by_celex_id("52021PC0206", language="sv")
        cellar_html = fetch.get_html_by_cellar_id("cellar:ABC", language="sv")

    items = fetch._parse_multichoice_html(multichoice_html)
    selected_en = fetch._select_multichoice_url(items, language="en")
    selected_sv = fetch._select_multichoice_url(items, language="sv")

    return {
        "celex_html": celex_html,
        "cellar_html": cellar_html,
        "selected_url_en": selected_en,
        "selected_url_sv": selected_sv,
        "parsed_order": fetch._parse_optional_int("3"),
        "call_count": len(calls),
    }


__all__ = ["run_example"]