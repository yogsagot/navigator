"""What OK means in *Editor/Viewer Defaults*: two sections' new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import SETTINGS, EditorDefaultsData, ViewerDefaultsData

#: The numbers, by the id of the line each is typed in.
NUMBERS = ("left_margin", "right_margin", "paragraph", "tab_size")


class EditorDefaultsDialog(Dialog):
    """DN's ``TEditorDefaultsData``: the editor's word and numbers, and the viewer's word.

    One dialog over two sections, as DN's was over one record:
    :meth:`accept` answers ``{"editor": {...}, "viewer": {...}}``.
    """

    def __init__(
        self,
        editor: EditorDefaultsData | None = None,
        viewer: ViewerDefaultsData | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.editor_section = editor or SETTINGS.editor
        self.viewer_section = viewer or SETTINGS.viewer
        self.editor.value = self.editor_section.to_bits(EditorDefaultsData.OPTIONS)
        self.viewer.value = self.viewer_section.to_bits(ViewerDefaultsData.OPTIONS)
        for name in NUMBERS:
            getattr(self, name).value = f"{getattr(self.editor_section, name):03d}"
        self.line_divisor.value = EditorDefaultsData.LINE_DIVISORS.index(
            self.editor_section.line_divisor
        )

    def _number(self, name: str) -> int:
        """The number typed for *name*; a blank place counts as nought."""
        text = getattr(self, name).value.replace(" ", "0")
        try:
            return int(text)
        except ValueError:
            return getattr(self.editor_section, name)

    def accept(self) -> dict[str, Any]:
        editor: dict[str, Any] = EditorDefaultsData.from_bits(
            EditorDefaultsData.OPTIONS, self.editor.value
        )
        for name in NUMBERS:
            editor[name] = self._number(name)
        # A tab of nought columns would never stop.
        editor["tab_size"] = max(1, editor["tab_size"])
        editor["line_divisor"] = EditorDefaultsData.LINE_DIVISORS[self.line_divisor.value]
        viewer = ViewerDefaultsData.from_bits(ViewerDefaultsData.OPTIONS, self.viewer.value)
        return {"editor": editor, "viewer": viewer}
