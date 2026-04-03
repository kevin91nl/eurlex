"""Compatibility wrapper for the EUR-Lex public API.

New code should import from `eurlex.public` or `eurlex`.
"""

from eurlex.public import *  # noqa: F401,F403
from eurlex.public import __all__ as __all__
