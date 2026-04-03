"""Runnable EUR-Lex examples used by the test suite and coverage."""

from .fetching import run_example as run_fetching_example
from .helpers import run_example as run_helpers_example
from .parsing import run_example as run_parsing_example
from .queries import run_example as run_queries_example


def run_all_examples() -> dict[str, object]:
    return {
        "helpers": run_helpers_example(),
        "fetching": run_fetching_example(),
        "parsing": run_parsing_example(),
        "queries": run_queries_example(),
    }


__all__ = [
    "run_all_examples",
    "run_fetching_example",
    "run_helpers_example",
    "run_parsing_example",
    "run_queries_example",
]
