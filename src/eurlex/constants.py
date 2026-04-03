from __future__ import annotations

PREFIXES: dict[str, str] = {
    "cdm": "http://publications.europa.eu/ontology/cdm#",
    "celex": "http://publications.europa.eu/resource/celex/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "cellar": "http://publications.europa.eu/resource/cellar/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}

ISO2_TO_ISO3: dict[str, str] = {
    "bg": "bul",
    "cs": "ces",
    "da": "dan",
    "de": "deu",
    "el": "ell",
    "en": "eng",
    "es": "spa",
    "et": "est",
    "fi": "fin",
    "fr": "fra",
    "ga": "gle",
    "hr": "hrv",
    "hu": "hun",
    "it": "ita",
    "lt": "lit",
    "lv": "lav",
    "mt": "mlt",
    "nl": "nld",
    "pl": "pol",
    "pt": "por",
    "ro": "ron",
    "sk": "slk",
    "sl": "slv",
    "sv": "swe",
    "no": "nor",
}

ISO3_TO_ISO2: dict[str, str] = {value: key for key, value in ISO2_TO_ISO3.items()}

__all__ = ["PREFIXES", "ISO2_TO_ISO3", "ISO3_TO_ISO2"]
