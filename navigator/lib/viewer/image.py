"""The viewer's *Image* reading of a file: a departure, DN's viewer had none.

A picture shown as one, in F3 and Ctrl+Q's quick view, on a terminal that
draws pictures (:attr:`navkit.capabilities.TerminalInfo.graphics`, kitty's
protocol or sixel); anywhere else an image is the bytes it always was.

:func:`decode` runs on the viewer's thread and makes a
:class:`~navkit.graphics.Picture` fitted to the cells it has, its aspect kept
by the cell's own in pixels (``cell_px``, else a cell twice as tall as wide)
and never enlarged past its own size.  Pillow reads it, when installed (the
``navigator-fm[images]`` extra, the one compiled dependency it would bring
otherwise); without it kitty is still sent a PNG as it is, kitty decoding PNG
itself, and every other picture or terminal shows the source.  An animation
shows its first frame.
"""

from __future__ import annotations

import importlib.util
import io
import struct
from dataclasses import dataclass
from typing import Any

from navkit.graphics import Picture, sixel_encode
from navkit.i18n import tr

#: What the pictures cannot be read without.
EXTRA = "navigator-fm[images]"

#: The most a picture's file may hold to be shown: it is read whole.
IMAGE_LIMIT = 64 * 1024 * 1024

#: A PNG sent to kitty as it is up to this size; a bigger one is made a
#: smaller PNG the size it is shown at, when Pillow can.
KITTY_AS_IS = 4 * 1024 * 1024

#: A cell's pixels when the terminal has not said: twice as tall as wide.
CELL_PX = (8, 16)

_PNG = b"\x89PNG\r\n\x1a\n"


def pillow() -> bool:
    """Whether Pillow is installed."""
    return importlib.util.find_spec("PIL") is not None


def available() -> str | None:
    """Why only a PNG on kitty can be shown -- Pillow missing -- or None."""
    if not pillow():
        return tr("Pictures other than PNG need Pillow: pip install {extra}").format(extra=EXTRA)
    return None


def can_show(name: str, protocol: str) -> bool:
    """Whether a file called *name* can be shown on a terminal speaking
    *protocol*, as far as its name says: anything Pillow reads, or a PNG on
    kitty without it."""
    if protocol not in ("kitty", "sixel"):
        return False
    return pillow() or (protocol == "kitty" and name.lower().endswith(".png"))


def png_size(data: bytes) -> tuple[int, int] | None:
    """A PNG's width and height from its header, or None for anything else."""
    if data[:8] != _PNG or data[12:16] != b"IHDR" or len(data) < 24:
        return None
    width, height = struct.unpack(">II", data[16:24])
    return (width, height) if width and height else None


def fit(width: int, height: int, cols: int, rows: int,
        cell_px: tuple[int, int] | None) -> tuple[int, int]:
    """The cells a *width* x *height* picture takes in *cols* x *rows*: as
    large as fits with its aspect kept, never larger than itself."""
    cw, ch = cell_px or CELL_PX
    scale = min(cols * cw / width, rows * ch / height, 1.0)
    return (max(1, min(cols, round(width * scale / cw))),
            max(1, min(rows, round(height * scale / ch))))


@dataclass(eq=False)
class Shown:
    """A picture made for the viewer, and what it says about it."""

    picture: Picture
    #: Its format, as Pillow names it (``PNG``, ``JPEG``...).
    format: str
    #: Its own size in pixels.
    width: int
    height: int


def decode(data: bytes, cols: int, rows: int, cell_px: tuple[int, int] | None,
           protocol: str) -> Shown:
    """On the thread: *data*, a whole picture file, made into a
    :class:`Shown` *cols* x *rows* cells at most, for *protocol*.

    Raises ``ValueError`` for what cannot be shown -- not a picture, or not
    one this can read -- and the viewer shows the source.
    """
    size = png_size(data)
    if protocol == "kitty" and size is not None and (len(data) <= KITTY_AS_IS or not pillow()):
        c, r = fit(*size, cols, rows, cell_px)
        return Shown(Picture(c, r, png=data), "PNG", *size)
    if not pillow():
        raise ValueError("not a PNG, and no Pillow to read it")
    from PIL import Image, ImageOps

    try:
        image: Any = Image.open(io.BytesIO(data))
        format = image.format or ""
        image.seek(0)
        image = ImageOps.exif_transpose(image)
        image.load()
    except Exception as error:  # Pillow raises what each plugin likes
        raise ValueError(f"not a picture Pillow reads: {error}") from error
    width, height = image.size
    if not (width and height):
        raise ValueError("an empty picture")
    c, r = fit(width, height, cols, rows, cell_px)
    cw, ch = cell_px or CELL_PX
    box = (max(1, min(width, c * cw)), max(1, min(height, r * ch)))
    rgba = image.convert("RGBA")
    if rgba.size != box:
        rgba = rgba.resize(box, Image.Resampling.LANCZOS)
    if protocol == "kitty":
        out = io.BytesIO()
        rgba.save(out, "PNG", compress_level=1)
        return Shown(Picture(c, r, png=out.getvalue()), format, width, height)
    return Shown(Picture(c, r, sixel=_sixel(rgba)), format, width, height)


def _sixel(rgba: Any) -> str:
    """*rgba* in at most 255 colours, a transparent pixel as the 256th."""
    from PIL import Image

    alpha = rgba.getchannel("A")
    paletted = rgba.convert("RGB").quantize(255, dither=Image.Dither.FLOYDSTEINBERG)
    see_through = alpha.point(lambda a: 255 if a < 128 else 0, mode="1")
    transparent = None
    if see_through.getbbox() is not None:
        paletted.paste(255, mask=see_through)
        transparent = 255
    raw = paletted.getpalette() or []
    palette = [tuple(raw[i : i + 3]) for i in range(0, min(len(raw), 255 * 3), 3)]
    width, height = paletted.size
    return sixel_encode(paletted.tobytes(), width, height, palette, transparent)  # type: ignore[arg-type]
