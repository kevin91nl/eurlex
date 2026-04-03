import sys
from pathlib import Path

from pytest_readme import setup

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

setup()

generated = ROOT / "test_readme.py"
legacy_target = ROOT / "tests" / "test_readme.py"
if legacy_target.exists():
    legacy_target.unlink()
