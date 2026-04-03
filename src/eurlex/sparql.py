from __future__ import annotations

import sys
from typing import Any, Dict, List

import pandas as pd
import rdflib

from .celex import get_possible_celex_ids
from .uri import get_prefixes, simplify_iri


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
    queries = [
        "{ ?s owl:sameAs celex:" + celex_id + " . ?s owl:sameAs ?o }"
        for celex_id in get_possible_celex_ids(slash_notation, document_type, sector_id)
    ]
    query = "SELECT * WHERE {" + " UNION ".join(queries) + "}"
    results = _run_prefixed_query(query)
    celex_ids = []
    for binding in results["results"]["bindings"]:
        value = _binding_value(binding, "o")
        if "/celex/" in value:
            celex_ids.append(value.split("/")[-1])
    celex_ids = list(set(celex_ids))
    return celex_ids


def get_regulations(limit: int = -1, shuffle: bool = False) -> list:
    query = "select ?doc where {?doc cdm:work_has_resource-type <http://publications.europa.eu/"
    query += (
        "resource/authority/resource-type/REG_IMPL> . }"
        + (" order by rand()" if shuffle else "")
        + (" limit " + str(limit) if limit > 0 else "")
    )
    results = _run_prefixed_query(query)
    cellar_ids = []
    for result in results["results"]["bindings"]:
        cellar_ids.append(_binding_value(result, "doc").split("/")[-1])
    return cellar_ids


def get_documents(
    types: List[str] | None = None, limit: int = -1
) -> List[Dict[str, str]]:
    types = ["REG"] if types is None else types

    query = "select distinct ?doc ?type ?celex ?date\n"
    query += "where{ ?doc cdm:work_has_resource-type ?type.\n"
    query += "  FILTER(\n    "
    query += " ||\n    ".join(
        map(
            lambda type: (
                f"?type=<http://publications.europa.eu/resource/authority/resource-type/{type}>"
            ),
            types,
        )
    )
    query += "\n  )\n"
    query += "  FILTER(BOUND(?celex))\n"
    query += "  OPTIONAL{?doc cdm:resource_legal_id_celex ?celex.}\n"
    query += "  OPTIONAL{?doc cdm:work_date_document ?date.}\n"
    query += "}\n"
    if limit > 0:
        query += "limit " + str(limit)

    results = []
    query_results = _run_prefixed_query(query)

    for result in query_results["results"]["bindings"]:
        results.append(
            {
                "celex": _binding_value(result, "celex"),
                "date": _binding_value(result, "date"),
                "link": _binding_value(result, "doc"),
                "type": _binding_value(result, "type").split("/")[-1],
            }
        )

    return results


__all__ = [
    "prepend_prefixes",
    "run_query",
    "convert_sparql_output_to_dataframe",
    "get_celex_dataframe",
    "guess_celex_ids_via_eurlex",
    "get_regulations",
    "get_documents",
]
