"""Utilities > *Remote shell*: what DOS Navigator's ``cmTerminal`` became.

DN's *Terminal* talked to a modem.  Here it is a shell at the other end of a
link, in a command window (``TerminalWindow``), one menu entry a protocol:
*SSH* -- a login shell on a server, ``ssh -t`` -- and, for the container and
device drives, ``docker exec -it`` / ``podman exec -it`` and ``adb shell``.
Which one, and where, is chosen in that protocol's link manager; nothing is
taken from the panel (asked for: a command whose behaviour follows what the
panel shows is an implicit one).

Of an SSH site only its host, user and port are passed: ``ssh`` reads
``~/.ssh/config`` -- HostName, Port, User, IdentityFile, ProxyJump -- just as
:func:`navigator.lib.drives.credentials.host_config` does for the SFTP drive,
so both reach the same machine as the same user.  A password or passphrase is
asked by ``ssh`` itself, in the window, which is a real terminal.
"""

from __future__ import annotations

import os
import shlex
import shutil

from navigator.lib.drives.location import Location, Site

#: The schemes a shell can be opened on: SSH's, the containers', a device's.
SCHEMES = frozenset({"sftp", "docker", "podman", "adb"})

#: The command each scheme's shell is run by.
PROGRAMS = {"sftp": "ssh", "docker": "docker", "podman": "podman", "adb": "adb"}


#: The status ``ssh`` exits with when it fails itself -- refused, unreachable,
#: authentication failed -- rather than passing on the remote shell's.
SSH_FAILED = 255


#: The statuses ``docker exec`` (and ``podman exec``) exit with when they fail
#: themselves: the daemon refused (125), nothing to run (126, 127).
EXEC_FAILED = frozenset({125, 126, 127})


def ended_well(status: int, scheme: str = "sftp") -> bool:
    """Whether a Remote shell that ended with wait *status* closes its window:
    the program exited -- Ctrl+D or ``exit`` there, with whatever status the
    shell's last command left -- and not with its own failure (``ssh``'s and
    ``adb``'s 255, the engines' 125-127), nor by a signal, either of which
    the window stays to show."""
    if not os.WIFEXITED(status):
        return False
    code = os.WEXITSTATUS(status)
    if scheme in ("docker", "podman"):
        return code not in EXEC_FAILED
    return code != SSH_FAILED


def program(scheme: str = "sftp") -> str | None:
    """Where *scheme*'s shell command is (``ssh``, ``docker``, ``podman``,
    ``adb``, which an Android SDK may hold off ``PATH``), or None when it is
    not installed."""
    if scheme == "adb":
        from navigator.lib.drives import adb

        return adb.program()
    return shutil.which(PROGRAMS.get(scheme, scheme))


def closes(scheme: str):
    """:func:`ended_well` for *scheme*, as ``run_in_window`` takes it."""
    return lambda status: ended_well(status, scheme)


def title(site: Site) -> str:
    """The shell window's title: ``ssh bob@host``, ``docker exec web``, ``adb shell R58M...``."""
    if site.scheme in ("docker", "podman"):
        user = f" -u {site.user}" if site.user else ""
        return f"{site.scheme} exec{user} {site.host}"
    if site.scheme == "adb":
        from navigator.lib.drives.adb import serial_of

        return f"adb shell {serial_of(site)}".rstrip()
    return f"ssh {login(site)}"


def login(site: Site) -> str:
    """*site* as ``ssh`` would be told it, for a title: ``user@host:port``."""
    user = f"{site.user}@" if site.user else ""
    host = f"[{site.host}]" if ":" in site.host and site.port else site.host
    port = f":{site.port}" if site.port else ""
    return f"{user}{host}{port}"


def words_of(text: str) -> list[str]:
    """*text* as the shell would split it -- quotes and all -- or by blanks
    when its quoting does not close."""
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def command(location: Location, options: str = "", forwards: list = ()) -> str:
    """The command line that logs in to *location*'s server and starts a
    login shell in its directory -- or the home directory, if that one has
    gone -- quoted for the local ``sh -c`` and the remote shell both.  With
    no directory (``profiles.HOME``, ``.``) the shell starts where ``ssh``
    puts it, the home directory.

    ``[remote] ssh_options`` (``-Y`` unless changed) come first, then the
    connection's own *options*, both before the host -- a later word wins
    where ``ssh`` lets one -- and its port *forwards* as ``-L``/``-R``/``-D``
    (:mod:`navigator.lib.drives.forwards`).  A local port an SFTP panel's
    connection already holds for the same forward is only warned about by
    ``ssh`` (*bind: Address already in use*), which carries on without it."""
    from navigator.lib.drives.forwards import ssh_words

    from navigator.settings import SETTINGS

    site = location.site
    if site.scheme in ("docker", "podman", "adb"):
        return _exec_command(location)
    remote = 'exec "${SHELL:-/bin/sh}" -l'
    if str(location.path) not in ("", "."):
        remote = f"cd {shlex.quote(str(location.path))} 2>/dev/null; {remote}"
    words = ["ssh", "-t", *words_of(SETTINGS.remote.ssh_options), *words_of(options), *ssh_words(list(forwards))]
    if site.port:
        words += ["-p", str(site.port)]
    if site.user:
        words += ["-l", site.user]
    words += ["--", site.host, remote]
    return shlex.join(words)


#: What puts a public key on a server: OpenSSH's own script.
COPY_ID = "ssh-copy-id"

#: What makes a key pair when there is none: ``ssh-keygen``.
KEYGEN = "ssh-keygen"


def copy_id_program() -> str | None:
    """Where ``ssh-copy-id`` is, or None (OpenSSH's client package has it)."""
    return shutil.which(COPY_ID)


def _copy_id_options(words: list[str]) -> list[str]:
    """Of ``ssh``'s flags, what ``ssh-copy-id`` passes on: ``-o`` options and
    ``-F``, and ``-J`` as ``-o ProxyJump=``.  The rest -- ``-Y``, ``-A``,
    forwards -- mean nothing to copying a key and it takes no others."""
    kept: list[str] = []
    index = 0
    while index < len(words):
        word = words[index]
        following = words[index + 1] if index + 1 < len(words) else None
        if word in ("-o", "-F") and following is not None:
            kept += [word, following]
            index += 2
            continue
        if word == "-J" and following is not None:
            kept += ["-o", f"ProxyJump={following}"]
            index += 2
            continue
        if word.startswith("-o") and len(word) > 2:
            kept += ["-o", word[2:]]
        elif word.startswith("-J") and len(word) > 2:
            kept += ["-o", f"ProxyJump={word[2:]}"]
        index += 1
    return kept


def copy_id_command(site: Site, key: str, options: str = "", *, generate: bool = False) -> str:
    """The command line that puts public key *key* (a ``.pub`` path) into
    *site*'s ``~/.ssh/authorized_keys`` -- ``ssh-copy-id``, which logs in
    with ``ssh`` and asks the password in the window it runs in.  With
    *generate* the key pair is made first (``ssh-keygen -t ed25519``, which
    asks a passphrase there too) and copied only once it is.  Of
    Communications' and the connection's *options* only what
    ``ssh-copy-id`` takes is passed (:func:`_copy_id_options`)."""
    from navigator.settings import SETTINGS

    words = [COPY_ID, "-i", key]
    if site.port:
        words += ["-p", str(site.port)]
    words += _copy_id_options([*words_of(SETTINGS.remote.ssh_options), *words_of(options)])
    words.append(f"{site.user}@{site.host}" if site.user else site.host)
    line = shlex.join(words)
    if generate:
        private = key[:-4] if key.endswith(".pub") else key
        line = f"{shlex.join([KEYGEN, '-t', 'ed25519', '-f', private])} && {line}"
    return line


def _exec_command(location: Location) -> str:
    """The command line for a shell in a container (``ENGINE exec -it``) or
    on a device (``adb shell``), in *location*'s directory -- the working
    directory or the device's own start, with none (``.``)."""
    site = location.site
    directory = "" if str(location.path) in ("", ".") else str(location.path)
    if site.scheme == "adb":
        from navigator.lib.drives.adb import command, serial_of

        serial = serial_of(site)
        words = [command(), *(["-s", serial] if serial else []), "shell", "-t"]
        if directory:
            # One word here, which adb hands the device's shell as its line.
            words.append(f"cd {shlex.quote(directory)} 2>/dev/null; exec sh")
        return shlex.join(words)
    words = [site.scheme, "exec", "-it"]
    if site.user:
        words += ["-u", site.user]
    if directory:
        words += ["-w", directory]
    words += [site.host, "sh", "-c", 'exec "${SHELL:-/bin/sh}" -l']
    return shlex.join(words)
