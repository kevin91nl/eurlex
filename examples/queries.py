from __future__ import annotations

import sys
from contextlib import contextmanager
from types import ModuleType
from typing import Callable, TypedDict

import eurlex.celex as celex
import eurlex.sparql as sparql


class QueriesExampleResult(TypedDict):
    query: str
    converted: list[dict[str, object]]
    celex_id: str
    possible_ids: list[str]
    celex_frame: list[dict[str, object]]
    guessed: list[str]
    regulations: list[str]
    documents: list[dict[str, str]]
    fallback_prefixed_query: dict[str, str]


class _FakeEurlexModule(ModuleType):
    prepend_prefixes: Callable[[str], str]
    run_query: Callable[[str], object]


class _FakeGraph:
    def parse(self, url):
        self.url = url
        return [
            (
                "http://example.com/s",
                "http://example.com/o",
                "http://example.com/p",
            )
        ]


@contextmanager
def _patched_attr(obj, name, value):
    original = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, original)


@contextmanager
def _patched_package(run_query_result: Callable[[str], object]):
    original = sys.modules.get("eurlex")
    package = _FakeEurlexModule("eurlex")
    package.prepend_prefixes = lambda query: query
    package.run_query = lambda query: run_query_result(query)
    sys.modules["eurlex"] = package
    try:
        yield
    finally:
        if original is None:
            sys.modules.pop("eurlex", None)
        else:
            sys.modules["eurlex"] = original


def run_example() -> QueriesExampleResult:
    query = sparql.prepend_prefixes("SELECT ?name WHERE { ?person rdf:name ?name }")
    converted = sparql.convert_sparql_output_to_dataframe(
        {"results": {"bindings": [{"subject": {"value": "cdm:test"}}]}}
    ).to_dict(orient="records")

    with _patched_attr(sparql.rdflib, "Graph", _FakeGraph):
        celex_frame = sparql.get_celex_dataframe("32019R0947")

    with _patched_package(
        lambda query: {
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
        }
    ):
        guessed = sparql.guess_celex_ids_via_eurlex("2019/947")

    original_package = sys.modules.pop("eurlex", None)
    with _patched_package(
        lambda query: {
            "results": {
                "bindings": [
                    {
                        "doc": {"value": "http://example.com/cellar/abc"},
                    },
                    {
                        "doc": {"value": "http://example.com/cellar/def"},
                    },
                ]
            }
        }
    ):
        regulations = sparql.get_regulations()
    if original_package is not None:
        sys.modules["eurlex"] = original_package

    with _patched_package(
        lambda query: {
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
    ):
        documents = sparql.get_documents(types=["REG"], limit=1)

    with _patched_attr(sparql, "run_query", lambda query: {"prefixed": query}):
        original_package = sys.modules.pop("eurlex", None)
        try:
            fallback_prefixed_query = sparql._run_prefixed_query("SELECT ?x WHERE {}")
        finally:
            if original_package is not None:
                sys.modules["eurlex"] = original_package

    return {
        "query": query.splitlines()[0],
        "converted": converted,
        "celex_id": celex.get_celex_id("2019/947"),
        "possible_ids": celex.get_possible_celex_ids(
            "2019/947", document_type="R", sector_id="3"
        ),
        "celex_frame": celex_frame.to_dict(orient="records"),
        "guessed": guessed,
        "regulations": regulations,
        "documents": documents,
        "fallback_prefixed_query": fallback_prefixed_query,
    }


__all__ = ["QueriesExampleResult", "run_example"]
