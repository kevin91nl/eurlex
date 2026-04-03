from __future__ import annotations

import json
import ssl
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import certifi
from packaging.requirements import Requirement
from packaging.version import Version


def _load_runtime_requirements(pyproject_path: Path) -> list[Requirement]:
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    return [Requirement(item) for item in data["project"]["dependencies"]]


def _latest_pypi_version(package_name: str) -> Version:
    url = f"https://pypi.org/pypi/{package_name}/json"
    request = urllib.request.Request(url, headers={"User-Agent": "eurlex-pre-commit"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=15, context=context) as response:
        payload = json.load(response)
    return Version(payload["info"]["version"])


def main() -> int:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    outdated: list[tuple[str, str, str]] = []

    for requirement in _load_runtime_requirements(pyproject_path):
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue

        try:
            latest_version = _latest_pypi_version(requirement.name)
        except urllib.error.URLError as exc:
            print(
                f"Failed to query PyPI for {requirement.name}: {exc.reason}",
                file=sys.stderr,
            )
            return 1

        if latest_version not in requirement.specifier:
            current_spec = str(requirement.specifier) or "<unpinned>"
            outdated.append((requirement.name, current_spec, str(latest_version)))

    if outdated:
        print("Runtime dependencies are not fully up to date:")
        for package, current_spec, latest_version in outdated:
            print(f"- {package} ({current_spec}) -> latest on PyPI: {latest_version}")
        return 1

    print("Runtime dependencies are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
