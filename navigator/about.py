"""What the About box says, read from the project's own metadata.

Nothing here is written twice.  The name, the summary, the licence, the author
and the home page are ``pyproject.toml``'s ``[project]`` table, and the version
is ``navigator.__version__``, which that table reads through
``[tool.setuptools.dynamic]``.

The table is found in one of two places, because ``pyproject.toml`` does not
reach an installed copy -- a wheel, a ``.deb`` or an ``.rpm`` carries the
packages and nothing beside them:

- **a checkout** has the file one directory above this package, and it is read
  with :mod:`tomllib`;
- **an installed copy** has the same table compiled into the distribution's
  ``METADATA``, read with :mod:`importlib.metadata`.

The file wins when it is there, for ``version_banner``'s reason turned round:
a checkout edited since it was last installed has a toml that says what it is
now and metadata that says what it was.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from email.utils import getaddresses
from functools import cache
from importlib import metadata
from pathlib import Path

from navigator import __version__

#: The distribution name, which is what both routes look the table up by.
DISTRIBUTION = "navigator-fm"

#: Where a checkout keeps the table: beside the ``navigator`` package.
PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


@dataclass(frozen=True)
class ProjectInfo:
    """The ``[project]`` facts the About box shows."""

    version: str
    summary: str = ""
    license: str = ""
    author: str = ""
    email: str = ""
    homepage: str = ""


@cache
def project_info() -> ProjectInfo:
    """The project's metadata: from ``pyproject.toml`` if this is a checkout, else as installed."""
    return _from_pyproject(PYPROJECT) or _from_metadata() or ProjectInfo(version=__version__)


def _from_pyproject(path: Path) -> ProjectInfo | None:
    try:
        with path.open("rb") as file:
            project = tomllib.load(file).get("project", {})
    except (OSError, tomllib.TOMLDecodeError):
        return None
    # A pyproject.toml above an installed package is somebody else's.
    if project.get("name") != DISTRIBUTION:
        return None
    authors = project.get("authors") or [{}]
    license = project.get("license", "")
    return ProjectInfo(
        version=project.get("version", __version__),
        summary=project.get("description", ""),
        # PEP 639's expression is a string; the older table form is not.
        license=license if isinstance(license, str) else license.get("text", ""),
        author=authors[0].get("name", ""),
        email=authors[0].get("email", ""),
        homepage=project.get("urls", {}).get("Homepage", ""),
    )


def _from_metadata() -> ProjectInfo | None:
    try:
        meta = metadata.metadata(DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return None
    # An author with a name and an address is written only to Author-email,
    # as `"Name" <address>'; one with a name alone goes to Author.
    author, email = "", ""
    if meta.get("Author-email"):
        author, email = getaddresses([meta["Author-email"]])[0]
    author = author or meta.get("Author", "")
    homepage = ""
    for entry in meta.get_all("Project-URL") or []:
        label, _, url = entry.partition(",")
        if label.strip().lower() == "homepage":
            homepage = url.strip()
            break
    return ProjectInfo(
        version=meta.get("Version", __version__),
        summary=meta.get("Summary", ""),
        license=meta.get("License-Expression") or meta.get("License", ""),
        author=author,
        email=email,
        homepage=homepage,
    )


def about_text(info: ProjectInfo) -> str:
    """The About box's text: DOS Navigator's ``dlAbout`` lines, with this project's facts.

    A fact the metadata does not carry is left out along with its line, and
    the blank lines only ever separate groups that have something in them.
    """
    author = f"{info.author} <{info.email}>" if info.author and info.email else info.author or info.email
    groups = [
        ["Navigator", f"Version {info.version}"],
        [info.summary],
        [author, f"License: {info.license}" if info.license else ""],
        [info.homepage],
    ]
    return "\n\n".join(
        "\n".join(line for line in group if line) for group in groups if any(group)
    )
