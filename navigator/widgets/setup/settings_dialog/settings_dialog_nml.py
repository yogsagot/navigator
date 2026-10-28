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
from navigator.widgets.setup.country_page import CountryPage    # settings_dialog.nml:6
from navigator.widgets.setup.drive_info_page import DriveInfoPage    # settings_dialog.nml:7
from navigator.widgets.setup.editor_defaults_page import EditorDefaultsPage    # settings_dialog.nml:8
from navigator.widgets.setup.fm_defaults_page import FMDefaultsPage    # settings_dialog.nml:9
from navigator.widgets.setup.fm_setup_page import FMSetupPage    # settings_dialog.nml:10
from navigator.widgets.setup.highlight_page import HighlightPage    # settings_dialog.nml:11
from navigator.widgets.setup.interface_page import InterfacePage    # settings_dialog.nml:12
from navigator.widgets.setup.savers_page import SaversPage    # settings_dialog.nml:13
from navigator.widgets.setup.startup_page import StartupPage    # settings_dialog.nml:14
from navigator.widgets.setup.system_setup_page import SystemSetupPage    # settings_dialog.nml:15

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
    widens the box to 80 for that; *Simple*, the default, is a row of bare
    captions over a rule on a page's first row, a row fewer, which it takes
    off the box's height.
    """

    #: The document this class was generated from.
    __navml_source__ = "settings_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    tabs: TabView    # settings_dialog.nml:42
    system: SystemSetupPage    # settings_dialog.nml:66
    startup: StartupPage    # settings_dialog.nml:69
    interface: InterfacePage    # settings_dialog.nml:72
    confirmations: ConfirmationsPage    # settings_dialog.nml:75
    savers: SaversPage    # settings_dialog.nml:78
    country: CountryPage    # settings_dialog.nml:81
    editor_viewer: EditorDefaultsPage    # settings_dialog.nml:84
    file_manager: FMSetupPage    # settings_dialog.nml:87
    drive_info: DriveInfoPage    # settings_dialog.nml:90
    panel_defaults: FMDefaultsPage    # settings_dialog.nml:93
    column_defaults: ColumnDefaultsPage    # settings_dialog.nml:96
    highlight_groups: HighlightPage    # settings_dialog.nml:99
    remote: CommunicationsPage    # settings_dialog.nml:102

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tabs = TabView(parent=self)    # settings_dialog.nml:41
        self.system = SystemSetupPage(parent=self.tabs)    # settings_dialog.nml:65
        self.startup = StartupPage(parent=self.tabs)    # settings_dialog.nml:68
        self.interface = InterfacePage(parent=self.tabs)    # settings_dialog.nml:71
        self.confirmations = ConfirmationsPage(parent=self.tabs)    # settings_dialog.nml:74
        self.savers = SaversPage(parent=self.tabs)    # settings_dialog.nml:77
        self.country = CountryPage(parent=self.tabs)    # settings_dialog.nml:80
        self.editor_viewer = EditorDefaultsPage(parent=self.tabs)    # settings_dialog.nml:83
        self.file_manager = FMSetupPage(parent=self.tabs)    # settings_dialog.nml:86
        self.drive_info = DriveInfoPage(parent=self.tabs)    # settings_dialog.nml:89
        self.panel_defaults = FMDefaultsPage(parent=self.tabs)    # settings_dialog.nml:92
        self.column_defaults = ColumnDefaultsPage(parent=self.tabs)    # settings_dialog.nml:95
        self.highlight_groups = HighlightPage(parent=self.tabs)    # settings_dialog.nml:98
        self.remote = CommunicationsPage(parent=self.tabs)    # settings_dialog.nml:101

        self.modal_width = 76    # settings_dialog.nml:32
        self.modal_height = 24    # settings_dialog.nml:33
        self.title = _bind(lambda _o: _tr('Settings'), yielding=True)    # settings_dialog.nml:34

        self.tabs.tooltips = _bind(    # settings_dialog.nml:44
            lambda _o: [_tr('The internal editor and viewer, the clipboard, temporary files, failures and root access'), _tr('What Navigator does when it starts and when it quits'), _tr('The clock, the menu and key bars, the command line, histories, language and looks'), _tr('Which actions ask before they act'), _tr('Screen savers: which, after how long, and the mouse corners'), _tr('How dates and times are written, and the first day of the week'), _tr("The editor's and the viewer's defaults"), _tr('How the file panels behave and look'), _tr('What the information panel (Ctrl+L) shows'), _tr("How a new file manager's panels start"), _tr('The columns a panel shows on the disk, in a Find: listing and in an archive'), _tr('Which files the panels show in which colour'), _tr('Remote connections: keep-alive, timeouts, idle links and changed files')],
            yielding=True,
        )
        self.tabs.x = _bind(lambda _o: 1 if _o.side == 'left' else 0)    # settings_dialog.nml:59
        self.tabs.y = _bind(lambda _o: 0 if _o.side == 'left' else 1)    # settings_dialog.nml:60
        self.tabs.width = _bind(    # settings_dialog.nml:61
            lambda _o: max(0, _o.parent.width - (2 if _o.side == 'left' else 0))
        )
        self.tabs.height = _bind(    # settings_dialog.nml:62
            lambda _o: max(0, _o.parent.height - (0 if _o.side == 'left' else 5))
        )
        self.tabs.joins_frame = True    # settings_dialog.nml:63

        self.system.title = _bind(lambda _o: _tr('System'), yielding=True)    # settings_dialog.nml:67

        self.startup.title = _bind(lambda _o: _tr('Startup'), yielding=True)    # settings_dialog.nml:70

        self.interface.title = _bind(    # settings_dialog.nml:73
            lambda _o: _tr('Interface'),
            yielding=True,
        )

        self.confirmations.title = _bind(    # settings_dialog.nml:76
            lambda _o: _tr('Confirmations'),
            yielding=True,
        )

        self.savers.title = _bind(lambda _o: _tr('Savers'), yielding=True)    # settings_dialog.nml:79

        self.country.title = _bind(lambda _o: _tr('Country'), yielding=True)    # settings_dialog.nml:82

        self.editor_viewer.title = _bind(    # settings_dialog.nml:85
            lambda _o: _tr('Editor/Viewer'),
            yielding=True,
        )

        self.file_manager.title = _bind(    # settings_dialog.nml:88
            lambda _o: _tr('File panels'),
            yielding=True,
        )

        self.drive_info.title = _bind(    # settings_dialog.nml:91
            lambda _o: _tr('Info panel'),
            yielding=True,
        )

        self.panel_defaults.title = _bind(    # settings_dialog.nml:94
            lambda _o: _tr('Panel defaults'),
            yielding=True,
        )

        self.column_defaults.title = _bind(    # settings_dialog.nml:97
            lambda _o: _tr('Columns'),
            yielding=True,
        )

        self.highlight_groups.title = _bind(    # settings_dialog.nml:100
            lambda _o: _tr('Highlight'),
            yielding=True,
        )

        self.remote.title = _bind(    # settings_dialog.nml:103
            lambda _o: _tr('Communications'),
            yielding=True,
        )
