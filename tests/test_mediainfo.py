"""Ctrl+L's *Current file* for media files and PDFs (navigator/lib/system/mediainfo.py)."""

from __future__ import annotations

import struct
import subprocess

import pytest

from navigator.lib.system import mediainfo
from navigator.lib.system.mediainfo import Media, from_image, from_probe, kind, pairs, read

MP3 = {
    "streams": [
        {"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2,
         "channel_layout": "stereo"},
        {"codec_type": "video", "codec_name": "mjpeg", "width": 500, "height": 500,
         "disposition": {"attached_pic": 1}},
    ],
    "format": {"format_name": "mp3", "duration": "245.6", "bit_rate": "320000",
               "tags": {"TITLE": "Song ~one~", "artist": "Band", "album": "Record", "date": "1999-04-01",
                        "track": "3/12", "genre": "Rock", "comment": "not shown"}},
}

MKV = {
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080,
         "avg_frame_rate": "30000/1001"},
        {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 6,
         "channel_layout": "5.1(side)"},
    ],
    "format": {"format_long_name": "Matroska / WebM", "duration": "3725", "bit_rate": "4000000"},
}


def test_kinds():
    assert [kind(m) for m in ("audio/mpeg", "video/mp4", "image/png", "application/pdf", "text/plain", "")] == \
        ["audio", "video", "image", "pdf", None, None]


def test_ffprobes_reading_of_a_song_skips_its_cover():
    assert pairs(from_probe(MP3)) == [
        ("Duration", "4:06"), ("Audio", "mp3, 44.1 kHz, stereo"), ("Bitrate", "320 kbit/s"),
        ("Title", "Song one"), ("Artist", "Band"), ("Album", "Record"), ("Year", "1999"), ("Track", "3/12"),
        ("Genre", "Rock"),
    ]


def test_ffprobes_reading_of_a_film():
    assert pairs(from_probe(MKV)) == [
        ("Container", "Matroska / WebM"), ("Duration", "1:02:05"), ("Video", "h264 1920 × 1080, 29.97 fps"),
        ("Audio", "aac, 48 kHz, 5.1(side)"), ("Bitrate", "4,000 kbit/s"),
    ]


def test_a_streams_tags_stand_in_for_the_containers():
    data = {"streams": [{"codec_type": "audio", "codec_name": "opus", "channels": 1,
                         "tags": {"TITLE": "Voice"}}], "format": {}}
    assert pairs(from_probe(data)) == [("Audio", "opus, mono"), ("Title", "Voice")]


def tiff(order: str) -> bytes:
    """A TIFF block with IFD0's Make and Model and an Exif IFD's DateTimeOriginal."""
    make, model, date = b"Canon\0", b"Canon EOS 80D\0", b"2024:05:01 12:34:56\0"
    head = (b"II" if order == "<" else b"MM") + struct.pack(order + "HI", 42, 8)
    ifd0 = struct.pack(order + "H", 3)
    ifd0 += struct.pack(order + "HHII", 0x010F, 2, len(make), 68)
    ifd0 += struct.pack(order + "HHII", 0x0110, 2, len(model), 74)
    ifd0 += struct.pack(order + "HHII", 0x8769, 4, 1, 50) + struct.pack(order + "I", 0)
    exif = struct.pack(order + "H", 1) + struct.pack(order + "HHII", 0x9003, 2, len(date), 88)
    exif += struct.pack(order + "I", 0)
    return head + ifd0 + exif + make + model + date


def jpeg(order: str = "<") -> bytes:
    app1 = b"Exif\0\0" + tiff(order)
    sof = bytes([8]) + struct.pack(">HH", 3000, 4000) + bytes([3]) + bytes(9)
    return (b"\xff\xd8" + b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1
            + b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xda\0\x02")


@pytest.mark.parametrize("order", ["<", ">"])
def test_a_jpegs_size_camera_and_date_taken(order, monkeypatch):
    media = from_image(jpeg(order))
    assert (media.width, media.height, media.camera) == (4000, 3000, "Canon EOS 80D")
    monkeypatch.setattr("time.mktime", lambda when: 1.0)
    assert from_image(jpeg(order)).taken == 1.0
    assert pairs(Media(width=4000, height=3000, camera="Canon EOS 80D", taken=1.0)) == [
        ("Dimensions", "4000 × 3000"), ("Camera", "Canon EOS 80D"), ("Taken", 1.0)]


def test_other_image_headers():
    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 640, 480)
    assert (from_image(png).width, from_image(png).height) == (640, 480)
    gif = b"GIF89a" + struct.pack("<HH", 32, 16)
    assert (from_image(gif).width, from_image(gif).height) == (32, 16)
    bmp = b"BM" + bytes(16) + struct.pack("<ii", 10, -20)
    assert (from_image(bmp).width, from_image(bmp).height) == (10, 20)
    webp = b"RIFF" + bytes(4) + b"WEBPVP8X" + bytes(8) + (99).to_bytes(3, "little") + (49).to_bytes(3, "little")
    assert (from_image(webp).width, from_image(webp).height) == (100, 50)
    assert from_image(b"\xff\xd8\xff\xe1") is None and from_image(png[:20]) is None
    assert from_image(b"nothing at all") is None


def test_an_image_not_read_here_is_ffprobes_size(tmp_path, monkeypatch):
    (tmp_path / "a.tiff").write_bytes(b"II*\0")
    monkeypatch.setattr(mediainfo, "probe", lambda path: Media(video=("tiff", 7, 9, None)))
    assert pairs(read(tmp_path / "a.tiff", "image/tiff")) == [("Dimensions", "7 × 9")]


def test_a_pdfs_pages_and_information(tmp_path):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    writer.add_blank_page(100, 100)
    writer.add_metadata({"/Title": "Report", "/Author": "Someone"})
    with open(tmp_path / "a.pdf", "wb") as file:
        writer.write(file)
    assert pairs(read(tmp_path / "a.pdf", "application/pdf")) == [
        ("Pages", "2"), ("Title", "Report"), ("Author", "Someone"), ("Producer", "pypdf")]
    (tmp_path / "bad.pdf").write_bytes(b"not a pdf")
    assert read(tmp_path / "bad.pdf", "application/pdf") is None


def test_without_ffprobe_or_once_not_wanted_nothing_runs(tmp_path, monkeypatch):
    (tmp_path / "a.mp3").write_bytes(b"x")

    def refused(*args, **kwargs):
        raise AssertionError("ffprobe ran")

    monkeypatch.setattr(subprocess, "run", refused)
    assert read(tmp_path / "a.mp3", "audio/mpeg", lambda: False) is None
    monkeypatch.setattr(mediainfo.shutil, "which", lambda name: None)
    assert read(tmp_path / "a.mp3", "audio/mpeg") is None


def test_ffprobe_is_asked_for_json(tmp_path, monkeypatch):
    import json

    seen = {}

    def run(command, **kwargs):
        seen["command"] = command
        return subprocess.CompletedProcess(command, 0, json.dumps(MKV).encode(), b"")

    monkeypatch.setattr(mediainfo.shutil, "which", lambda name: "/usr/bin/ffprobe")
    monkeypatch.setattr(subprocess, "run", run)
    assert read(tmp_path / "a.mkv", "video/x-matroska").video == ("h264", 1920, 1080, 30000 / 1001)
    assert seen["command"][0] == "/usr/bin/ffprobe" and "json" in seen["command"]
