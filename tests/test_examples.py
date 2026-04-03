from __future__ import annotations

from examples import run_all_examples
from examples.fetching import run_example as run_fetching_example
from examples.helpers import run_example as run_helpers_example
from examples.parsing import run_example as run_parsing_example
from examples.queries import run_example as run_queries_example


def test_helpers_example_runs():
    result = run_helpers_example()
    assert result["language"]["query"] == "eng"
    assert result["iri"] == "cellar:abc"


def test_fetching_example_runs():
    result = run_fetching_example()
    assert result["celex_html"].startswith("<html>")
    assert result["selected_url_en"].endswith("DOC_1")
    assert result["selected_url_sv"].endswith("DOC_2")
    assert result["parsed_order"] == 3


def test_parsing_example_runs():
    result = run_parsing_example()
    assert result["records"][0]["article"] == "1"
    assert result["processed"]
    assert result["article_rows"]
    assert result["no_modifier"] == []
    assert result["empty_processed"] is True
    assert result["missing_column_processed"] == ["celex_id"]


def test_queries_example_runs():
    result = run_queries_example()
    assert result["celex_id"] == "32019R0947"
    assert set(result["guessed"]) == {"abc", "def"}
    assert result["documents"][0]["type"] == "REG"
    assert result["fallback_prefixed_query"]["prefixed"].startswith("prefix")


def test_all_examples_runs_everything():
    result = run_all_examples()
    assert set(result) == {"helpers", "fetching", "parsing", "queries"}