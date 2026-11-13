"""The one thing ``pyproject.toml`` cannot say: Help's pages live in ``docs/``,
at the top of the repository where GitHub shows them, and are installed as
``navigator/docs/`` (the ``navigator-help`` skill, *Shipping*).

A package named for a directory outside its parent has to be listed by hand,
and ``[tool.setuptools.packages.find]`` cannot list what it does not find --
so the packages are named here, and everything else stays in
``pyproject.toml``.  No symbolic link: a clone on a system without them
would get a text file in its place.
"""

from setuptools import find_packages, setup

setup(
    packages=[*find_packages(include=["navkit*", "navml*", "navigator*"]), "navigator.docs"],
    package_dir={"navigator.docs": "docs"},
)
