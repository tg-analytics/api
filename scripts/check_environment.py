"""Quick environment check for the FastAPI starter kit.

Run this script from the repository root to verify that the active Python environment
has the expected dependencies (particularly Pydantic v2+). It prints the versions of
key packages and highlights common issues.
"""

from __future__ import annotations

import shutil
import sys
from importlib import metadata
from typing import Iterable


def get_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def describe_versions(names: Iterable[str]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
        versions[name] = get_version(name)
    return versions


def main() -> None:
    print_section("Python")
    print(f"Executable: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")

    packages = ("pydantic", "pydantic-settings", "fastapi", "uvicorn")
    versions = describe_versions(packages)

    print_section("Dependency versions")
    for name in packages:
        version = versions[name] or "not installed"
        print(f"{name}: {version}")

    issues: list[str] = []

    pydantic_version = versions["pydantic"]
    if pydantic_version is None:
        issues.append("Pydantic is not installed. Install from requirements.txt.")
    elif pydantic_version.startswith("1."):
        issues.append(
            "Pydantic v2+ is required (v1 detected). Reinstall with the requirements file."
        )

    settings_version = versions["pydantic-settings"]
    if settings_version is None:
        issues.append("pydantic-settings is missing. Install from requirements.txt.")

    uvicorn_version = versions["uvicorn"]
    if uvicorn_version is None:
        issues.append("Uvicorn is missing. Install from requirements.txt.")

    print_section("Status")
    if issues:
        print("Found issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("All expected dependencies are present.")

    print_section("Quick fixes")
    print(
        "Use the Python executable above to reinstall dependencies if Pydantic v1 is still "
        "present. For example:\n"
        "  python -m pip install --upgrade --force-reinstall "
        "-r requirements.txt\n"
    )
    uvicorn_path = shutil.which("uvicorn") or "not found"
    print(f"uvicorn resolves to: {uvicorn_path}")
    print("If this points outside your virtual environment, activate the venv before running.")


if __name__ == "__main__":
    main()
