"""Public package facade for the EUR-Lex parser.

Importing from `eurlex` stays supported for compatibility, while
`eurlex.public` is the easiest module to inspect for the curated public API.
"""

from eurlex.public import *  # noqa: F401,F403
from eurlex.public import __all__ as __all__
