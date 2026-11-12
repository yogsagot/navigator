"""What OK means in *Tools*: ``[encryption] age_identities``, and the
Process list's, Services' and the System monitor's settings -- four
sections, answered by name."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr

from navigator.settings import SETTINGS, ServicesData
from navigator.widgets.setup.settings_page import SettingsPage


def manager_names() -> dict[str, str]:
    """``{shown name: [services] manager}``, in ``ServicesData.MANAGERS``' order."""
    shown = {"auto": tr("Automatic (the one running)"), "systemd": "systemd", "openrc": "OpenRC",
             "runit": "runit", "sysvinit": "SysVinit"}
    return {shown[name]: name for name in ServicesData.MANAGERS}


class ToolsPage(SettingsPage):
    """Encryption's identities and Utilities' windows' intervals.  The
    intervals say what they edit (``key:``); the identities and the service
    manager are read here."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        encryption, services = SETTINGS.encryption, SETTINGS.services
        self.age_identities.value = encryption.age_identities
        self.age_identities.entry.tooltip = encryption.tooltip("age_identities")
        self.managers = manager_names()
        self.services_manager.choices = list(self.managers)
        self.services_manager.value = next(
            (shown for shown, name in self.managers.items() if name == services.manager),
            self.services_manager.choices[0])
        self.services_manager.tooltip = tr("{doc} -- used from the next time Services opens").format(
            doc=services.tooltip("manager"))

    def accept(self) -> dict[str, dict[str, Any]]:
        values = super().accept()
        values["encryption"] = {"age_identities": " ".join(self.age_identities.value.split())}
        values["services"]["manager"] = self.managers.get(self.services_manager.value, SETTINGS.services.manager)
        return values
