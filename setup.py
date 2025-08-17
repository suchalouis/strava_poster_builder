#!/usr/bin/env python3
"""
Setup script for Strava Poster Builder
Allows proper importing of project modules
"""

from setuptools import setup, find_packages
import os

# Use find_packages to automatically discover packages
def find_all_packages():
    """Find all packages in project-strava-api directory"""
    packages = []
    for root, dirs, files in os.walk("project-strava-api"):
        if "__init__.py" in files:
            # Convert path to module name
            package = root.replace(os.sep, ".").replace("project-strava-api", "project_strava_api")
            packages.append(package)
    return packages

# Simple setup to avoid conflicts with pyproject.toml
setup(
    name="strava-poster-builder-dev",  # Different name to avoid conflicts
    version="0.1.0",
    
    # Package configuration
    packages=find_all_packages(),
    package_dir={"project_strava_api": "project-strava-api"},
    
    # Include package data
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.svg", "*.png", "*.jpg"],
    },
    
    # Dependencies - minimal to avoid conflicts
    install_requires=[
        "requests>=2.32.4",
        "python-dotenv>=1.1.1",
        "aiohttp>=3.8.0",
    ],
    
    # Zip safe
    zip_safe=False,
)