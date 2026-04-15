#!/usr/bin/env python
"""Setup script for privacyforms.ai."""

from setuptools import find_packages, setup

setup(
    name="privacyforms.ai",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
