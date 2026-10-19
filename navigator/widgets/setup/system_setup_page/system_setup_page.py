"""What OK means in *System Setup*: the ``[system]`` section's new values."""

from __future__ import annotations

from typing import Any


from navkit.widget import Widget

from navigator.settings import ON_ERROR, SETTINGS, SystemData


class SystemSetupPage(Widget):
    """DN's ``TSystemData``: its *Options* word and its temporary directory, *Unexpected failures* and *Report a stall after*."""

    def __init__(self, section: SystemData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.system
        self.options.value = self.section.to_bits(SystemData.OPTIONS)
        self.temp_dir.value = self.section.temp_dir
        self.on_error.value = ON_ERROR.index(self.section.on_error)
        self.stall_report.value = f"{self.section.stall_report:03d}"

    def accept(self) -> dict[str, Any]:
        values: dict[str, Any] = SystemData.from_bits(SystemData.OPTIONS, self.options.value)
        values["temp_dir"] = self.temp_dir.value.strip()
        values["on_error"] = ON_ERROR[self.on_error.value]
        text = self.stall_report.value.replace(" ", "0")
        values["stall_report"] = int(text) if text.isdigit() else self.section.stall_report
        return values
