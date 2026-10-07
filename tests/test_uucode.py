"""File > UU Encode (Ctrl+F7) and UU Decode (Ctrl+F8): DOS Navigator's
``UuEncode`` and ``UU_Decode``."""

from __future__ import annotations

import binascii
import os
import random
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import uucode
from navigator.__main__ import Navigator
from navigator.job import Job, Stopped
from navigator.settings import SETTINGS
from navigator.uucode import (
    CHECKSUMS, DecodeError, EncodeRequest, FileExists, decode, encode, encode_line, plan, sum_r,
    target_names,
)
from navigator.widgets.file_ops.exists_query import ExistsQuery
from navigator.widgets.file_ops.uu_decode_dialog import UUDecodeDialog
from navigator.widgets.file_ops.uu_encode_dialog import UUEncodeDialog

DATA = bytes(random.Random(7).randrange(256) for _ in range(20000))


def asker(answers: list, answer="yes"):
    def ask(question):
        answers.append(question)
        return answer
    return Job(asker=ask)


@pytest.fixture
def blob(tmp_path) -> Path:
    path = tmp_path / "blob.bin"
    path.write_bytes(DATA)
    return path


# -- the arithmetic ------------------------------------------------------------------


def test_lines_map_through_dns_table_with_a_backquote_for_nothing():
    assert encode_line(b"Cat") == binascii.b2a_uu(b"Cat", backtick=True).decode().rstrip("\n")
    assert encode_line(b"\0\0\0")[1:] == "````"
    # The check character is the six-bit sum of the encoded characters.
    line = encode_line(b"Cat", check=True)
    assert line[:-1] == encode_line(b"Cat") and line[-1] == uucode.UUXLT[sum(
        (ord(c) - 32) & 63 for c in line[1:-1]) & 63]


def test_sum_r_is_bsds():
    total = 0
    for byte in b"hello":
        total = ((total >> 1) | ((total & 1) << 15)) + byte & 0xFFFF
    assert sum_r(b"hello") == total


def test_sections_are_evened_out_and_the_last_is_not_short():
    cut = plan(20000, 100)
    assert cut.sections == 5 and cut.section_size % 45 == 0
    assert cut.section_size * 4 + cut.last_size == 20000 and cut.last_size >= cut.section_size // 2
    assert plan(1000, 100).sections == 1
    assert plan(10, 3).lines == 0 and plan(10, 3).sections == 1  # ten lines at the least


def test_each_section_has_a_file_of_its_own(tmp_path):
    source = tmp_path / "a.bin"
    assert target_names(source, "out.uue", 1, tmp_path) == [tmp_path / "out.uue"]
    names = target_names(source, "out.uue", 12, tmp_path)
    assert [n.name for n in names[:2]] == ["out.uu1", "out.uu2"] and names[9].name == "out.u10"
    assert target_names(source, "dir/", 1, tmp_path) == [tmp_path / "dir" / "a.uue"]
    assert target_names(source, "plain", 1, tmp_path) == [tmp_path / "plain.uue"]


# -- encoding ------------------------------------------------------------------------


def test_the_first_section_carries_the_prefixes_and_the_last_the_end(blob, tmp_path):
    request = EncodeRequest(blob, "out.uue", map_table=True, checksum="line", lines=100)
    written = encode(request, Job(), tmp_path)
    assert [p.name for p in written] == ["out.uu1", "out.uu2", "out.uu3", "out.uu4", "out.uu5"]
    first = written[0].read_text().splitlines()
    assert any(line.strip().startswith("source file name : blob.bin") for line in first)
    header = first.index("section 1 of 5 of file blob.bin  < uuencode by Navigator >")
    assert first[header + 1] == "" and first[header + 2].startswith("filetime ")
    assert first[header + 3:header + 6] == ["table", uucode.UUXLT[:32], uucode.UUXLT[32:]]
    assert first[header + 6] == "begin 644 blob.bin"
    assert len(first[header + 7]) == 62  # length, sixty characters, check character
    assert first[-2].startswith("sum -r/size ") and first[-2].endswith(
        'section (from "begin" to last encoded line)')
    last = written[-1].read_text().splitlines()
    assert last[0].startswith("section 5 of 5") and "``" in last and "end" in last
    assert any(line.endswith("entire input file") and line.startswith(f"sum -r/size {sum_r(DATA)}/20000")
               for line in last)


def test_dos_line_ends_and_none_of_the_prefixes(blob, tmp_path):
    request = EncodeRequest(blob, "out.uue", file_time=False, statistics=False, checksum="none",
                            lines=1000, crlf=True)
    (written,) = encode(request, Job(), tmp_path)
    raw = written.read_bytes()
    assert raw.count(b"\r\n") == raw.count(b"\n")
    text = raw.decode().splitlines()
    assert text[0].startswith("section 1 of file blob.bin") and text[2] == "begin 644 blob.bin"
    assert not any(line.startswith("sum -r") for line in text)


def test_a_file_too_small_is_refused(tmp_path):
    (tmp_path / "x").write_bytes(b"ab")
    with pytest.raises(ValueError, match="too small"):
        encode(EncodeRequest(tmp_path / "x", "x.uue"), Job(), tmp_path)


def test_a_file_there_already_is_asked_about(blob, tmp_path):
    (tmp_path / "out.uue").write_text("old")
    asked: list = []
    with pytest.raises(Stopped):
        encode(EncodeRequest(blob, "out.uue", lines=1000), asker(asked, "no"), tmp_path)
    assert asked == [FileExists(tmp_path / "out.uue")] and (tmp_path / "out.uue").read_text() == "old"


# -- decoding ------------------------------------------------------------------------


@pytest.mark.parametrize("checksum", CHECKSUMS)
def test_every_level_decodes_back_whatever_order_the_sections_come_in(blob, tmp_path, checksum):
    written = encode(EncodeRequest(blob, "out.uue", map_table=True, checksum=checksum, lines=100),
                     Job(), tmp_path)
    mail = tmp_path / "mail.txt"
    mail.write_text("From: someone\n\n" + "".join(p.read_text() for p in reversed(written)) + "-- \nsig\n")
    errors: list = []
    result = decode(mail, tmp_path / "out", asker(errors))
    assert (tmp_path / "out" / "blob.bin").read_bytes() == DATA
    assert result.decoded == 1 and result.errors == 0 and errors == []
    stamp = os.stat(tmp_path / "out" / "blob.bin").st_mtime
    assert abs(stamp - os.stat(blob).st_mtime) <= 2


@pytest.mark.parametrize("backtick", [True, False])
def test_a_classic_uuencode_decodes(tmp_path, backtick):
    lines = ["begin 600 classic.bin"] + [binascii.b2a_uu(DATA[i:i + 45], backtick=backtick).decode().rstrip("\n")
                                        for i in range(0, len(DATA), 45)]
    (tmp_path / "c.uue").write_text("\n".join(lines + ["`" if backtick else " ", "end", ""]))
    result = decode(tmp_path / "c.uue", tmp_path, Job())
    assert (tmp_path / "classic.bin").read_bytes() == DATA and result.decoded == 1


def test_a_missing_section_breaks_the_file_and_save_broken_keeps_it(blob, tmp_path):
    written = encode(EncodeRequest(blob, "out.uue", lines=100), Job(), tmp_path)
    mail = tmp_path / "mail.txt"
    mail.write_text("".join(p.read_text() for i, p in enumerate(written) if i != 2))
    errors: list = []
    result = decode(mail, tmp_path / "out", asker(errors))
    assert not (tmp_path / "out" / "blob.bin").exists() and result.decoded == 0
    texts = [e.text for e in errors]
    assert "Section 3 of file blob.bin (5) is absent" in texts and "Failed to decode blob.bin" in texts

    result = decode(mail, tmp_path / "kept", Job(), display_errors=False, save_broken=True)
    assert (tmp_path / "kept" / "blob.bin").exists() and result.errors >= 1 and result.decoded == 0


def test_a_damaged_line_is_a_section_crc_error(blob, tmp_path):
    (written,) = encode(EncodeRequest(blob, "out.uue", lines=1000), Job(), tmp_path)
    lines = written.read_text().splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("M"))
    lines[index] = "M" + ("!" if lines[index][1] != "!" else '"') + lines[index][2:]
    written.write_text("\n".join(lines) + "\n")
    errors: list = []
    decode(written, tmp_path / "out", asker(errors))
    assert errors[0] == DecodeError("CRC error - blob.bin, Section 1")


def test_a_file_there_already_can_be_kept(blob, tmp_path):
    (written,) = encode(EncodeRequest(blob, "out.uue", lines=1000), Job(), tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "blob.bin").write_text("mine")
    asked: list = []
    decode(written, tmp_path / "out", asker(asked, "no"))
    assert asked == [FileExists(tmp_path / "out" / "blob.bin")]
    assert (tmp_path / "out" / "blob.bin").read_text() == "mine"


def test_nothing_encoded_says_so(tmp_path):
    (tmp_path / "plain.txt").write_text("just\ntext\n")
    errors: list = []
    result = decode(tmp_path / "plain.txt", tmp_path, asker(errors))
    assert not result.found and errors == [DecodeError(uucode.NO_STUFF)]


# -- the dialogs ----------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    (tmp_path / "a" / "blob.bin").write_bytes(DATA)
    return tmp_path


def on(name: str):
    def action(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def test_ctrl_f7_encodes_into_the_other_panel_and_keeps_the_choices(place):
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}

    def choose(a):
        dialog = a.modal
        seen["target"] = dialog.target.value
        dialog.checksum.value = 3  # of Each line
        dialog.lines.value = "1000"

    run_app(app, [on("blob.bin"), KeyEvent("f7", ctrl=True), Until(lambda a: isinstance(a.modal, UUEncodeDialog)),
                  choose, KeyEvent("enter"), Until(lambda a: (place / "b" / "blob.uue").exists() and a.modal is None)])
    assert seen["target"] == str(place / "b" / "blob.uue")
    assert SETTINGS.uucode.checksum == "line" and SETTINGS.uucode.lines_per_section == 1000
    assert "checksum = line" in SETTINGS.path.read_text()


def test_ctrl_f8_decodes_into_the_other_panel(place):
    encode(EncodeRequest(place / "a" / "blob.bin", "blob.uue", lines=1000), Job(), place / "a")
    (place / "a" / "blob.bin").unlink()
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}
    run_app(app, [on("blob.uue"), KeyEvent("f8", ctrl=True), Until(lambda a: isinstance(a.modal, UUDecodeDialog)),
                  lambda a: seen.update(target=a.modal.target.value), KeyEvent("enter"),
                  Until(lambda a: (place / "b" / "blob.bin").exists() and a.modal is None)])
    assert seen["target"] == f"{place / 'b'}/"
    assert (place / "b" / "blob.bin").read_bytes() == DATA


def test_no_to_a_file_there_already_writes_nothing(place):
    SETTINGS.uucode.lines_per_section = 1000  # one section: blob.uue
    encode(EncodeRequest(place / "a" / "blob.bin", "blob.uue", lines=1000), Job(), place / "a")
    before = (place / "a" / "blob.uue").read_bytes()
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    run_app(app, [on("blob.bin"), KeyEvent("f7", ctrl=True), Until(lambda a: isinstance(a.modal, UUEncodeDialog)),
                  lambda a: setattr(a.modal.target, "value", "blob.uue"), KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, ExistsQuery)), KeyEvent("n", alt=True),
                  Until(lambda a: a.modal is None)])
    assert (place / "a" / "blob.uue").read_bytes() == before
