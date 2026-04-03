from __future__ import annotations

from eurlex.constants import ISO2_TO_ISO3, ISO3_TO_ISO2

_EMPTY_LANGUAGE = {"header": "", "query": "", "stream": ""}


def _normalize_language(language: str | None) -> dict[str, str]:
    if not isinstance(language, str) or not language.strip():
        return _EMPTY_LANGUAGE.copy()

    lang = language.strip().lower().split("-", 1)[0]

    if len(lang) == 2:
        return {
            "header": lang,
            "query": ISO2_TO_ISO3.get(lang, ""),
            "stream": lang.upper(),
        }

    if len(lang) == 3:
        header = ISO3_TO_ISO2.get(lang, lang)
        return {
            "header": header,
            "query": lang,
            "stream": header.upper(),
        }

    return {"header": lang, "query": "", "stream": ""}


__all__ = ["_normalize_language"]
