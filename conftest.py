from pathlib import Path

from pytest_readme import setup

setup()

generated = Path("test_readme.py")
target = Path("tests/test_readme.py")
if generated.exists():
    target.parent.mkdir(parents=True, exist_ok=True)
    generated.replace(target)
