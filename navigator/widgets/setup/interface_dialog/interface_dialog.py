"""What OK means in *Interface Setup*: the ``[interface]`` section's new values."""

from __future__ import annotations

from typing import Any

from navkit.i18n import languages, tr
from navml.widgets.dialog.dialog import Dialog

from navigator.language import AUTOMATIC
from navigator.settings import SETTINGS, InterfaceData


class InterfaceDialog(Dialog):
    """The screen's furniture: DN's ``TInterfaceData.Options``, one box a bit."""

    def __init__(self, section: InterfaceData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.interface
        self.options.value = self.section.to_bits(InterfaceData.OPTIONS)
        self.history_size.value = f"{self.section.history_size:03d}"
        #: ``{shown name: code}``, automatic first; each language by its own
        #: name, as a person who cannot read the current one looks for it.
        self.languages = {tr("Automatic"): AUTOMATIC}
        self.languages.update((name, code) for code, name in languages().items())
        self.language.choices = list(self.languages)
        current = self.section.language
        self.language.value = next(
            (name for name, code in self.languages.items() if code == current), current
        )

    def accept(self) -> dict[str, Any]:
        values = InterfaceData.from_bits(InterfaceData.OPTIONS, self.options.value)
        # A blank place counts as nought; a list kept to nothing keeps one.
        text = self.history_size.value.replace(" ", "0")
        values["history_size"] = max(1, int(text)) if text.isdigit() else self.section.history_size
        values["language"] = self.languages.get(self.language.value, self.section.language)
        return values
