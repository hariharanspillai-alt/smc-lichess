#!/usr/bin/env python3
"""Setup script for SMC Lichess Tournament Creator."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="smc-lichess-tournament-creator",
    version="1.0.0",
    author="SMC Chess Club",
    author_email="info@smcchess.org",
    description="CLI tool for automatically creating SMC Chess Club weekly Swiss tournaments on Lichess",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smc-chess/tournament-creator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "smc-create=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)