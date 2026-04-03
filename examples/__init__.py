"""Runnable EUR-Lex examples used by the test suite and coverage."""

from typing import TypedDict

from .fetching import FetchingExampleResult
from .fetching import run_example as run_fetching_example
from .helpers import HelpersExampleResult
from .helpers import run_example as run_helpers_example
from .parsing import ParsingExampleResult
from .parsing import run_example as run_parsing_example
from .queries import QueriesExampleResult
from .queries import run_example as run_queries_example


class AllExampleResults(TypedDict):
    helpers: HelpersExampleResult
    fetching: FetchingExampleResult
    parsing: ParsingExampleResult
    queries: QueriesExampleResult


def run_all_examples() -> AllExampleResults:
    return {
        "helpers": run_helpers_example(),
        "fetching": run_fetching_example(),
        "parsing": run_parsing_example(),
        "queries": run_queries_example(),
    }


__all__ = [
    "AllExampleResults",
    "run_all_examples",
    "run_fetching_example",
    "run_helpers_example",
    "run_parsing_example",
    "run_queries_example",
]
