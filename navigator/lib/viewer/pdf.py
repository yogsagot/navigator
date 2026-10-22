"""The viewer's *PDF* reading of a file: a departure, DN's viewer had none.

``render`` reads a whole document with pypdf and lays out the text of each
page into a :class:`~navigator.lib.viewer.layout.Builder`: a heading naming
the page, its text in paragraphs (lines run together between blank lines)
wrapped to the width, and a rule between pages.  Only the text is shown --
pictures, drawings and fonts are not, since a cell is not a pixel -- and a
page that is a scanned image shows nothing but its heading.

**Rows are not offsets into the file**: a PDF's text sits in compressed
streams, not at a byte a row could name.  Each page is given an even share of
the file's size, and its paragraphs offsets spread across that share, so
``src`` still only grows, the scroll bar moves with the pages and switching
back to the source lands in proportion -- on the PDF's own bytes, which are
what the source is.  For the same reason a search (F7), which runs over the
source, does not find the rendered text.

A document locked with a password other than the empty one raises, as an
unreadable file does, and the viewer shows the source.
"""

from __future__ import annotations

import io
import logging
import re

from navkit.i18n import tr

from navigator.lib.viewer.layout import ASCII, UNICODE, Builder, Layout, _cells

#: The most a PDF may hold to be rendered: bigger than ``RENDER_LIMIT``, since
#: a PDF carries fonts and pictures the text is a small part of.
PDF_LIMIT = 64 * 1024 * 1024

#: The blank lines a page's text is cut into paragraphs at.
_PARAGRAPHS = re.compile(r"\n[ \t\f\v]*\n")


def _paragraphs(text: str) -> list[str]:
    """A page's text in paragraphs, each one's lines joined by a blank."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = []
    for chunk in _PARAGRAPHS.split(text):
        joined = " ".join(line.strip() for line in chunk.split("\n") if line.strip())
        if joined:
            paragraphs.append(joined)
    return paragraphs


def render(data: bytes, width: int, *, codec: str = "utf-8", unicode: bool = True) -> Layout:
    """*data*, a PDF document, laid out *width* columns wide; *unicode* draws
    with box characters, else with ASCII.  *codec* is not used: a PDF says
    what its text is encoded in."""
    from pypdf import PdfReader

    # pypdf warns through logging about every flaw it reads past; a damaged
    # file still renders what it can, quietly.
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("the PDF is locked with a password")
    pages = len(reader.pages)
    builder = Builder([0], width, UNICODE if unicode else ASCII)
    for index, page in enumerate(reader.pages):
        start = index * len(data) // max(1, pages)
        span = (index + 1) * len(data) // max(1, pages) - start
        if index:
            builder.rule(start)
        title = tr("Page {page} of {pages}").format(page=index + 1, pages=pages)
        builder.heading(2, _cells(title, builder.classes("heading", "h2")), start)
        try:
            text = page.extract_text() or ""
        except Exception:
            # One page pypdf cannot read is not the document's end.
            text = ""
        paragraphs = _paragraphs(text)
        for number, paragraph in enumerate(paragraphs):
            src = start + span * (number + 1) // (len(paragraphs) + 1)
            builder.paragraph(_cells(paragraph, builder.classes()), src)
    return builder.finish()
