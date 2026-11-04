"""A running Podman container as a drive: ``podman://[user@]container/path``.

:mod:`navigator.lib.drives.docker` with ``podman`` spoken through: the two
command lines take the same words.  A module of its own because
:func:`available` is asked per scheme's module (``sessions.available``).
"""

from __future__ import annotations

from navigator.lib.drives import docker
from navigator.lib.drives.location import Site
from navigator.lib.drives.sessions import Answers

ENGINE = "podman"


def program() -> str | None:
    return docker.program(ENGINE)


def available() -> str | None:
    if program() is None:
        return "Podman needs the podman command"
    return None


def connect(site: Site, answers: Answers) -> docker.DockerDrive:
    return docker.connect_engine(ENGINE, site, answers)


def list_containers() -> list[docker.Container]:
    return docker.list_containers(ENGINE)


__all__ = ["ENGINE", "available", "connect", "list_containers", "program"]
