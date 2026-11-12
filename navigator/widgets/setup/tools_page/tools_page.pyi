# navml: generated
"""The merged surface of ``navigator.widgets.setup.tools_page.tools_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.masked_field import MaskedField
from navml.widgets.dialog.static_text import StaticText
from navigator.widgets.setup.settings_page import SettingsPage

from typing import Any
from navkit.i18n import tr
from navigator.settings import SETTINGS, ServicesData


class ToolsPage(SettingsPage, _Component):
    title: str
    age_identities: Field
    processes_refresh: MaskedField
    processes_unit: StaticText
    services_manager: ChoiceField
    services_refresh: MaskedField
    services_unit: StaticText
    journal_lines: MaskedField
    monitor_refresh: MaskedField
    monitor_unit: StaticText
    def __init__(self, **kwargs: Any) -> None: ...
    def accept(self) -> dict[str, dict[str, Any]]: ...
