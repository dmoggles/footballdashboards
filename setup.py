"""Install packages as defined in this file into the Python environment."""
from typing import Any, Dict
from setuptools import setup, find_namespace_packages

# The version of this tool is based on the following steps:
# https://packaging.python.org/guides/single-sourcing-package-version/
VERSION: Dict[str, Any] = {}

with open("./footballdashboards/version.py") as fp:
    # pylint: disable=W0122
    exec(fp.read(), VERSION)

setup(
    name="footballdashboards",
    author="Dmitry Mogilevsky",
    author_email="dmitry.mogilevsky@gmail.com",
    description="Football Dashboards",
    version=VERSION.get("__version__", "0.0.0"),
    package_dir={".": "."},
    packages=find_namespace_packages(where="."),
    install_requires=[
        "setuptools>=45.0",
        "pandas",
        "requests",
        "mplsoccer @ git+http://github.com/dmoggles/mplsoccer",
        "footmav @ git+http://github.com/dmoggles/footmav",
        "seaborn",
        "scikit-learn",
        "scipy",
        "matplotlib==3.6.0",
        "tabulate",
        "cmasher",
        "adjustText",
        "jinja2",
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3.0",
        "Topic :: Utilities",
    ],
    package_data={"": ["*.ttf", "*.otf"]},
)
