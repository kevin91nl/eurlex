from __future__ import annotations

import datetime
from itertools import product


def get_celex_id(
    slash_notation: str, document_type: str = "R", sector_id: str = "3"
) -> str:
    term1, term2 = slash_notation.split("/")
    current_year = datetime.datetime.now().year
    term1_value = int(term1)
    term2_value = int(term2)
    term1_is_year = 1800 <= term1_value <= current_year
    term2_is_year = 1800 <= term2_value <= current_year
    year, document_id = (
        (term1_value, term2_value)
        if term1_is_year and not term2_is_year
        else (term2_value, term1_value)
    )
    return "{}{}{}{}".format(
        str(sector_id), year, document_type, str(document_id).zfill(4)
    )


def get_possible_celex_ids(
    slash_notation: str, document_type: str | None = None, sector_id: str | None = None
) -> list:
    sector_ids = (
        [str(i) for i in range(10)] + ["C", "E"]
        if sector_id is None
        else [str(sector_id)]
    )
    document_types = (
        ["L", "R", "E", "PC", "DC", "SC", "JC", "CJ", "CC", "CO"]
        if document_type is None
        else [document_type]
    )
    return [
        get_celex_id(slash_notation, document_type, sector_id)
        for sector_id, document_type in product(sector_ids, document_types)
    ]


__all__ = ["get_celex_id", "get_possible_celex_ids"]
