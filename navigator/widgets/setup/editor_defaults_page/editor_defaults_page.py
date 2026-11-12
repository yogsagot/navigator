"""What OK means in *Editor/Viewer Defaults*: two sections' new values.  Each
control says what it edits (``key:``); the fallback encoding, a list made at
run time, is read here."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navigator.lib.editor import encodings
from navigator.widgets.setup.settings_page import SettingsPage


class EditorDefaultsPage(SettingsPage):
    """DN's ``TEditorDefaultsData``: the editor's word and numbers, and the viewer's word.

    One dialog over two sections, as DN's was over one record:
    :meth:`accept` answers ``{"editor": {...}, "viewer": {...}}``.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Each choice's caption and the key it stands for.
        self.encodings = {tr("UTF-8, bytes kept"): "utf-8",
                          **{encodings.caption(key): key for key in encodings.LEGACY}}
        self.fallback_encoding.choices = list(self.encodings)
        self.fallback_encoding.value = next(
            (caption for caption, key in self.encodings.items()
             if key == self.section.fallback_encoding), next(iter(self.encodings)))
        self.fallback_encoding.tooltip = self.section.tooltip("fallback_encoding")

    def accept(self) -> dict[str, Any]:
        values = super().accept()
        editor = values["editor"]
        # A tab of nought columns would never stop.
        editor["tab_size"] = max(1, editor["tab_size"])
        editor["fallback_encoding"] = self.encodings.get(self.fallback_encoding.value,
                                                         self.section.fallback_encoding)
        return values
