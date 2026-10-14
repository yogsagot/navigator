"""What OK means in *System Setup*: the ``[system]`` section's new values."""

from __future__ import annotations

from typing import Any

from navml.widgets.dialog.dialog import Dialog

from navigator.settings import ON_ERROR, SETTINGS, SystemData


class SystemSetupDialog(Dialog):
    """DN's ``TSystemData``: its *Options* word and its temporary directory, and *Unexpected failures*."""

    def __init__(self, section: SystemData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.system
        self.options.value = self.section.to_bits(SystemData.OPTIONS)
        self.temp_dir.value = self.section.temp_dir
        self.on_error.value = ON_ERROR.index(self.section.on_error)

    def accept(self) -> dict[str, Any]:
        values: dict[str, Any] = SystemData.from_bits(SystemData.OPTIONS, self.options.value)
        values["temp_dir"] = self.temp_dir.value.strip()
        values["on_error"] = ON_ERROR[self.on_error.value]
        return values
