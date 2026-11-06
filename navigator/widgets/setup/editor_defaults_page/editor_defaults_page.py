"""What OK means in *Editor/Viewer Defaults*: two sections' new values."""

from __future__ import annotations

from typing import Any


from navkit.i18n import tr
from navkit.widget import Widget

from navigator.lib.editor import encodings
from navigator.settings import SETTINGS, EditorDefaultsData, ViewerDefaultsData

#: The numbers, by the id of the line each is typed in.
NUMBERS = ("left_margin", "right_margin", "paragraph", "tab_size")


class EditorDefaultsPage(Widget):
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
        self.editor.tooltips = EditorDefaultsData.tooltips(EditorDefaultsData.OPTIONS)
        self.viewer.value = self.viewer_section.to_bits(ViewerDefaultsData.OPTIONS)
        self.viewer.tooltips = ViewerDefaultsData.tooltips(ViewerDefaultsData.OPTIONS)
        for name in NUMBERS:
            getattr(self, name).value = f"{getattr(self.editor_section, name):03d}"
            getattr(self, name).tooltip = self.editor_section.tooltip(name)
        self.line_divisor.value = EditorDefaultsData.LINE_DIVISORS.index(
            self.editor_section.line_divisor
        )
        self.line_divisor.tooltip = self.editor_section.tooltip("line_divisor")
        #: Each choice's caption and the key it stands for.
        self.encodings = {tr("UTF-8, bytes kept"): "utf-8",
                          **{encodings.caption(key): key for key in encodings.ONE_BYTE}}
        self.fallback_encoding.choices = list(self.encodings)
        self.fallback_encoding.value = next(
            (caption for caption, key in self.encodings.items()
             if key == self.editor_section.fallback_encoding), next(iter(self.encodings)))
        self.fallback_encoding.tooltip = self.editor_section.tooltip("fallback_encoding")

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
        editor["fallback_encoding"] = self.encodings.get(self.fallback_encoding.value,
                                                         self.editor_section.fallback_encoding)
        viewer = ViewerDefaultsData.from_bits(ViewerDefaultsData.OPTIONS, self.viewer.value)
        return {"editor": editor, "viewer": viewer}
