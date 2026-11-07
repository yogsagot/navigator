"""What OK means in *Tools*: ``[encryption] age_identities``, and the
Process list's, Services' and the System monitor's settings -- four
sections, answered by name."""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.widget import Widget

from navigator.settings import SETTINGS, ServicesData


def _number(text: str, keep: int) -> int:
    text = text.replace(" ", "0")
    return int(text) if text.isdigit() else keep


def manager_names() -> dict[str, str]:
    """``{shown name: [services] manager}``, in ``ServicesData.MANAGERS``' order."""
    shown = {"auto": tr("Automatic (the one running)"), "systemd": "systemd", "openrc": "OpenRC",
             "runit": "runit", "sysvinit": "SysVinit"}
    return {shown[name]: name for name in ServicesData.MANAGERS}


class ToolsPage(Widget):
    """Encryption's identities and Utilities' windows' intervals."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        encryption, processes = SETTINGS.encryption, SETTINGS.processes
        services, monitor = SETTINGS.services, SETTINGS.monitor
        self.age_identities.value = encryption.age_identities
        self.age_identities.entry.tooltip = encryption.tooltip("age_identities")
        self.processes_refresh.value = f"{processes.refresh:02d}"
        self.processes_refresh.tooltip = processes.tooltip("refresh")
        #: ``{shown name: [services] manager}``.
        self.managers = manager_names()
        self.services_manager.choices = list(self.managers)
        self.services_manager.value = next(
            (shown for shown, name in self.managers.items() if name == services.manager),
            self.services_manager.choices[0])
        self.services_manager.tooltip = tr("{doc} -- used from the next time Services opens").format(
            doc=services.tooltip("manager"))
        self.services_refresh.value = f"{services.refresh:02d}"
        self.services_refresh.tooltip = services.tooltip("refresh")
        self.journal_lines.value = f"{services.journal_lines:04d}"
        self.journal_lines.tooltip = services.tooltip("journal_lines")
        self.monitor_refresh.value = f"{monitor.refresh:02d}"
        self.monitor_refresh.tooltip = monitor.tooltip("refresh")

    def accept(self) -> dict[str, dict[str, Any]]:
        processes, services, monitor = SETTINGS.processes, SETTINGS.services, SETTINGS.monitor
        return {
            "encryption": {"age_identities": " ".join(self.age_identities.value.split())},
            "processes": {"refresh": _number(self.processes_refresh.value, processes.refresh)},
            "services": {
                "manager": self.managers.get(self.services_manager.value, services.manager),
                "refresh": _number(self.services_refresh.value, services.refresh),
                "journal_lines": _number(self.journal_lines.value, services.journal_lines),
            },
            "monitor": {"refresh": _number(self.monitor_refresh.value, monitor.refresh)},
        }
