"""Setup script for REST API Simulator"""

from setuptools import setup, find_packages

setup(
    name="rest-api-simulator",
    version="1.0.0",
    description="Advanced REST API Simulator and Load Testing Tool",
    author="REST API Simulator Team",
    packages=find_packages(),
    install_requires=[
        "textual>=0.47.1",
        "aiohttp>=3.9.1",
        "pydantic>=2.5.3",
        "rich>=13.7.0",
        "plotext>=5.2.8",
        "httpx>=0.26.0",
        "psutil>=5.9.6",
        "orjson>=3.9.10",
        "python-dateutil>=2.8.2",
        "tabulate>=0.9.0",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "rest-api-sim=main:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

