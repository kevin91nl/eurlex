from __future__ import annotations

import datetime


def get_celex_id(
    slash_notation: str, document_type: str = "R", sector_id: str = "3"
) -> str:
    term1, term2 = slash_notation.split("/")
    current_year = datetime.datetime.now().year
    term1 = int(term1)
    term2 = int(term2)
    term1_is_year = 1800 <= term1 <= current_year
    term2_is_year = 1800 <= term2 <= current_year
    year = term2
    document_id = term1
    if term1_is_year and not term2_is_year:
        year = term1
        document_id = term2
    if term2_is_year and not term1_is_year:
        year = term2
        document_id = term1
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
    possible_ids = []
    for sector_id in sector_ids:
        for document_type in document_types:
            guess = get_celex_id(slash_notation, document_type, sector_id)
            possible_ids.append(guess)
    return possible_ids


__all__ = ["get_celex_id", "get_possible_celex_ids"]
