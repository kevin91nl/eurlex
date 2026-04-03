from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from eurlex.constants import PREFIXES


def get_prefixes() -> dict[str, str]:
    return PREFIXES


def _add_query_param(url: str, key: str, value: str) -> str:
    if not value:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    if query.get(key) == value:
        return url
    query[key] = value
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def simplify_iri(iri: str) -> str:
    for prefix, url in PREFIXES.items():
        if iri.startswith(url):
            return prefix + ":" + iri[len(url) :]
    return iri


__all__ = ["get_prefixes", "_add_query_param", "simplify_iri"]
