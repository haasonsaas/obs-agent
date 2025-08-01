"""
Setup configuration for OBS Agent.
"""

import os
from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
here = Path(__file__).parent.absolute()
readme_path = here / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = here / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read version from package
version = "2.0.0"
version_file = here / "src" / "obs_agent" / "__version__.py"
if version_file.exists():
    exec(version_file.read_text())

setup(
    name="obs-agent",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered OBS Studio automation and control system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/obs-agent",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/obs-agent/issues",
        "Documentation": "https://obs-agent.readthedocs.io/",
        "Source Code": "https://github.com/yourusername/obs-agent",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.4.0",
            "sphinx>=7.1.0",
        ],
        "crew": [
            "crewai>=0.1.0",
            "langchain>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "obs-agent=obs_agent.cli:main",
            "obs-setup=obs_agent.scripts.setup:main",
            "obs-stream=obs_agent.scripts.stream:main",
        ],
    },
    include_package_data=True,
    package_data={
        "obs_agent": ["py.typed"],
    },
    zip_safe=False,
)