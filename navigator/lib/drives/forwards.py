"""SSH port forwards kept with a connection: ``ssh -L``, ``-R`` and ``-D``.

A departure from DOS Navigator, asked for: its link was a serial cable, with
nothing to tunnel.  The SSH link manager keeps a connection's forwards
(``RemoteProfile.forwards``), one a line in ``ssh``'s own words:

- ``L [bind:]port:host:hostport`` -- a port here, each connection to it
  carried to *host*:*hostport* as the server sees it (``direct-tcpip``);
- ``R [bind:]port:host:hostport`` -- a port on the server, each connection
  to it carried back to *host*:*hostport* as this machine sees it
  (``tcpip-forward``);
- ``D [bind:]port`` -- a SOCKS 4/4a/5 proxy here, each connection carried to
  where it asks (``direct-tcpip`` again).

They are used twice.  :func:`ssh_words` hands them to Remote shell's ``ssh``
as its flags; and :class:`Tunnels` opens them over a panel's paramiko
connection (:mod:`navigator.lib.drives.sftp`) while it is up -- again after
its one silent reconnect -- and says in the information panel which are
listening and why one is not.  A bind address left out is the loopback, as
``ssh``'s own ``GatewayPorts no``; ``*`` is every address.

Everything here but :class:`Tunnels` is plain text; nothing imports paramiko.
"""

from __future__ import annotations

import ipaddress
import selectors
import socket
import struct
import threading
from dataclasses import dataclass, field
from typing import Any

#: The three kinds, by the letter ``ssh`` takes them by.
KINDS = ("L", "R", "D")

#: Where a forward listens when its line names nowhere: the loopback, as
#: ``ssh`` binds (``GatewayPorts no``).
LOOPBACK = "127.0.0.1"

#: How long a SOCKS client has to say where it is going.
HANDSHAKE_TIMEOUT = 10.0

#: How long a ``select`` waits before looking whether the tunnels are stopping.
POLL = 0.5

CHUNK = 32768


@dataclass(frozen=True)
class Forward:
    """One forward: its kind, where it listens, and where it goes (not a
    dynamic one's: the SOCKS client says)."""

    kind: str
    port: int
    #: Where it listens; ``""`` as written -- the loopback.
    bind: str = ""
    host: str = ""
    host_port: int = 0

    @property
    def listen_address(self) -> str:
        """The address it listens on: the loopback unless one is named,
        ``""`` (every address) for ``*``."""
        if self.bind == "*":
            return ""
        return self.bind or (LOOPBACK if self.kind != "R" else "localhost")

    def spec(self) -> str:
        """What follows ``-L``/``-R``/``-D`` in ``ssh``'s words: ``8080:db:5432``."""
        parts = [_bracketed(self.bind)] if self.bind else []
        parts.append(str(self.port))
        if self.kind != "D":
            parts += [_bracketed(self.host), str(self.host_port)]
        return ":".join(parts)

    def line(self) -> str:
        """Its line as kept: ``L 8080:db:5432``."""
        return f"{self.kind} {self.spec()}"


def _bracketed(host: str) -> str:
    return f"[{host}]" if ":" in host else host


def _split(spec: str) -> list[str]:
    """*spec* split at its colons, a ``[...]`` IPv6 address one part --
    or at ``/``, which ``ssh`` takes too."""
    if "/" in spec and "[" not in spec:
        return spec.split("/")
    parts, current, depth = [], "", 0
    for char in spec:
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == ":" and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    return [part[1:-1] if part.startswith("[") and part.endswith("]") else part for part in parts]


def _port(text: str, line: str, *, zero: bool = True) -> int:
    if not text.isdigit() or not (0 if zero else 1) <= int(text) <= 65535:
        raise ValueError(f"{line}: {text or 'nothing'} is no port")
    return int(text)


def parse_line(line: str) -> Forward:
    """One forward's line -- ``L 8080:db:5432``, ``-D 1080``, ``R *:9000:localhost:80``.
    Raises ``ValueError`` saying what is wrong with it."""
    text = line.strip()
    head, _, spec = text.partition(" ")
    kind = head.lstrip("-").upper()
    if kind not in KINDS:
        raise ValueError(f"{text}: not L, R or D")
    spec = spec.strip()
    parts = _split(spec)
    if kind == "D":
        if len(parts) == 1:
            return Forward("D", _port(parts[0], text))
        if len(parts) == 2:
            return Forward("D", _port(parts[1], text), parts[0])
        raise ValueError(f"{text}: D takes [address:]port")
    if len(parts) == 3:
        bind, (port, host, host_port) = "", parts
    elif len(parts) == 4:
        bind, port, host, host_port = parts
    else:
        raise ValueError(f"{text}: {kind} takes [address:]port:host:hostport")
    if not host:
        raise ValueError(f"{text}: no host to go to")
    return Forward(kind, _port(port, text), bind, host, _port(host_port, text, zero=False))


def parse(text: str, *, strict: bool = True) -> list[Forward]:
    """Every forward in *text*, one a line; blank lines and ``#`` comments
    skipped.  A bad line raises ``ValueError`` -- or, not *strict*, is left out."""
    found = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            found.append(parse_line(line))
        except ValueError:
            if strict:
                raise
    return found


def render(forwards: list[Forward]) -> str:
    """*forwards* as they are kept, one a line."""
    return "\n".join(forward.line() for forward in forwards)


def describe(forward: Forward, port: int | None = None) -> str:
    """*forward* in words for a list or the information panel:
    ``L 127.0.0.1:8080 → db:5432``.  *port* is the one actually bound, for
    a forward asking for any (0)."""
    listen = forward.listen_address or "*"
    where = f"{_bracketed(listen)}:{port if port else forward.port}"
    if forward.kind == "D":
        return f"D {where} (SOCKS)"
    return f"{forward.kind} {where} → {_bracketed(forward.host)}:{forward.host_port}"


def ssh_words(forwards: list[Forward]) -> list[str]:
    """*forwards* as ``ssh``'s flags: ``["-L", "8080:db:5432", "-D", "1080"]``."""
    words: list[str] = []
    for forward in forwards:
        words += [f"-{forward.kind}", forward.spec()]
    return words


# -- SOCKS ---------------------------------------------------------------------------------------


class SocksRefused(Exception):
    """What a SOCKS client asked cannot be done: not CONNECT, no method."""


def _exactly(sock: socket.socket, count: int) -> bytes:
    data = b""
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:
            raise ConnectionError("the SOCKS client went away")
        data += part
    return data


def _until_nul(sock: socket.socket) -> bytes:
    data = b""
    while True:
        byte = _exactly(sock, 1)
        if byte == b"\0":
            return data
        data += byte
        if len(data) > 255:
            raise SocksRefused("SOCKS 4 field too long")


@dataclass
class SocksRequest:
    """Where a SOCKS client asked to go, and how to answer it."""

    version: int
    host: str
    port: int

    def answer(self, ok: bool) -> bytes:
        """The reply to send: success, or *connection refused*."""
        if self.version == 4:
            return bytes([0, 0x5A if ok else 0x5B]) + b"\0\0\0\0\0\0"
        return bytes([5, 0 if ok else 5, 0, 1]) + b"\0\0\0\0\0\0"


def socks_request(sock: socket.socket) -> SocksRequest:
    """Read a SOCKS 4, 4a or 5 client's request from *sock* (no
    authentication, CONNECT only), answering its greeting.  Raises
    :class:`SocksRefused` -- having told the client -- or ``OSError``."""
    version = _exactly(sock, 1)[0]
    if version == 4:
        command, port = struct.unpack("!BH", _exactly(sock, 3))
        address = _exactly(sock, 4)
        _until_nul(sock)  # the user id
        if command != 1:
            sock.sendall(SocksRequest(4, "", 0).answer(False))
            raise SocksRefused("SOCKS 4: only CONNECT")
        if address[:3] == b"\0\0\0" and address[3]:
            host = _until_nul(sock).decode("idna")  # 4a: a name to resolve over there
        else:
            host = str(ipaddress.IPv4Address(address))
        return SocksRequest(4, host, port)
    if version != 5:
        raise SocksRefused(f"SOCKS version {version}")
    methods = _exactly(sock, _exactly(sock, 1)[0])
    if 0 not in methods:
        sock.sendall(b"\x05\xff")
        raise SocksRefused("SOCKS 5: no method without authentication")
    sock.sendall(b"\x05\x00")
    _, command, _, kind = _exactly(sock, 4)
    if kind == 1:
        host = str(ipaddress.IPv4Address(_exactly(sock, 4)))
    elif kind == 3:
        host = _exactly(sock, _exactly(sock, 1)[0]).decode("idna")
    elif kind == 4:
        host = str(ipaddress.IPv6Address(_exactly(sock, 16)))
    else:
        sock.sendall(b"\x05\x08\x00\x01" + b"\0" * 6)
        raise SocksRefused(f"SOCKS 5: address type {kind}")
    (port,) = struct.unpack("!H", _exactly(sock, 2))
    if command != 1:
        sock.sendall(b"\x05\x07\x00\x01" + b"\0" * 6)
        raise SocksRefused("SOCKS 5: only CONNECT")
    return SocksRequest(5, host, port)


# -- the tunnels ---------------------------------------------------------------------------------


def _close(each: Any) -> None:
    try:
        each.close()
    except Exception:
        pass


def _reason(error: BaseException) -> str:
    return getattr(error, "strerror", None) or str(error) or type(error).__name__


@dataclass
class Opened:
    """One forward as :class:`Tunnels` opened it: the port it got, or why not."""

    forward: Forward
    #: The port actually listened on (a forward asking 0 gets one); 0 if none.
    port: int = 0
    #: Why it is not listening; ``""`` when it is.
    error: str = ""

    def describe(self) -> str:
        text = describe(self.forward, self.port)
        return f"{text}: {self.error}" if self.error else text


@dataclass
class Tunnels:
    """*forwards* opened over a paramiko ``Transport``: a listening socket
    here for each ``L`` and ``D`` one, a ``tcpip-forward`` on the server for
    each ``R``.  Each connection through one is pumped by a thread of its
    own; :meth:`stop` ends them all.  A forward that cannot be opened (the
    port taken, the server refusing) is said in :attr:`opened`, not raised:
    the connection is no less usable for it."""

    transport: Any
    forwards: list[Forward]
    #: How long opening a channel to the far end may take.
    timeout: float = 10.0
    opened: list[Opened] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._stopping = threading.Event()
        self._listeners: list[socket.socket] = []
        self._remote: dict[int, Forward] = {}
        self._open: set[Any] = set()
        self._lock = threading.Lock()

    # -- opening ---------------------------------------------------------------------------------

    def start(self) -> Tunnels:
        for forward in self.forwards:
            opened = Opened(forward)
            try:
                opened.port = self._remote_forward(forward) if forward.kind == "R" else self._listen(forward)
            except Exception as error:  # every refusal is said, none is fatal
                opened.error = _reason(error)
            self.opened.append(opened)
        return self

    def _listen(self, forward: Forward) -> int:
        address = forward.listen_address
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        if address == "":
            listener = socket.create_server(("", forward.port), family=socket.AF_INET6, dualstack_ipv6=True) \
                if socket.has_dualstack_ipv6() else socket.create_server(("", forward.port))
        else:
            listener = socket.create_server((address, forward.port), family=family)
        self._listeners.append(listener)
        threading.Thread(target=self._accept, args=(listener, forward), daemon=True,
                         name=f"nav-ssh-fwd-{forward.kind}{forward.port}").start()
        return listener.getsockname()[1]

    def _remote_forward(self, forward: Forward) -> int:
        port = self.transport.request_port_forward(forward.listen_address, forward.port, handler=self._arrived)
        with self._lock:
            self._remote[port] = forward
        return port

    # -- carrying ---------------------------------------------------------------------------------

    def _accept(self, listener: socket.socket, forward: Forward) -> None:
        with selectors.DefaultSelector() as selector:
            selector.register(listener, selectors.EVENT_READ)
            while not self._stopping.is_set():
                if not selector.select(POLL):
                    continue
                try:
                    sock, peer = listener.accept()
                except OSError:
                    if self._stopping.is_set():
                        return
                    continue
                threading.Thread(target=self._local, args=(sock, peer, forward), daemon=True,
                                 name=f"nav-ssh-fwd-{forward.kind}{forward.port}-conn").start()

    def _local(self, sock: socket.socket, peer: Any, forward: Forward) -> None:
        """An ``L`` or ``D`` connection: a ``direct-tcpip`` channel to where
        it goes -- a SOCKS client's asked first -- and the two pumped."""
        request = None
        try:
            if forward.kind == "D":
                sock.settimeout(HANDSHAKE_TIMEOUT)
                request = socks_request(sock)
                sock.settimeout(None)
                host, port = request.host, request.port
            else:
                host, port = forward.host, forward.host_port
            channel = self.transport.open_channel("direct-tcpip", (host, port), (peer[0], peer[1]),
                                                  timeout=self.timeout)
        except Exception:
            if request is not None:
                try:
                    sock.sendall(request.answer(False))
                except OSError:
                    pass
            _close(sock)
            return
        if request is not None:
            try:
                sock.sendall(request.answer(True))
            except OSError:
                _close(sock)
                _close(channel)
                return
        self._pump(sock, channel)

    def _arrived(self, channel: Any, origin: Any, server: Any) -> None:
        """paramiko's handler for every ``R`` connection (one for them all,
        told apart by the server's port); on its thread, so it hands off."""
        with self._lock:
            forward = self._remote.get(server[1])
        if forward is None or self._stopping.is_set():
            _close(channel)
            return
        threading.Thread(target=self._back, args=(channel, forward), daemon=True,
                         name=f"nav-ssh-fwd-R{forward.port}-conn").start()

    def _back(self, channel: Any, forward: Forward) -> None:
        try:
            sock = socket.create_connection((forward.host, forward.host_port), timeout=self.timeout)
            sock.settimeout(None)
        except OSError:
            _close(channel)
            return
        self._pump(sock, channel)

    def _pump(self, sock: socket.socket, channel: Any) -> None:
        """Bytes both ways between *sock* and *channel* until either ends."""
        with self._lock:
            if self._stopping.is_set():
                _close(sock)
                _close(channel)
                return
            self._open.update((sock, channel))
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(sock, selectors.EVENT_READ, channel)
                selector.register(channel, selectors.EVENT_READ, sock)
                while not self._stopping.is_set():
                    for key, _ in selector.select(POLL):
                        data = key.fileobj.recv(CHUNK)
                        if not data:
                            return
                        key.data.sendall(data)
        except Exception:
            return
        finally:
            with self._lock:
                self._open.difference_update((sock, channel))
            _close(sock)
            _close(channel)

    # -- ending ------------------------------------------------------------------------------------

    def stop(self) -> None:
        """Every listener closed, every ``tcpip-forward`` cancelled (while the
        connection still answers), every connection through them ended."""
        self._stopping.set()
        for listener in self._listeners:
            _close(listener)
        self._listeners = []
        with self._lock:
            remote, self._remote = self._remote, {}
            open_now, self._open = list(self._open), set()
        for port, forward in remote.items():
            try:
                if self.transport.is_active():
                    self.transport.cancel_port_forward(forward.listen_address, port)
            except Exception:
                pass
        for each in open_now:
            _close(each)

    def describe(self) -> list[tuple[str, str]]:
        """The information panel's lines: ``("Forward", "L 127.0.0.1:8080 → db:5432")``."""
        return [("Forward", opened.describe()) for opened in self.opened]


__all__ = ["Forward", "KINDS", "LOOPBACK", "Opened", "SocksRefused", "SocksRequest", "Tunnels", "describe",
           "parse", "parse_line", "render", "socks_request", "ssh_words"]
