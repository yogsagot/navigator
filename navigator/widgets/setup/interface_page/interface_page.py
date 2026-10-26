"""What OK means in *Interface Setup*: the ``[interface]`` section's new values,
and ``[appearance]``'s colour depth and check marks."""

from __future__ import annotations

from typing import Any

from navkit.i18n import languages, tr
from navkit.widget import Widget

from navigator.lib.config.language import AUTOMATIC
from navigator.settings import COLOR_DEPTHS, MARK_LOOKS, SETTINGS, AppearanceData, InterfaceData


class InterfacePage(Widget):
    """The screen's furniture: DN's ``TInterfaceData.Options``, one box a bit."""

    def __init__(
        self,
        section: InterfaceData | None = None,
        appearance: AppearanceData | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.interface
        self.appearance = appearance or SETTINGS.appearance
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
        sides = InterfaceData.field("settings_tabs").choices
        self.settings_tabs.value = self.settings_tabs.sel = sides.index(self.section.settings_tabs)
        strips = InterfaceData.field("window_strip").choices
        self.window_strip.value = self.window_strip.sel = strips.index(self.section.window_strip)
        #: ``{shown name: depth}``, in ``COLOR_DEPTHS``' order.
        self.depths = dict(zip(
            (tr("Automatic"), tr("Monochrome"), tr("8 colours"), tr("16 colours"),
             tr("256 colours"), tr("True colour")),
            COLOR_DEPTHS,
        ))
        self.colors.choices = list(self.depths)
        self.colors.value = next(
            name for name, depth in self.depths.items() if depth == self.appearance.colors
        )
        #: ``{shown name: look}``, in ``MARK_LOOKS``' order, each showing its
        #: own marks.
        self.looks = dict(zip(
            (tr("Classic [X] (•)"), tr("Brackets [✓] (●)"), tr("Boxes ☑ ◉")),
            MARK_LOOKS,
        ))
        self.marks.choices = list(self.looks)
        self.marks.value = next(
            (name for name, look in self.looks.items() if look == self.appearance.marks),
            self.marks.choices[0],
        )

    def accept(self) -> dict[str, dict[str, Any]]:
        values = InterfaceData.from_bits(InterfaceData.OPTIONS, self.options.value)
        # A blank place counts as nought; a list kept to nothing keeps one.
        text = self.history_size.value.replace(" ", "0")
        values["history_size"] = max(1, int(text)) if text.isdigit() else self.section.history_size
        values["language"] = self.languages.get(self.language.value, self.section.language)
        values["settings_tabs"] = InterfaceData.field("settings_tabs").choices[self.settings_tabs.value]
        values["window_strip"] = InterfaceData.field("window_strip").choices[self.window_strip.value]
        colors = self.depths.get(self.colors.value, self.appearance.colors)
        marks = self.looks.get(self.marks.value, self.appearance.marks)
        return {"interface": values, "appearance": {"colors": colors, "marks": marks}}
