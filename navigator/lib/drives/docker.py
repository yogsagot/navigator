"""A running container as a drive: ``docker://[user@]container/path``.

Every step is ``docker exec`` (:class:`~navigator.lib.drives.execdrive.ExecDrive`):
the container needs a POSIX ``sh`` and ``stat``, which every image with a
shell has -- GNU's, busybox's.  The site's host is the container's name or
ID, kept as written (names are case-sensitive); its user is ``exec -u``'s.
No connection is held: "connecting" is asking ``docker inspect`` that the
container is there and running, and a container stopped meanwhile is the
drive lost (*Disconnect* then sends its panels home).

:mod:`navigator.lib.drives.podman` is this module with ``podman`` for
:data:`ENGINE`: the two command lines take the same words.  What is running
is :func:`list_containers`, for the link manager's live part.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from navigator.lib.drives.base import CHMOD, CHOWN, FREE_SPACE, RENAME, SYMLINK, WRITE, DriveGone
from navigator.lib.drives.execdrive import ExecDrive
from navigator.lib.drives.location import Site
from navigator.lib.drives.sessions import Answers

#: The command spoken through.
ENGINE = "docker"

#: What the boxes call the engine.
ENGINE_NAME = "Docker"

#: Words in ``docker``'s own failure that say the container is gone: stopped,
#: removed, or the daemon not answering.
LOST_WORDS = ("is not running", "no such container", "cannot connect to the docker daemon",
              "container state improper", "is paused", "error during connect")


def program(engine: str = ENGINE) -> str | None:
    """Where *engine*'s command is, or None."""
    return shutil.which(engine)


def available() -> str | None:
    if program() is None:
        return f"{ENGINE_NAME} needs the {ENGINE} command"
    return None


def lost(text: str, status: int) -> str | None:
    """Why the container cannot be reached, from the engine's own *text*; None
    for a command that failed inside it.  The engine's own failures exit 125
    (the daemon's answer), 126 and 127 (nothing to run)."""
    lower = text.lower()
    if any(words in lower for words in LOST_WORDS):
        return " ".join(text.split()) or None
    if status == 125 and "error response from daemon" in lower:
        return " ".join(text.split())
    return None


class DockerDrive(ExecDrive):
    """A container's files, through ``ENGINE exec``."""

    capabilities = frozenset((WRITE, RENAME, SYMLINK, CHMOD, CHOWN, FREE_SPACE))

    def __init__(self, site: Site, *, engine: str = ENGINE, image: str = "", version: str = "") -> None:
        super().__init__(site)
        self.engine = engine
        self.image = image
        self.version = version

    def argv(self, words: list[str], *, stdin: bool = False) -> list[str]:
        argv = [self.engine, "exec"]
        if stdin:
            argv.append("-i")
        if self.site.user:
            argv += ["-u", self.site.user]
        return [*argv, self.site.host, *words]

    def lost(self, text: str, status: int) -> str | None:
        return lost(text, status)

    def missing_shell(self, text: str, status: int) -> bool:
        lower = text.lower()
        return status in (126, 127) and ("executable file not found" in lower or "no such file" in lower)

    def describe(self) -> list[tuple[str, str]]:
        facts = [("Container", self.site.host)]
        if self.image:
            facts.append(("Image", self.image))
        facts.append(("Engine", f"{self.engine} {self.version}".strip()))
        return facts


def inspect(engine: str, name: str) -> dict[str, Any]:
    """``ENGINE inspect`` of *name*: the container's record, or ``DriveGone``."""
    try:
        done = subprocess.run([engine, "inspect", "--type", "container", name], capture_output=True,
                              stdin=subprocess.DEVNULL, timeout=30)
    except FileNotFoundError as error:
        raise DriveGone(name, f"{engine}: command not found") from error
    except subprocess.TimeoutExpired as error:
        raise DriveGone(name, f"{engine} did not answer") from error
    if done.returncode != 0:
        text = " ".join(done.stderr.decode("utf-8", "replace").split())
        raise DriveGone(name, text or f"No such container: {name}")
    try:
        records = json.loads(done.stdout or b"[]")
    except ValueError as error:
        raise DriveGone(name, f"{engine} inspect said nothing readable") from error
    if not records:
        raise DriveGone(name, f"No such container: {name}")
    return records[0]


def _version(engine: str) -> str:
    try:
        done = subprocess.run([engine, "version", "--format", "{{.Server.Version}}"], capture_output=True,
                              stdin=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.decode("utf-8", "replace").strip() if done.returncode == 0 else ""


def connect_engine(engine: str, site: Site, answers: Answers) -> DockerDrive:
    """*site*'s container, there and running: blocks."""
    if not site.host:
        raise DriveGone(engine, "Name a container: docker://NAME/path")
    record = inspect(engine, site.host)
    state = record.get("State") or {}
    if not state.get("Running", False):
        raise DriveGone(site.host, f"Container {site.host} is not running")
    config = record.get("Config") or {}
    drive = DockerDrive(site, engine=engine, image=str(config.get("Image") or ""), version=_version(engine))
    workdir = str(config.get("WorkingDir") or "")
    drive.home = PurePosixPath(workdir) if workdir.startswith("/") else PurePosixPath("/")
    return drive


def connect(site: Site, answers: Answers) -> DockerDrive:
    return connect_engine(ENGINE, site, answers)


@dataclass(frozen=True)
class Container:
    """One running container, as ``ENGINE ps`` lists it."""

    name: str
    image: str = ""
    status: str = ""
    id: str = ""


def parse_ps(text: str) -> list[Container]:
    """``ENGINE ps --format '{{json .}}'``: a JSON object a line from Docker;
    Podman's ``Names`` is a list, and it may print one JSON array instead."""
    found: list[Container] = []
    text = text.strip()
    if not text:
        return found
    records: list[Any] = []
    if text.startswith("["):
        try:
            records = json.loads(text)
        except ValueError:
            records = []
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    for record in records:
        if not isinstance(record, dict):
            continue
        names = record.get("Names") or record.get("Name") or ""
        if isinstance(names, list):
            names = names[0] if names else ""
        name = str(names).split(",")[0].strip().lstrip("/")
        ident = str(record.get("ID") or record.get("Id") or "")
        if not name:
            name = ident[:12]
        if not name:
            continue
        found.append(Container(name, str(record.get("Image") or ""),
                               str(record.get("Status") or record.get("State") or ""), ident))
    return found


def list_containers(engine: str = ENGINE) -> list[Container]:
    """The containers running now (on a thread: it asks the daemon).  Raises
    ``OSError`` with the engine's words when it cannot say."""
    try:
        done = subprocess.run([engine, "ps", "--format", "{{json .}}"], capture_output=True,
                              stdin=subprocess.DEVNULL, timeout=30)
    except FileNotFoundError as error:
        raise OSError(f"{engine}: command not found") from error
    except subprocess.TimeoutExpired as error:
        raise OSError(f"{engine} did not answer") from error
    if done.returncode != 0:
        raise OSError(" ".join(done.stderr.decode("utf-8", "replace").split()) or f"{engine} ps failed")
    return parse_ps(done.stdout.decode("utf-8", "replace"))


__all__ = ["Container", "DockerDrive", "ENGINE", "available", "connect", "connect_engine", "inspect",
           "list_containers", "lost", "parse_ps", "program"]
