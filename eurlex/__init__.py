"""Compatibility package that exposes the source-layout EUR-Lex modules.

The repository uses a `src/` layout, but a legacy top-level `eurlex` package
also exists in the working tree. When pytest collects `src/eurlex/*.py` files,
Python may resolve `import eurlex` to this directory first. Extending the
package search path keeps the old import surface working while allowing
submodules such as `eurlex.celex` to resolve to `src/eurlex/celex.py`.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import rdflib
import requests
from SPARQLWrapper import JSON, SPARQLWrapper
from xml.etree import ElementTree as ETree

_PACKAGE_DIR = Path(__file__).resolve().parent
_SRC_PACKAGE_DIR = _PACKAGE_DIR.parent / "src" / "eurlex"

__path__ = [str(_PACKAGE_DIR), str(_SRC_PACKAGE_DIR)]

from .constants import *  # noqa: F401,F403
from .utils import *  # noqa: F401,F403
from .celex import *  # noqa: F401,F403
from .fetch import *  # noqa: F401,F403
from .parser import *  # noqa: F401,F403
from .sparql import *  # noqa: F401,F403

# Legacy module-level names used by the original monolithic package and by the
# existing test suite's monkeypatches.
__all__ = [name for name in globals() if not name.startswith("_")]
