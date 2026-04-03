from __future__ import annotations

import sys
from typing import Any, Dict, List

import pandas as pd
import rdflib

from eurlex.celex import get_possible_celex_ids
from eurlex.uri import get_prefixes, simplify_iri


def prepend_prefixes(query: str) -> str:
    return (
        "\n".join(
            [
                "prefix {}: <{}>".format(prefix, url)
                for prefix, url in get_prefixes().items()
            ]
        )
        + " "
        + query
    )


def _run_prefixed_query(query: str) -> Any:
    package = sys.modules.get("eurlex")
    if package is not None:
        return package.run_query(package.prepend_prefixes(query).strip())
    return run_query(prepend_prefixes(query).strip())


def _binding_value(binding: dict, key: str) -> str:
    return binding[key]["value"]


def run_query(query: str) -> Any:
    from SPARQLWrapper import JSON, SPARQLWrapper

    sparql = SPARQLWrapper("http://publications.europa.eu/webapi/rdf/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results


def convert_sparql_output_to_dataframe(sparql_results: dict) -> pd.DataFrame:
    items = [
        {key: simplify_iri(item[key]["value"]) for key in item.keys()}
        for item in sparql_results["results"]["bindings"]
    ]
    return pd.DataFrame(items)


def get_celex_dataframe(celex_id: str) -> pd.DataFrame:
    graph = rdflib.Graph()
    results = graph.parse(
        f"http://publications.europa.eu/resource/celex/{str(celex_id)}?language=eng"
    )
    items = [
        {key: simplify_iri(str(item[key])) for key in range(len(item))}
        for item in results
    ]
    df = pd.DataFrame(items)
    df.columns = ["s", "o", "p"]
    return df


def guess_celex_ids_via_eurlex(
    slash_notation: str, document_type: str | None = None, sector_id: str | None = None
) -> list:
    slash_notation = "/".join(slash_notation.split("/")[:2])
    query = (
        "SELECT * WHERE {"
        + " UNION ".join(
            "{ ?s owl:sameAs celex:" + celex_id + " . ?s owl:sameAs ?o }"
            for celex_id in get_possible_celex_ids(
                slash_notation, document_type, sector_id
            )
        )
        + "}"
    )
    results = _run_prefixed_query(query)
    celex_ids = [
        value.split("/")[-1]
        for binding in results["results"]["bindings"]
        if "/celex/" in (value := _binding_value(binding, "o"))
    ]
    return list(dict.fromkeys(celex_ids))


def get_regulations(limit: int = -1, shuffle: bool = False) -> list:
    query = (
        "select ?doc where {?doc cdm:work_has_resource-type <http://publications.europa.eu/"
        "resource/authority/resource-type/REG_IMPL> . }"
        + (" order by rand()" if shuffle else "")
        + (f" limit {limit}" if limit > 0 else "")
    )
    results = _run_prefixed_query(query)
    return [
        _binding_value(result, "doc").split("/")[-1]
        for result in results["results"]["bindings"]
    ]


def get_documents(
    types: List[str] | None = None, limit: int = -1
) -> List[Dict[str, str]]:
    types = ["REG"] if types is None else types
    type_filter = " ||\n    ".join(
        f"?type=<http://publications.europa.eu/resource/authority/resource-type/{type}>"
        for type in types
    )
    query = (
        "select distinct ?doc ?type ?celex ?date\n"
        "where{ ?doc cdm:work_has_resource-type ?type.\n"
        f"  FILTER(\n    {type_filter}\n  )\n"
        "  FILTER(BOUND(?celex))\n"
        "  OPTIONAL{?doc cdm:resource_legal_id_celex ?celex.}\n"
        "  OPTIONAL{?doc cdm:work_date_document ?date.}\n"
        "}\n"
    )
    if limit > 0:
        query += f"limit {limit}"

    query_results = _run_prefixed_query(query)
    return [
        {
            "celex": _binding_value(result, "celex"),
            "date": _binding_value(result, "date"),
            "link": _binding_value(result, "doc"),
            "type": _binding_value(result, "type").split("/")[-1],
        }
        for result in query_results["results"]["bindings"]
    ]


__all__ = [
    "prepend_prefixes",
    "run_query",
    "convert_sparql_output_to_dataframe",
    "get_celex_dataframe",
    "guess_celex_ids_via_eurlex",
    "get_regulations",
    "get_documents",
]
