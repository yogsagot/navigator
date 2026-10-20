# navml: generated
"""Generated from ``settings_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # settings_dialog.nml:1
from navml.widgets.dialog.tab_view import TabView    # settings_dialog.nml:2
from navigator.widgets.setup.column_defaults_page import ColumnDefaultsPage    # settings_dialog.nml:3
from navigator.widgets.setup.communications_page import CommunicationsPage    # settings_dialog.nml:4
from navigator.widgets.setup.confirmations_page import ConfirmationsPage    # settings_dialog.nml:5
from navigator.widgets.setup.drive_info_page import DriveInfoPage    # settings_dialog.nml:6
from navigator.widgets.setup.editor_defaults_page import EditorDefaultsPage    # settings_dialog.nml:7
from navigator.widgets.setup.fm_defaults_page import FMDefaultsPage    # settings_dialog.nml:8
from navigator.widgets.setup.fm_setup_page import FMSetupPage    # settings_dialog.nml:9
from navigator.widgets.setup.highlight_page import HighlightPage    # settings_dialog.nml:10
from navigator.widgets.setup.interface_page import InterfacePage    # settings_dialog.nml:11
from navigator.widgets.setup.savers_page import SaversPage    # settings_dialog.nml:12
from navigator.widgets.setup.startup_page import StartupPage    # settings_dialog.nml:13
from navigator.widgets.setup.system_setup_page import SystemSetupPage    # settings_dialog.nml:14

__navml_component__ = "SettingsDialog"

__all__ = ["SettingsDialog"]


class SettingsDialog(Dialog, _Component):
    """Options > Settings: every ``navigator.ini`` section's setup in one box,

    a page to a tab.  **A departure**: DOS Navigator gave each its own
    resource (``dlgSystemSetup``, ``dlgInterfaceSetup``, ...), and each menu
    item under Options > Configuration and Options > File Manager still opens
    this one on its own page.  The ids are the pages' names, which
    :data:`PAGES` maps to the sections they answer for.

    Tall enough for the tallest page (*Panel defaults*) under the one row of
    tabs, scrolled between arrows, whose baseline is each page's first row:
    24 rows, so an 80 by 24 terminal shows it whole.  Interface's *Settings
    tabs* puts them in a column down the left instead, and the Python half
    widens the box to 80 for that.
    """

    #: The document this class was generated from.
    __navml_source__ = "settings_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    tabs: TabView    # settings_dialog.nml:39
    system: SystemSetupPage    # settings_dialog.nml:47
    startup: StartupPage    # settings_dialog.nml:50
    interface: InterfacePage    # settings_dialog.nml:53
    confirmations: ConfirmationsPage    # settings_dialog.nml:56
    savers: SaversPage    # settings_dialog.nml:59
    editor_viewer: EditorDefaultsPage    # settings_dialog.nml:62
    file_manager: FMSetupPage    # settings_dialog.nml:65
    drive_info: DriveInfoPage    # settings_dialog.nml:68
    panel_defaults: FMDefaultsPage    # settings_dialog.nml:71
    column_defaults: ColumnDefaultsPage    # settings_dialog.nml:74
    highlight_groups: HighlightPage    # settings_dialog.nml:77
    remote: CommunicationsPage    # settings_dialog.nml:80

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tabs = TabView(parent=self)    # settings_dialog.nml:38
        self.system = SystemSetupPage(parent=self.tabs)    # settings_dialog.nml:46
        self.startup = StartupPage(parent=self.tabs)    # settings_dialog.nml:49
        self.interface = InterfacePage(parent=self.tabs)    # settings_dialog.nml:52
        self.confirmations = ConfirmationsPage(parent=self.tabs)    # settings_dialog.nml:55
        self.savers = SaversPage(parent=self.tabs)    # settings_dialog.nml:58
        self.editor_viewer = EditorDefaultsPage(parent=self.tabs)    # settings_dialog.nml:61
        self.file_manager = FMSetupPage(parent=self.tabs)    # settings_dialog.nml:64
        self.drive_info = DriveInfoPage(parent=self.tabs)    # settings_dialog.nml:67
        self.panel_defaults = FMDefaultsPage(parent=self.tabs)    # settings_dialog.nml:70
        self.column_defaults = ColumnDefaultsPage(parent=self.tabs)    # settings_dialog.nml:73
        self.highlight_groups = HighlightPage(parent=self.tabs)    # settings_dialog.nml:76
        self.remote = CommunicationsPage(parent=self.tabs)    # settings_dialog.nml:79

        self.modal_width = 76    # settings_dialog.nml:29
        self.modal_height = 24    # settings_dialog.nml:30
        self.title = _bind(lambda _o: _tr('Settings'), yielding=True)    # settings_dialog.nml:31

        self.tabs.x = _bind(lambda _o: 1 if _o.side == 'left' else 0)    # settings_dialog.nml:40
        self.tabs.y = _bind(lambda _o: 0 if _o.side == 'left' else 1)    # settings_dialog.nml:41
        self.tabs.width = _bind(    # settings_dialog.nml:42
            lambda _o: max(0, _o.parent.width - (2 if _o.side == 'left' else 0))
        )
        self.tabs.height = _bind(    # settings_dialog.nml:43
            lambda _o: max(0, _o.parent.height - (0 if _o.side == 'left' else 5))
        )
        self.tabs.joins_frame = True    # settings_dialog.nml:44

        self.system.title = _bind(lambda _o: _tr('System'), yielding=True)    # settings_dialog.nml:48

        self.startup.title = _bind(lambda _o: _tr('Startup'), yielding=True)    # settings_dialog.nml:51

        self.interface.title = _bind(    # settings_dialog.nml:54
            lambda _o: _tr('Interface'),
            yielding=True,
        )

        self.confirmations.title = _bind(    # settings_dialog.nml:57
            lambda _o: _tr('Confirmations'),
            yielding=True,
        )

        self.savers.title = _bind(lambda _o: _tr('Savers'), yielding=True)    # settings_dialog.nml:60

        self.editor_viewer.title = _bind(    # settings_dialog.nml:63
            lambda _o: _tr('Editor/Viewer'),
            yielding=True,
        )

        self.file_manager.title = _bind(    # settings_dialog.nml:66
            lambda _o: _tr('File panels'),
            yielding=True,
        )

        self.drive_info.title = _bind(    # settings_dialog.nml:69
            lambda _o: _tr('Info panel'),
            yielding=True,
        )

        self.panel_defaults.title = _bind(    # settings_dialog.nml:72
            lambda _o: _tr('Panel defaults'),
            yielding=True,
        )

        self.column_defaults.title = _bind(    # settings_dialog.nml:75
            lambda _o: _tr('Columns'),
            yielding=True,
        )

        self.highlight_groups.title = _bind(    # settings_dialog.nml:78
            lambda _o: _tr('Highlight'),
            yielding=True,
        )

        self.remote.title = _bind(    # settings_dialog.nml:81
            lambda _o: _tr('Communications'),
            yielding=True,
        )
