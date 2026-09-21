"""What a document is told when it cannot be read.

One exception for the whole toolchain, carrying the position in the markup
rather than in whatever navml was doing at the time.  Every check in the parser
and every check in the code generator names a ``.nml`` line, which is the one
thing ``navml/DESIGN.md`` asks of all of them without exception -- a document's
author is reading the markup, never the node graph and never the emitted
Python.

Modelled on :class:`navkit.stylesheet.StylesheetError`, which solved the same
problem for ``.nss`` and reads the same way at a terminal::

    button.nml:12: 'parent' is reserved and cannot be an id

Deliberately *not* :class:`navml._merge.ComponentError`: that one is an
:class:`ImportError`, raised when two halves of an already-built component
disagree at import time, and the import system treats it as such.  This one is
raised while reading a file, long before anything is importable.
"""

from __future__ import annotations


class MarkupError(Exception):
    """A document could not be read.  Carries the source line."""

    def __init__(self, message: str, line: int, filename: str = "<markup>"):
        super().__init__(f"{filename}:{line}: {message}")
        self.message = message
        self.line = line
        self.filename = filename
