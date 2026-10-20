"""Just enough DCE/RPC to ask an SMB server for its shares: ``srvsvc``'s
``NetrShareEnum`` (MS-SRVS 3.1.4.8) at level 1, over the ``\\PIPE\\srvsvc``
named pipe of the server's ``IPC$``.

smbprotocol speaks SMB, not the RPC above it, and the alternatives
(impacket) are large; this is the one call a share listing needs.  It
speaks to any object with ``write(bytes)`` and ``read(size) -> bytes`` --
the pipe :func:`smbclient.open_file` opens -- and knows nothing of SMB, so
it is tested with bytes alone.  No RPC-level authentication: the SMB
session the pipe was opened on has proved who is asking already.

Connection-oriented RPC (C706 chapter 12): a *bind* to the interface, its
*bind_ack*, then a *request* and its *response*, possibly in several
fragments; the stub data in between is NDR (C706 chapter 14), little-endian.
"""

from __future__ import annotations

import struct
import uuid
from dataclasses import dataclass
from typing import Any

#: ``srvsvc``, version 3.0.
SRVSVC = uuid.UUID("4b324fc8-1670-01d3-1278-5a47bf6ee188")
#: The NDR transfer syntax, version 2.
NDR = uuid.UUID("8a885d04-1ceb-11c9-9fe8-08002b104860")

#: Packet types.
REQUEST, RESPONSE, FAULT, BIND, BIND_ACK, BIND_NAK = 0, 2, 3, 11, 12, 13
#: ``pfc_flags``.
FIRST_FRAG, LAST_FRAG = 0x01, 0x02
#: ``NetrShareEnum``'s operation number.
NETR_SHARE_ENUM = 15
#: The largest fragment either side sends.
MAX_FRAG = 4280

#: ``shi1_type``: the kind in the low bits, then the flags.
STYPE_DISKTREE = 0
STYPE_MASK = 0x0FFFFFFF
STYPE_SPECIAL = 0x80000000
STYPE_TEMPORARY = 0x40000000


class RpcError(Exception):
    """The server refused, faulted, or answered what is not RPC."""


@dataclass(frozen=True)
class Share:
    """One ``SHARE_INFO_1``."""

    name: str
    type: int
    remark: str

    @property
    def is_disk(self) -> bool:
        """A share of files -- not a printer, a device or ``IPC$``."""
        return self.type & STYPE_MASK == STYPE_DISKTREE

    @property
    def is_special(self) -> bool:
        """An administrative share: ``C$``, ``ADMIN$``."""
        return bool(self.type & STYPE_SPECIAL)


# -- packets -----------------------------------------------------------------------------------


def _header(ptype: int, body: bytes, call_id: int) -> bytes:
    """The common header, 16 bytes: version 5.0, one fragment, little-endian ASCII IEEE."""
    return struct.pack("<BBBB4sHHI", 5, 0, ptype, FIRST_FRAG | LAST_FRAG, b"\x10\x00\x00\x00",
                       16 + len(body), 0, call_id) + body


def bind(call_id: int = 1) -> bytes:
    """A *bind* to ``srvsvc`` v3.0 over NDR."""
    body = struct.pack("<HHI", MAX_FRAG, MAX_FRAG, 0)
    body += struct.pack("<B3x", 1)  # one presentation context
    body += struct.pack("<HBx", 0, 1)  # context 0, one transfer syntax
    body += SRVSVC.bytes_le + struct.pack("<HH", 3, 0)
    body += NDR.bytes_le + struct.pack("<I", 2)
    return _header(BIND, body, call_id)


def request(opnum: int, stub: bytes, call_id: int = 2) -> bytes:
    """A *request* for *opnum* on context 0 -- in one fragment, being small."""
    return _header(REQUEST, struct.pack("<IHH", len(stub), 0, opnum) + stub, call_id)


def check_bind_ack(pdu: bytes) -> None:
    """A *bind_ack* whose first result accepts; :class:`RpcError` otherwise."""
    ptype = _type(pdu)
    if ptype == BIND_NAK:
        raise RpcError("the server refused the bind")
    if ptype != BIND_ACK or len(pdu) < 28:
        raise RpcError(f"not a bind_ack (type {ptype})")
    # max_xmit, max_recv, assoc_group, then the secondary address as a
    # length-prefixed string, aligned to four from the packet's start.
    (address_length,) = struct.unpack_from("<H", pdu, 24)
    offset = 26 + address_length
    offset += -offset % 4
    if len(pdu) < offset + 8:
        raise RpcError("a short bind_ack")
    (results,) = struct.unpack_from("<B", pdu, offset)
    (result, reason) = struct.unpack_from("<HH", pdu, offset + 4)
    if results < 1 or result != 0:
        raise RpcError(f"the server would not take srvsvc (result {result}, reason {reason})")


def _type(pdu: bytes) -> int:
    if len(pdu) < 16 or pdu[0] != 5:
        raise RpcError("not an RPC packet")
    return pdu[2]


# -- NDR ---------------------------------------------------------------------------------------


def _string(text: str) -> bytes:
    """A conformant varying ``wchar_t`` string, NUL-ended, padded to four."""
    data = (text + "\0").encode("utf-16-le")
    count = len(data) // 2
    out = struct.pack("<III", count, 0, count) + data
    return out + b"\0" * (-len(out) % 4)


def share_enum_stub(server: str) -> bytes:
    """``NetrShareEnum``'s ``[in]`` parameters: *server*, level 1, an empty
    container to fill, no limit, and a resume handle of 0."""
    stub = struct.pack("<I", 0x00020000) + _string(f"\\\\{server}")  # ServerName, unique
    stub += struct.pack("<II", 1, 1)  # InfoStruct: Level, then the union's discriminant
    stub += struct.pack("<I", 0x00020004)  # Level1: unique pointer to the container ...
    stub += struct.pack("<II", 0, 0)  # ... EntriesRead 0, Buffer null
    stub += struct.pack("<I", 0xFFFFFFFF)  # PreferedMaximumLength: all of them
    stub += struct.pack("<II", 0x00020008, 0)  # ResumeHandle, unique, 0
    return stub


class _Reader:
    """NDR read off the stub, every scalar aligned to its size."""

    def __init__(self, data: bytes) -> None:
        self.data, self.offset = data, 0

    def u32(self) -> int:
        self.offset += -self.offset % 4
        if self.offset + 4 > len(self.data):
            raise RpcError("a short response")
        (value,) = struct.unpack_from("<I", self.data, self.offset)
        self.offset += 4
        return value

    def string(self) -> str:
        _maximum, _first, actual = self.u32(), self.u32(), self.u32()
        end = self.offset + 2 * actual
        if end > len(self.data):
            raise RpcError("a short string")
        text = self.data[self.offset:end].decode("utf-16-le", "replace")
        self.offset = end
        return text.rstrip("\0")


def parse_share_enum(stub: bytes) -> list[Share]:
    """``NetrShareEnum``'s ``[out]`` parameters at level 1, as :class:`Share`
    s; :class:`RpcError` for a ``WERROR`` that is not success."""
    reader = _Reader(stub)
    reader.u32()  # Level
    reader.u32()  # the union's discriminant
    shares: list[Share] = []
    if reader.u32():  # the container's pointer
        count = reader.u32()
        if reader.u32():  # the array's pointer
            if reader.u32() != count:  # its conformance
                raise RpcError("the share count does not match")
            fixed = [(reader.u32(), reader.u32(), reader.u32()) for _ in range(count)]
            for name_pointer, kind, remark_pointer in fixed:
                # Deferred: each entry's strings after the array, in order.
                name = reader.string() if name_pointer else ""
                remark = reader.string() if remark_pointer else ""
                shares.append(Share(name, kind, remark))
    reader.u32()  # TotalEntries
    if reader.u32():  # ResumeHandle's pointer
        reader.u32()
    status = reader.u32()
    if status != 0:
        raise RpcError(f"NetrShareEnum failed: WERROR {status:#x}")
    return shares


# -- over a pipe -------------------------------------------------------------------------------


class _Fragments:
    """*pipe*'s bytes cut into fragments, however its reads split or join
    them: what one read brought beyond a fragment kept for the next."""

    def __init__(self, pipe: Any) -> None:
        self.pipe, self._kept = pipe, b""

    def _fill(self, count: int) -> None:
        while len(self._kept) < count:
            chunk = self.pipe.read(MAX_FRAG)
            if not chunk:
                raise RpcError("the pipe closed")
            self._kept += chunk

    def next(self) -> bytes:
        self._fill(10)
        (length,) = struct.unpack_from("<H", self._kept, 8)
        if length < 16:
            raise RpcError("not an RPC packet")
        self._fill(length)
        pdu, self._kept = self._kept[:length], self._kept[length:]
        return pdu


def _call(pipe: Any, fragments: _Fragments, packet: bytes) -> bytes:
    """*packet* sent, and the stub data of the response it gets, its
    fragments joined."""
    pipe.write(packet)
    stub = b""
    while True:
        pdu = fragments.next()
        ptype = _type(pdu)
        if ptype == FAULT:
            (status,) = struct.unpack_from("<I", pdu, 24) if len(pdu) >= 28 else (0,)
            raise RpcError(f"the server faulted: {status:#x}")
        if ptype != RESPONSE:
            raise RpcError(f"not a response (type {ptype})")
        (auth_length,) = struct.unpack_from("<H", pdu, 10)
        stub += pdu[24:len(pdu) - auth_length]
        if pdu[3] & LAST_FRAG:
            return stub


def share_enum(pipe: Any, server: str) -> list[Share]:
    """Every share *server* lists, asked over its ``srvsvc`` pipe."""
    fragments = _Fragments(pipe)
    pipe.write(bind())
    check_bind_ack(fragments.next())
    return parse_share_enum(_call(pipe, fragments, request(NETR_SHARE_ENUM, share_enum_stub(server))))


__all__ = ["RpcError", "Share", "parse_share_enum", "share_enum", "share_enum_stub"]
