"""What Ctrl+L's *Current file* says of a media file or a PDF: a departure,
DOS Navigator's ``TDiskInfo`` described the directory alone.

:func:`read` runs on the information panel's thread and returns a
:class:`Media` of plain fields; :func:`pairs` lays it out as ``(label,
value)`` on the loop, where :func:`~navkit.i18n.tr` may be read.

- **Audio and video** are ``ffprobe``'s (FFmpeg's), run as ``gio`` is run
  (:func:`program` looks it up at the call): the duration, the streams, the
  bitrate and the tags.  Without it they get nothing more.
- **Images** are read here, from the head of the file: PNG, GIF, BMP, WebP
  and JPEG dimensions, and a JPEG's EXIF camera and date taken, which
  ``ffprobe`` does not give.  Any other image is ``ffprobe``'s size.
- **PDFs** are pypdf's: the pages and the document's title, author, subject
  and producer.

Nothing is run for a file the cursor has already left: *wanted* is asked
first, the panel's reader having one thread a held-down key would queue
behind.
"""

from __future__ import annotations

import json
import logging
import shutil
import struct
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from navkit.i18n import tr, tr_n

#: How long ``ffprobe`` may take over one file.
TIMEOUT = 5.0

#: How much of an image is read for its header and EXIF.
HEAD = 128 * 1024

#: How long a tag's value may be.
LONGEST = 200

#: The tags shown, as ``ffprobe`` names them (any case), in order.
TAGS = ("title", "artist", "album", "date", "track", "genre")

#: Every label :func:`pairs` gives, in English: what the information panel
#: translates, listed for the catalogues (``navigator/locales/__init__.py``).
LABELS = ("Duration", "Container", "Video", "Audio", "Bitrate", "Title", "Artist", "Album", "Year", "Track",
          "Genre", "Date", "Dimensions", "Camera", "Taken", "Pages", "Author", "Subject", "Producer", "Encrypted")


@dataclass
class Media:
    """What a read of a media file or PDF found: plain fields, for the loop
    to lay out (:func:`pairs`)."""

    duration: float | None = None
    container: str = ""
    #: ``(codec, width, height, frames per second or None)``.
    video: tuple[str, int, int, float | None] | None = None
    #: ``(codec, sample rate, channel layout, channels)``.
    audio: tuple[str, int, str, int] | None = None
    bitrate: int | None = None
    tags: dict[str, str] = field(default_factory=dict)
    width: int | None = None
    height: int | None = None
    camera: str = ""
    taken: float | None = None
    pages: int | None = None
    encrypted: bool = False


def kind(mime: str) -> str | None:
    """``audio``, ``video``, ``image`` or ``pdf`` for a MIME type; None for
    anything else."""
    if mime == "application/pdf":
        return "pdf"
    major = mime.partition("/")[0]
    return major if major in ("audio", "video", "image") else None


def program(which: Callable[[str], str | None] | None = None) -> str | None:
    """The ``ffprobe`` to run, or None: not installed."""
    return (which or shutil.which)("ffprobe")


def read(path: Path, mime: str, wanted: Callable[[], bool] = lambda: True) -> Media | None:
    """*path*'s :class:`Media`, or None: not a kind described, not readable,
    or no longer *wanted*.  Runs on a thread."""
    what = kind(mime)
    if what is None or not wanted():
        return None
    try:
        if what == "pdf":
            return from_pdf(path)
        if what == "image":
            with open(path, "rb") as file:
                media = from_image(file.read(HEAD))
            if media is not None:
                return media
            probed = probe(path)
            if probed is None or probed.video is None:
                return None
            return Media(width=probed.video[1], height=probed.video[2])
        return probe(path)
    except Exception:  # a damaged file is described as far as the listing goes
        return None


# -- ffprobe -----------------------------------------------------------------------


def probe(path: Path) -> Media | None:
    """``ffprobe``'s reading of *path*, or None without it or when it fails."""
    ffprobe = program()
    if ffprobe is None:
        return None
    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            capture_output=True, stdin=subprocess.DEVNULL, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return from_probe(json.loads(result.stdout.decode("utf-8", "replace")))
    except ValueError:
        return None


def _number(value: Any, kind: type = float) -> Any:
    try:
        return kind(value)
    except (TypeError, ValueError):
        return None


def _rate(text: Any) -> float | None:
    """``30000/1001`` as frames per second; None for ``0/0`` or nothing."""
    top, _, bottom = str(text or "").partition("/")
    top, bottom = _number(top), _number(bottom or 1)
    return top / bottom if top and bottom else None


def _clean(value: Any) -> str:
    """A tag's value as a line can show it: one line, no ``~``, not too long."""
    text = " ".join(str(value).replace("~", "").split())
    return text[:LONGEST]


def from_probe(data: dict[str, Any]) -> Media:
    """``ffprobe -print_format json -show_format -show_streams``'s output as
    a :class:`Media`.  Cover art (``attached_pic``) is not a video stream."""
    fmt = data.get("format") or {}
    streams = [stream for stream in data.get("streams") or ()
               if not (stream.get("disposition") or {}).get("attached_pic")]
    media = Media(duration=_number(fmt.get("duration")), bitrate=_number(fmt.get("bit_rate"), int),
                  container=_clean(fmt.get("format_long_name") or fmt.get("format_name") or ""))
    for stream in streams:
        codec = str(stream.get("codec_name") or "")
        if stream.get("codec_type") == "video" and media.video is None:
            media.video = (codec, _number(stream.get("width"), int) or 0, _number(stream.get("height"), int) or 0,
                           _rate(stream.get("avg_frame_rate")) or _rate(stream.get("r_frame_rate")))
        elif stream.get("codec_type") == "audio" and media.audio is None:
            media.audio = (codec, _number(stream.get("sample_rate"), int) or 0,
                           str(stream.get("channel_layout") or ""), _number(stream.get("channels"), int) or 0)
    # Tags are the container's, else (Ogg, Opus) the first stream's.
    for tags in [fmt.get("tags")] + [stream.get("tags") for stream in streams]:
        found = {str(name).lower(): value for name, value in (tags or {}).items()}
        if any(name in found for name in TAGS):
            media.tags = {name: _clean(found[name]) for name in TAGS if str(found.get(name, "")).strip()}
            break
    return media


# -- images ------------------------------------------------------------------------

#: The JPEG markers that start a frame and give its size.
_SOF = frozenset({0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF})


def from_image(head: bytes) -> Media | None:
    """The size, and a JPEG's camera and date taken, from the first bytes of
    an image; None for a format not read here or a header cut short."""
    try:
        if head.startswith(b"\x89PNG\r\n\x1a\n") and head[12:16] == b"IHDR":
            width, height = struct.unpack(">II", head[16:24])
            return Media(width=width, height=height)
        if head[:6] in (b"GIF87a", b"GIF89a"):
            width, height = struct.unpack("<HH", head[6:10])
            return Media(width=width, height=height)
        if head.startswith(b"BM") and len(head) >= 26:
            width, height = struct.unpack("<ii", head[18:26])
            return Media(width=width, height=abs(height))
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return _webp(head)
        if head.startswith(b"\xff\xd8"):
            return _jpeg(head)
    except struct.error:
        pass
    return None


def _webp(head: bytes) -> Media | None:
    chunk = head[12:16]
    if chunk == b"VP8 " and head[23:26] == b"\x9d\x01\x2a":
        width, height = struct.unpack("<HH", head[26:30])
        return Media(width=width & 0x3FFF, height=height & 0x3FFF)
    if chunk == b"VP8L" and head[20] == 0x2F:
        bits = int.from_bytes(head[21:25], "little")
        return Media(width=(bits & 0x3FFF) + 1, height=((bits >> 14) & 0x3FFF) + 1)
    if chunk == b"VP8X":
        return Media(width=int.from_bytes(head[24:27], "little") + 1,
                     height=int.from_bytes(head[27:30], "little") + 1)
    return None


def _jpeg(head: bytes) -> Media | None:
    """A JPEG's segments up to its frame: EXIF from APP1, the size from SOFn."""
    media = Media()
    at = 2
    while at + 4 <= len(head):
        if head[at] != 0xFF:
            return None
        marker = head[at + 1]
        if marker == 0xFF:  # fill byte
            at += 1
            continue
        length = struct.unpack(">H", head[at + 2:at + 4])[0]
        body = head[at + 4:at + 2 + length]
        if marker == 0xE1 and body.startswith(b"Exif\0\0"):
            _exif(body[6:], media)
        elif marker in _SOF:
            media.height, media.width = struct.unpack(">HH", body[1:5])
            return media
        elif marker == 0xDA:  # the scan starts: no frame header before it
            return None
        at += 2 + length
    return None


def _exif(tiff: bytes, media: Media) -> None:
    """IFD0's *Make* and *Model*, and the Exif IFD's *DateTimeOriginal*."""
    order = {b"II": "<", b"MM": ">"}.get(tiff[:2])
    if order is None:
        return

    def entries(offset: int) -> dict[int, tuple[int, int, bytes]]:
        count = struct.unpack(order + "H", tiff[offset:offset + 2])[0]
        found = {}
        for index in range(count):
            at = offset + 2 + 12 * index
            tag, kind, n = struct.unpack(order + "HHI", tiff[at:at + 8])
            found[tag] = (kind, n, tiff[at + 8:at + 12])
        return found

    def text(entry: tuple[int, int, bytes] | None) -> str:
        if entry is None or entry[0] != 2:  # ASCII
            return ""
        _, n, value = entry
        data = value[:n] if n <= 4 else tiff[struct.unpack(order + "I", value)[0]:][:n]
        return data.split(b"\0")[0].decode("latin-1").strip()

    first = entries(struct.unpack(order + "I", tiff[4:8])[0])
    make, model = text(first.get(0x010F)), text(first.get(0x0110))
    # The model often repeats the make already: "Canon" + "Canon EOS 80D".
    media.camera = _clean(model if make and model.lower().startswith(make.lower()) else f"{make} {model}")
    pointer = first.get(0x8769)
    if pointer is not None:
        taken = text(entries(struct.unpack(order + "I", pointer[2])[0]).get(0x9003))
        try:
            media.taken = time.mktime(time.strptime(taken, "%Y:%m:%d %H:%M:%S"))
        except (ValueError, OverflowError):
            pass


# -- PDF ---------------------------------------------------------------------------


def from_pdf(path: Path) -> Media:
    """pypdf's reading of a PDF: its pages and its document information."""
    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(""):
        return Media(encrypted=True)
    media = Media(pages=len(reader.pages))
    info = reader.metadata or {}
    for key, name in (("/Title", "title"), ("/Author", "author"), ("/Subject", "subject"),
                      ("/Producer", "producer")):
        value = info.get(key)
        if value is not None and _clean(value):
            media.tags[name] = _clean(value)
    return media


# -- laid out ----------------------------------------------------------------------


def _duration(seconds: float) -> str:
    whole = int(round(seconds))
    hours, rest = divmod(whole, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


def _channels(layout: str, channels: int) -> str:
    if layout == "mono" or (not layout and channels == 1):
        return tr("mono")
    if layout == "stereo" or (not layout and channels == 2):
        return tr("stereo")
    return layout or tr_n("{n} channel", "{n} channels", channels)


def pairs(media: Media | None) -> list[tuple[str, str | float]]:
    """*media* as ``(label, value)``, the labels English (:data:`LABELS`), a
    date as a time for the caller to stamp."""
    if media is None:
        return []
    out: list[tuple[str, str | float]] = []
    if media.encrypted:
        return [("Encrypted", tr("yes"))]
    if media.width is not None and media.height is not None:
        out.append(("Dimensions", f"{media.width} × {media.height}"))
    if media.camera:
        out.append(("Camera", media.camera))
    if media.taken is not None:
        out.append(("Taken", media.taken))
    if media.pages is not None:
        out.append(("Pages", f"{media.pages:,}"))
    if media.video is not None:
        out.append(("Container", media.container))
    if media.duration is not None:
        out.append(("Duration", _duration(media.duration)))
    if media.video is not None:
        codec, width, height, fps = media.video
        text = f"{codec} {width} × {height}" if width and height else codec
        if fps:
            text += ", " + tr("{n} fps").format(n=f"{fps:.3f}".rstrip("0").rstrip("."))
        out.append(("Video", text))
    if media.audio is not None:
        codec, rate, layout, channels = media.audio
        parts = [codec]
        if rate:
            parts.append(tr("{n} kHz").format(n=f"{rate / 1000:.1f}".removesuffix(".0")))
        if layout or channels:
            parts.append(_channels(layout, channels))
        out.append(("Audio", ", ".join(part for part in parts if part)))
    if media.bitrate:
        out.append(("Bitrate", tr("{n} kbit/s").format(n=f"{round(media.bitrate / 1000):,}")))
    for name, value in media.tags.items():
        label = name.capitalize()
        if name == "date":
            label, value = ("Year", value[:4]) if value[:4].isdigit() else ("Date", value)
        out.append((label, value))
    return [(label, value) for label, value in out if value != ""]
