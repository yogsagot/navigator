"""SSH port forwards kept with a connection (``navigator/lib/drives/forwards.py``):
their lines, ``ssh``'s words for them, the SOCKS handshake a dynamic one
speaks, and *Copy key*'s ``ssh-copy-id`` command.  The tunnels themselves run
against a real paramiko server in ``tests/test_sftp.py``."""

from __future__ import annotations

import socket
import struct
import threading
from pathlib import PurePosixPath

import pytest

from navigator.lib.drives import forwards, remote_shell
from navigator.lib.drives.forwards import Forward
from navigator.lib.drives.location import Location, Site


@pytest.mark.parametrize("line, forward", [
    ("L 8080:db:5432", Forward("L", 8080, "", "db", 5432)),
    ("-L 0.0.0.0:8080:db:5432", Forward("L", 8080, "0.0.0.0", "db", 5432)),
    ("r *:9000:localhost:80", Forward("R", 9000, "*", "localhost", 80)),
    ("D 1080", Forward("D", 1080)),
    ("D [::1]:1080", Forward("D", 1080, "::1")),
    ("L [::1]:80:[fe80::1]:22", Forward("L", 80, "::1", "fe80::1", 22)),
    ("L 8080/db/5432", Forward("L", 8080, "", "db", 5432)),
])
def test_a_line_is_read_and_written_back_in_ssh_s_words(line, forward):
    assert forwards.parse_line(line) == forward
    assert forwards.parse_line(forward.line()) == forward


@pytest.mark.parametrize("line", ["X 1:a:2", "L 8080", "L 8080:db", "L 99999:db:1", "L 1:db:0", "D a",
                                  "L 1::2", "D 1:2:3"])
def test_a_bad_line_says_so(line):
    with pytest.raises(ValueError):
        forwards.parse_line(line)


def test_parse_skips_blanks_and_comments_and_leaves_bad_lines_out_unless_strict():
    text = "L 1:a:2\n\n# a note\nnonsense\nD 1080\n"
    with pytest.raises(ValueError):
        forwards.parse(text)
    found = forwards.parse(text, strict=False)
    assert found == [Forward("L", 1, "", "a", 2), Forward("D", 1080)]
    assert forwards.render(found) == "L 1:a:2\nD 1080"


def test_described_with_where_it_listens():
    assert forwards.describe(Forward("L", 8080, "", "db", 5432)) == "L 127.0.0.1:8080 → db:5432"
    assert forwards.describe(Forward("R", 0, "*", "localhost", 80), port=4321) == "R *:4321 → localhost:80"
    assert forwards.describe(Forward("D", 1080, "::1")) == "D [::1]:1080 (SOCKS)"


def test_remote_shell_passes_them_to_ssh_after_the_connection_s_options(monkeypatch):
    monkeypatch.setattr("navigator.settings.SETTINGS.remote.ssh_options", "-Y")
    place = Location(Site("sftp", "bob", "box", 2222), PurePosixPath("."))
    line = remote_shell.command(place, "-A", [Forward("L", 8080, "", "db", 5432), Forward("D", 1080)])
    assert line == "ssh -t -Y -A -L 8080:db:5432 -D 1080 -p 2222 -l bob -- box 'exec \"${SHELL:-/bin/sh}\" -l'"


def test_copy_id_takes_only_what_ssh_copy_id_understands(monkeypatch):
    monkeypatch.setattr("navigator.settings.SETTINGS.remote.ssh_options", "-Y")
    site = Site("sftp", "bob", "box", 2222)
    line = remote_shell.copy_id_command(site, "/h/.ssh/id_ed25519.pub", "-A -J jump -o Compression=yes -L 1:a:2")
    assert line == ("ssh-copy-id -i /h/.ssh/id_ed25519.pub -p 2222 -o ProxyJump=jump -o Compression=yes bob@box")
    made = remote_shell.copy_id_command(Site("sftp", "", "box", 0), "/h/.ssh/id_ed25519.pub", generate=True)
    assert made == "ssh-keygen -t ed25519 -f /h/.ssh/id_ed25519 && ssh-copy-id -i /h/.ssh/id_ed25519.pub box"


def test_public_keys_come_default_first(tmp_path, monkeypatch):
    from navigator.lib.drives import credentials

    monkeypatch.setattr(credentials, "ssh_directory", lambda: tmp_path)
    assert credentials.public_keys() == []
    for name in ("work.pub", "id_rsa.pub", "id_ed25519.pub", "known_hosts"):
        (tmp_path / name).write_text("x")
    assert [path.name for path in credentials.public_keys()] == ["id_ed25519.pub", "id_rsa.pub", "work.pub"]


# -- SOCKS ---------------------------------------------------------------------------------------


def _ask(*sent: bytes):
    """What :func:`forwards.socks_request` makes of a client sending *sent*,
    and what it answered back."""
    ours, theirs = socket.socketpair()
    result = {}

    def serve():
        try:
            result["request"] = forwards.socks_request(ours)
        except Exception as error:  # noqa: BLE001 - the test looks at which
            result["error"] = error
        ours.close()

    thread = threading.Thread(target=serve)
    thread.start()
    for part in sent:
        theirs.sendall(part)
    thread.join(5)
    theirs.settimeout(1)
    got = b""
    try:
        while part := theirs.recv(100):
            got += part
    except OSError:
        pass
    theirs.close()
    return result, got


def test_socks5_by_name_ipv4_and_ipv6():
    for kind, address, host in ((3, bytes([4]) + b"host", "host"), (1, bytes([10, 0, 0, 1]), "10.0.0.1"),
                                (4, socket.inet_pton(socket.AF_INET6, "::1"), "::1")):
        result, got = _ask(b"\x05\x02\x02\x00", bytes([5, 1, 0, kind]) + address + struct.pack("!H", 443))
        assert got == b"\x05\x00"
        request = result["request"]
        assert (request.version, request.host, request.port) == (5, host, 443)
        assert request.answer(True)[:2] == b"\x05\x00" and request.answer(False)[:2] == b"\x05\x05"


def test_socks5_refuses_what_it_cannot_do():
    result, got = _ask(b"\x05\x01\x02")
    assert got == b"\x05\xff" and isinstance(result["error"], forwards.SocksRefused)
    result, got = _ask(b"\x05\x01\x00", b"\x05\x02\x00\x01\x01\x02\x03\x04\x00\x50")  # BIND
    assert got.startswith(b"\x05\x00\x05\x07") and isinstance(result["error"], forwards.SocksRefused)


def test_socks4_and_4a():
    result, _ = _ask(b"\x04\x01" + struct.pack("!H", 80) + bytes([10, 0, 0, 2]) + b"me\0")
    assert (result["request"].host, result["request"].port) == ("10.0.0.2", 80)
    result, _ = _ask(b"\x04\x01" + struct.pack("!H", 80) + bytes([0, 0, 0, 1]) + b"\0" + b"example.org\0")
    request = result["request"]
    assert (request.version, request.host) == (4, "example.org")
    assert request.answer(True) == b"\x00\x5a" + b"\0" * 6
