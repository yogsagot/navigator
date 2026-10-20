"""Who a connection is, and what proves it: ``~/.ssh/config``, the host
keys ``ssh`` knows, and the passwords a desktop's keyring keeps.

**Nothing secret is written by Navigator.**  A password typed for a
connection lives in that connection's memory until it closes; it is kept
past that only when the user ticks *Save in keyring* and the ``keyring``
package is installed, which stores it wherever the desktop keeps its own
(GNOME Keyring, KWallet, macOS's Keychain).  Without the package the box is
not offered.  Keyring calls may wait on the desktop's bus, so each runs on a
thread, like everything else here.

Host keys are ``ssh``'s: ``~/.ssh/known_hosts`` (and the system's) is read,
an unknown key is asked about, and *Accept and save* appends it there in
the form ``ssh`` writes.  A key that changed is refused, as ``ssh`` refuses
it -- there is no button that accepts it.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from navigator.lib.drives.location import Site

#: The keyring's service name for every password Navigator keeps.
KEYRING_SERVICE = "navigator-fm"


def ssh_directory() -> Path:
    return Path(os.path.expanduser("~/.ssh"))


@dataclass
class HostConfig:
    """What ``~/.ssh/config`` says of a host, merged with what the site says."""

    hostname: str
    port: int
    user: str
    identity_files: list[str] = field(default_factory=list)
    proxy_command: str | None = None


def host_config(site: Site) -> HostConfig:
    """*site*'s host as ``ssh`` would reach it: ``Host`` blocks in
    ``~/.ssh/config`` matched, the site's own user and port winning."""
    import paramiko

    found: dict[str, Any] = {}
    config_path = ssh_directory() / "config"
    if config_path.is_file():
        try:
            found = paramiko.SSHConfig.from_path(str(config_path)).lookup(site.host)
        except (OSError, ValueError, paramiko.SSHException):
            found = {}
    port = site.port or int(found.get("port", 22) or 22)
    user = site.user or found.get("user") or _local_user()
    files = [os.path.expanduser(path) for path in found.get("identityfile", [])]
    hostname = found.get("hostname", site.host)
    proxy = found.get("proxycommand")
    jump = found.get("proxyjump")
    if proxy is None and jump and jump.lower() != "none":
        # ``ProxyJump``: through the system's ``ssh``, which reaches the jump
        # host with its own config, agent and keys -- as ``ssh -J`` does.
        import shlex

        proxy = f"ssh -W {shlex.quote(hostname)}:{port} {shlex.quote(jump.split(',')[0])}"
    return HostConfig(hostname, port, user, [path for path in files if os.path.isfile(path)], proxy)


def _local_user() -> str:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return ""


# -- host keys -------------------------------------------------------------------------------------


def fingerprint(key: Any) -> str:
    """``SHA256:...``, as ``ssh`` shows a key."""
    digest = hashlib.sha256(key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode().rstrip("=")


def known_name(hostname: str, port: int) -> str:
    """The name ``known_hosts`` files a host under: ``[host]:port`` off 22."""
    return hostname if port == 22 else f"[{hostname}]:{port}"


def save_host_key(hostname: str, port: int, key: Any) -> None:
    """*key* appended to ``~/.ssh/known_hosts``, as ``ssh`` appends one."""
    directory = ssh_directory()
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / "known_hosts"
    line = f"{known_name(hostname, port)} {key.get_name()} {key.get_base64()}\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="ascii") as file:
        file.write(line)


# -- passwords ---------------------------------------------------------------------------------------


def keyring_available() -> bool:
    """Whether a keyring is there to keep passwords in: the package, with a
    backend that is not the one that refuses everything."""
    try:
        import keyring
        from keyring.backends import fail
    except Exception:
        return False
    try:
        return not isinstance(keyring.get_keyring(), fail.Keyring)
    except Exception:
        return False


def account(site: Site) -> str:
    """The keyring account a site's password is kept under."""
    return str(site)


def saved_password(site: Site) -> str | None:
    """The password kept for *site*, or None -- also when there is no keyring."""
    if not keyring_available():
        return None
    import keyring

    try:
        return keyring.get_password(KEYRING_SERVICE, account(site))
    except Exception:
        return None


def save_password(site: Site, password: str) -> bool:
    """*password* kept for *site*; False when the keyring would not."""
    if not keyring_available():
        return False
    import keyring

    try:
        keyring.set_password(KEYRING_SERVICE, account(site), password)
    except Exception:
        return False
    return True


def forget_password(site: Site) -> None:
    if not keyring_available():
        return
    import keyring

    try:
        keyring.delete_password(KEYRING_SERVICE, account(site))
    except Exception:
        pass


__all__ = [
    "HostConfig", "KEYRING_SERVICE", "account", "fingerprint", "forget_password", "host_config",
    "keyring_available", "known_name", "save_host_key", "save_password", "saved_password",
]
