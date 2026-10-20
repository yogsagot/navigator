"""The share listing's RPC (``navigator/lib/drives/dcerpc.py``): ``srvsvc``'s
``NetrShareEnum`` encoded and its answer decoded, against a pipe that
answers as a server does -- the bind accepted, the response in fragments,
strings deferred after the array, a remark left out."""

from __future__ import annotations

import struct

import pytest

from navigator.lib.drives import dcerpc


def _string(text: str) -> bytes:
    data = (text + "\0").encode("utf-16-le")
    out = struct.pack("<III", len(data) // 2, 0, len(data) // 2) + data
    return out + b"\0" * (-len(out) % 4)


def response_stub(shares: list[tuple[str, int, str | None]], status: int = 0) -> bytes:
    """What a server's ``NetrShareEnum`` answers at level 1."""
    stub = struct.pack("<III", 1, 1, 0x00020000)  # Level, discriminant, the container
    stub += struct.pack("<II", len(shares), 0x00020004)  # EntriesRead, the array
    stub += struct.pack("<I", len(shares))  # its conformance
    referent = 0x00020008
    for name, kind, remark in shares:
        stub += struct.pack("<III", referent, kind, 0 if remark is None else referent + 4)
        referent += 8
    for name, _, remark in shares:
        stub += _string(name)
        if remark is not None:
            stub += _string(remark)
    stub += struct.pack("<III", len(shares), 0x00020100, 0)  # TotalEntries, ResumeHandle
    return stub + struct.pack("<I", status)


def pdu(ptype: int, body: bytes, flags: int) -> bytes:
    return struct.pack("<BBBB4sHHI", 5, 0, ptype, flags, b"\x10\x00\x00\x00", 16 + len(body), 0, 2) + body


def bind_ack(result: int = 0) -> bytes:
    address = b"\\PIPE\\srvsvc\0"
    body = struct.pack("<HHI", 4280, 4280, 0x1234) + struct.pack("<H", len(address)) + address
    body += b"\0" * (-(16 + len(body)) % 4)
    body += struct.pack("<B3x", 1) + struct.pack("<HH", result, 0) + dcerpc.NDR.bytes_le + struct.pack("<I", 2)
    return pdu(dcerpc.BIND_ACK, body, 3)


def responses(stub: bytes, pieces: int) -> list[bytes]:
    """*stub* in *pieces* response fragments."""
    size = -(-len(stub) // pieces)
    parts = [stub[i:i + size] for i in range(0, len(stub), size)]
    out = []
    for number, part in enumerate(parts):
        flags = (dcerpc.FIRST_FRAG if number == 0 else 0) | (dcerpc.LAST_FRAG if number == len(parts) - 1 else 0)
        out.append(pdu(dcerpc.RESPONSE, struct.pack("<IHBx", len(stub), 0, 0) + part, flags))
    return out


class Pipe:
    """A ``srvsvc`` pipe: the bind answered, then the request; each read
    hands out at most *chunk* bytes, as a pipe may."""

    def __init__(self, answers: list[bytes], chunk: int = 4280) -> None:
        self.written: list[bytes] = []
        self._answers = answers
        self._pending = b""
        self.chunk = chunk

    def write(self, data: bytes) -> int:
        self.written.append(bytes(data))
        if len(self.written) == 1:
            self._pending += self._answers[0]
        else:
            self._pending += b"".join(self._answers[1:])
        return len(data)

    def read(self, size: int) -> bytes:
        size = min(size, self.chunk)
        data, self._pending = self._pending[:size], self._pending[size:]
        return data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


SHARES = [("public", 0, "Everyone's"), ("IPC$", dcerpc.STYPE_SPECIAL | 3, "IPC Service"),
          ("C$", dcerpc.STYPE_SPECIAL, "Default share"), ("printer", 1, None), ("media", 0, None)]


def test_the_shares_come_back_in_fragments_strings_deferred():
    pipe = Pipe([bind_ack(), *responses(response_stub(SHARES), 3)], chunk=40)
    shares = dcerpc.share_enum(pipe, "nas")
    assert [(share.name, share.remark) for share in shares] == [
        ("public", "Everyone's"), ("IPC$", "IPC Service"), ("C$", "Default share"), ("printer", ""), ("media", "")]
    assert [share.name for share in shares if share.is_disk and not share.is_special] == ["public", "media"]
    bind, call = pipe.written
    assert bind[2] == dcerpc.BIND and dcerpc.SRVSVC.bytes_le in bind
    assert call[2] == dcerpc.REQUEST and struct.unpack_from("<H", call, 22)[0] == dcerpc.NETR_SHARE_ENUM
    assert "\\\\nas".encode("utf-16-le") in call


def test_fragments_a_read_brings_together_are_each_had():
    pipe = Pipe([bind_ack(), *responses(response_stub(SHARES), 3)], chunk=1 << 16)
    assert len(dcerpc.share_enum(pipe, "nas")) == len(SHARES)


def test_the_request_s_stub_is_ndr_aligned():
    stub = dcerpc.share_enum_stub("ab")
    # Referent, then ``\\ab`` and its NUL: five characters, padded to four.
    assert stub[:16] == struct.pack("<IIII", 0x00020000, 5, 0, 5)
    assert len(stub) % 4 == 0
    assert stub[-12:] == struct.pack("<III", 0xFFFFFFFF, 0x00020008, 0)


def test_a_refused_bind_a_fault_and_a_werror_raise():
    with pytest.raises(dcerpc.RpcError, match="would not take"):
        dcerpc.share_enum(Pipe([bind_ack(result=2)]), "nas")
    fault = pdu(dcerpc.FAULT, struct.pack("<IHBxI", 0, 0, 0, 0x1C010002), 3)
    with pytest.raises(dcerpc.RpcError, match="faulted"):
        dcerpc.share_enum(Pipe([bind_ack(), fault]), "nas")
    with pytest.raises(dcerpc.RpcError, match="WERROR 0x5"):
        dcerpc.share_enum(Pipe([bind_ack(), *responses(response_stub([], status=5), 1)]), "nas")
