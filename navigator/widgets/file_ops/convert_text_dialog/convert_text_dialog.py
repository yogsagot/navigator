"""The handlers behind ``convert_text_dialog.nml``: what it opens on, and
what OK means.

It opens on the choices last accepted, kept in ``navigator.ini``'s
``[text_conversion]``.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.lib.editor import encodings
from navigator.settings import SETTINGS, TextConversionData


class ConvertTextDialog(Dialog):
    """*Convert Text Files*: the encoding, what non-UTF-8 is read as, the
    line endings and whether the times are kept."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        section = SETTINGS.text_conversion
        #: Each choice's caption and the key it stands for.
        self.encodings = {tr("Keep each file's"): "keep",
                          **{encodings.caption(key): key for key, _, _ in encodings.CODECS}}
        self.fallbacks = {tr("Nothing: leave such files alone"): encodings.UTF8,
                          **{encodings.caption(key): key for key in encodings.LEGACY}}
        self.encoding.choices = list(self.encodings)
        self.encoding.value = _caption_of(self.encodings, section.encoding)
        self.fallback.choices = list(self.fallbacks)
        self.fallback.value = _caption_of(self.fallbacks, section.fallback)
        self.ending.value = self.ending.sel = TextConversionData.ENDINGS.index(section.ending)
        self.options.value = int(section.keep_times)
        self.encoding.tooltip = section.tooltip("encoding")
        self.fallback.tooltip = section.tooltip("fallback")
        self.ending.tooltip = section.tooltip("ending")
        self.options.tooltip = section.tooltip("keep_times")

    def mounted(self) -> None:
        super().mounted()
        # The line endings first: what is changed most, and Enter on a choice
        # line drops its list rather than answering the box.
        self.ending.focus()

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon)

    def accept(self) -> dict[str, Any]:
        """``{"encoding", "ending", "fallback", "keep_times"}`` as the section keeps them."""
        section = SETTINGS.text_conversion
        return {
            "encoding": self.encodings.get(self.encoding.value, section.encoding),
            "ending": TextConversionData.ENDINGS[self.ending.value],
            "fallback": self.fallbacks.get(self.fallback.value, section.fallback),
            "keep_times": bool(self.options.value & 1),
        }

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True


def _caption_of(choices: dict[str, str], key: str) -> str:
    return next((caption for caption, value in choices.items() if value == key), next(iter(choices)))
