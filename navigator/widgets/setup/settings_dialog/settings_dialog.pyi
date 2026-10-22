# navml: generated
"""The merged surface of ``navigator.widgets.setup.settings_dialog.settings_dialog``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.tab_view import TabView
from navigator.widgets.setup.column_defaults_page import ColumnDefaultsPage
from navigator.widgets.setup.communications_page import CommunicationsPage
from navigator.widgets.setup.confirmations_page import ConfirmationsPage
from navigator.widgets.setup.drive_info_page import DriveInfoPage
from navigator.widgets.setup.editor_defaults_page import EditorDefaultsPage
from navigator.widgets.setup.fm_defaults_page import FMDefaultsPage
from navigator.widgets.setup.fm_setup_page import FMSetupPage
from navigator.widgets.setup.highlight_page import HighlightPage
from navigator.widgets.setup.interface_page import InterfacePage
from navigator.widgets.setup.savers_page import SaversPage
from navigator.widgets.setup.startup_page import StartupPage
from navigator.widgets.setup.system_setup_page import SystemSetupPage

from typing import Any
from navkit.i18n import tr
from navkit.reactive import bind, unbind
from navkit.screen import Surface
from navkit.widget import Widget
from navigator.settings import SETTINGS


class SettingsDialog(Dialog, _Component):
    tabs: TabView
    system: SystemSetupPage
    startup: StartupPage
    interface: InterfacePage
    confirmations: ConfirmationsPage
    savers: SaversPage
    editor_viewer: EditorDefaultsPage
    file_manager: FMSetupPage
    drive_info: DriveInfoPage
    panel_defaults: FMDefaultsPage
    column_defaults: ColumnDefaultsPage
    highlight_groups: HighlightPage
    remote: CommunicationsPage
    def __init__(self, tab: str = ..., side: str | None = ..., **kwargs: Any) -> None: ...
    def _buttons_under_pages(self) -> None: ...
    def tab_hint(self) -> tuple[int, str] | None: ...
    def render(self, surface: Surface) -> None: ...
    def page(self, tab: str) -> Widget: ...
    def accept(self) -> dict[str, dict[str, Any]]: ...
