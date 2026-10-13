"""What OK means in the box: the new name, if it is one."""

from __future__ import annotations

import os
from typing import Any

from navkit.i18n import tr
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog


class RenameDialog(Dialog):
    """The line seeded with *name*, its stem selected and the cursor after it,
    so typing replaces the name and keeps the extension.  A directory's, or a
    name with no extension (``.bashrc`` has none), is selected whole."""

    def __init__(self, name: str = "", *, is_dir: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.caption = tr("~R~ename {name} to").format(name=escape_caption(name))
        self.line.value = name
        stem = name if is_dir else os.path.splitext(name)[0]
        self.line.entry.anchor, self.line.entry.cursor = 0, len(stem)

    def accept(self) -> Any:
        """The name typed, or ``None`` for an empty line, as Cancel answers."""
        return self.line.value or None
