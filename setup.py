#!/usr/bin/env python
"""Setup script for privacyforms.ai."""

import ast
from pathlib import Path

from setuptools import find_packages, setup


def _read_version() -> str:
    """Read __version__ from _version.py without importing the package.

    Works inside isolated build environments where the package is not yet
    importable; keeps _version.py as the single source of truth.
    """
    version_file = Path(__file__).parent / "src" / "privacyforms_ai" / "_version.py"
    tree = ast.parse(version_file.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("__version__ not found in src/privacyforms_ai/_version.py")


setup(
    name="privacyforms.ai",
    version=_read_version(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
