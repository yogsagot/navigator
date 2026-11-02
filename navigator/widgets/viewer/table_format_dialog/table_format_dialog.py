"""What OK means in *Format*: the dialect the file is read in again."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.viewer import ENCODINGS
from navigator.lib.viewer.table import DELIMITERS, Dialect


class TableFormatDialog(Dialog):
    """The delimiter, the header and the encoding, seeded from *dialect*."""

    def __init__(self, dialect: Dialect, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dialect = dialect
        if dialect.delimiter in DELIMITERS:
            self.delimiter.value = self.delimiter.sel = DELIMITERS.index(dialect.delimiter)
        else:
            self.delimiter.value = self.delimiter.sel = len(DELIMITERS)
            self.other.value = dialect.delimiter
        self.options.value = 1 if dialect.header else 0
        self.names = {label: codec for codec, label in ENCODINGS}
        self.encoding.choices = list(self.names)
        codec = dialect.encoding.replace("-sig", "")
        self.encoding.value = next((label for label, value in self.names.items() if value == codec),
                                   ENCODINGS[0][1])

    def accept(self) -> Dialect | None:
        """The dialect chosen; None when *Other* has no one character."""
        if self.delimiter.value < len(DELIMITERS):
            delimiter = DELIMITERS[self.delimiter.value]
        else:
            delimiter = self.other.value
            if len(delimiter) != 1:
                return None
        codec = self.names.get(self.encoding.value, "utf-8")
        if codec == "utf-8" and self.dialect.encoding == "utf-8-sig":
            codec = "utf-8-sig"
        return replace(self.dialect, delimiter=delimiter, header=bool(self.options.value & 1), encoding=codec)
