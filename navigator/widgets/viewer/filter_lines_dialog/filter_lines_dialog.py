"""What OK means in *Filter lines*: a :class:`~navigator.lib.viewer.lines.LinePattern`, or nothing."""

from __future__ import annotations

import re
from typing import Any

from navkit.i18n import tr
from navkit.text import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.viewer.lines import LinePattern


class FilterLinesDialog(Dialog):
    """Ctrl+G in a viewer: the pattern and its switches, opened on the last."""

    def __init__(self, last: LinePattern | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if last is not None:
            self.what.value = last.text
            self.options.value = int(last.regex) | int(last.case) << 1 | int(last.invert) << 2

    def pattern(self) -> LinePattern | None:
        what = self.what.value
        if not what:
            return None
        value = self.options.value
        return LinePattern(what, regex=bool(value & 1), case=bool(value & 2), invert=bool(value & 4))

    def valid(self) -> bool:
        """Refused, with a box saying why, while a regular expression is not one."""
        pattern = self.pattern()
        if pattern is None:
            return True
        try:
            pattern.compile()
        except re.error as error:
            if self.application is not None:
                box = Dialog(title=tr("Error"),
                             prompt=tr("Not a regular expression: {error}").format(error=escape_caption(str(error))),
                             buttons="ok")
                self.spawn(box.execute(self.application))
            return False
        return True

    def accept(self) -> LinePattern | str:
        """The pattern, or "" for an empty line: the filter taken off.
        Cancel says ``None``."""
        return self.pattern() or ""
