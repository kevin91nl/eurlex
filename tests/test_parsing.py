import pytest
from eurlex import get_html_by_celex_id, parse_html
import pandas as pd

from tests import _convert_outline


@pytest.mark.parametrize(
    "celex_id,header,ref,expected_text_or_text_count",
    [
        [
            "32019R0945",
            "Requirements for a class C0 Unmanned aircraft system",
            ["(8)", "(a)"],
            6,
        ],
        [
            "32019R0945",
            "Requirements for a class C0 Unmanned aircraft system",
            ["(1)"],
            "have an MTOM of less than 250 g, including payload;",
        ],
        [
            "32019R0945",
            "Definitions",
            ["(1)"],
            "‘unmanned aircraft’ (‘UA’) means any aircraft operating or designed to operate autonomously or to be piloted remotely without a pilot on board;",
        ],
        [
            "32019R0947",
            "UAS.OPEN.060 Responsibilities of the remote pilot",
            ["(2)", "(f)"],
            "comply with the operator's procedures when available.",
        ],
    ],
)
def test_paragraph_content(celex_id, header, ref, expected_text_or_text_count):
    html = get_html_by_celex_id(celex_id)
    df = parse_html(html)
    expected_text = None
    expected_text_count = 1
    if type(expected_text_or_text_count) == int:
        expected_text_count = expected_text_or_text_count
    if type(expected_text_or_text_count) == str:
        expected_text = expected_text_or_text_count
    assert df.shape[0] > 0, "No rows found for CELEX ID {}".format(celex_id)
    if "article_subtitle" not in df:
        df["article_subtitle"] = ""
    df = df[(df.group == header) | (df.article_subtitle == header)]
    assert df.shape[0] > 0, "No rows found for header {}".format(header)
    df = df[df.ref.apply("".join).str.startswith("".join(ref))]
    assert df.shape[0] > 0, "No rows found for reference {}".format(ref)
    assert df.shape[0] == expected_text_count, "Expected {} texts, but found {}".format(
        expected_text_count, df.shape[0]
    )
    assert (
        expected_text is None or df.text.values[0] == expected_text
    ), "Text is not as expected"


@pytest.mark.parametrize(
    "celex_id,header,expected_outline",
    [
        (
            "32019R0947",
            "UAS.SPEC.020 Operational declaration",
            {
                "(1)": {
                    "(a)": {"i.": None, "ii.": None, "iii.": None, "iv.": None},
                    "(b)": {"i.": None, "ii.": None},
                },
                "(2)": {"(a)": None, "(b)": None, "(c)": None, "(d)": None},
                "(3)": None,
                "(4)": None,
                "(5)": None,
                "(6)": None,
            },
        )
    ],
)
def test_outline(celex_id, header, expected_outline):
    html = get_html_by_celex_id(celex_id)
    df = parse_html(html)
    df = df[(df.group == header) | (df.article_subtitle == header)]
    assert (
        _convert_outline(df.ref.tolist()) == expected_outline
    ), "Outline is not as expected"


@pytest.mark.parametrize(
    "celex_id,expected_articles", [("32015R0220", 16), ("32019R0947", 23)]
)
def test_article_count(celex_id, expected_articles):
    html = get_html_by_celex_id(celex_id)
    df = parse_html(html)
    num_unique_articles = df[~pd.isna(df.article)].article.unique().shape[0]
    assert (
        num_unique_articles == expected_articles
    ), f"Wrong number of articles (found: {num_unique_articles}, expected: {expected_articles})"
