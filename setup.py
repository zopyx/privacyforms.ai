#!/usr/bin/env python
"""Setup script for privacyforms.ai."""

from setuptools import setup, find_packages

setup(
    name="privacyforms.ai",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
