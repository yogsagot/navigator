# navml: generated
"""Generated from ``tools_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.choice_field import ChoiceField    # tools_page.nml:1
from navml.widgets.dialog.field import Field    # tools_page.nml:2
from navml.widgets.dialog.masked_field import MaskedField    # tools_page.nml:3
from navml.widgets.dialog.static_text import StaticText    # tools_page.nml:4

__navml_component__ = "ToolsPage"

__all__ = ["ToolsPage"]


class ToolsPage(_Component):
    """Options > Settings > *Tools*: Encryption's age identity files, and how

    often the Process list, Services and the System monitor read again.  Not
    DN's -- each is a departure's setting (``[encryption]``, ``[processes]``,
    ``[services]``, ``[monitor]``), given a page so that none is the ini
    file's alone.  A window open reads its new interval at its next tick.
    """

    #: The document this class was generated from.
    __navml_source__ = "tools_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # tools_page.nml:13

    #: Ids, annotated so the hand-written half completes them.
    age_identities: Field    # tools_page.nml:17
    processes_refresh: MaskedField    # tools_page.nml:28
    processes_unit: StaticText    # tools_page.nml:39
    services_manager: ChoiceField    # tools_page.nml:48
    services_refresh: MaskedField    # tools_page.nml:57
    services_unit: StaticText    # tools_page.nml:68
    journal_lines: MaskedField    # tools_page.nml:77
    monitor_refresh: MaskedField    # tools_page.nml:88
    monitor_unit: StaticText    # tools_page.nml:99

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.age_identities = Field(parent=self)    # tools_page.nml:16
        self.processes_refresh = MaskedField(parent=self)    # tools_page.nml:27
        self.processes_unit = StaticText(parent=self)    # tools_page.nml:38
        self.services_manager = ChoiceField(parent=self)    # tools_page.nml:47
        self.services_refresh = MaskedField(parent=self)    # tools_page.nml:56
        self.services_unit = StaticText(parent=self)    # tools_page.nml:67
        self.journal_lines = MaskedField(parent=self)    # tools_page.nml:76
        self.monitor_refresh = MaskedField(parent=self)    # tools_page.nml:87
        self.monitor_unit = StaticText(parent=self)    # tools_page.nml:98

        self.age_identities.y = 1    # tools_page.nml:18
        self.age_identities.height = 1    # tools_page.nml:19
        self.age_identities.label_text = _bind(    # tools_page.nml:23
            lambda _o: _tr('~A~ge identity files'),
            yielding=True,
        )
        self.age_identities.label_width = 30    # tools_page.nml:24
        self.age_identities.history_id = 'age_identities'    # tools_page.nml:25
        self.age_identities.x = 2    # tools_page.nml:21
        self.age_identities.width = _bind(    # tools_page.nml:22
            lambda _o: max(0, _o.parent.width - 4)
        )

        self.processes_refresh.x = 2    # tools_page.nml:29
        self.processes_refresh.y = 3    # tools_page.nml:30
        self.processes_refresh.width = 34    # tools_page.nml:31
        self.processes_refresh.height = 1    # tools_page.nml:32
        self.processes_refresh.label_text = _bind(    # tools_page.nml:33
            lambda _o: _tr('~P~rocess list reads every'),
            yielding=True,
        )
        self.processes_refresh.label_width = 30    # tools_page.nml:34
        self.processes_refresh.mask = '99'    # tools_page.nml:35
        self.processes_refresh.page_keys = False    # tools_page.nml:36

        self.processes_unit.y = 3    # tools_page.nml:40
        self.processes_unit.height = 1    # tools_page.nml:41
        self.processes_unit.text = _bind(    # tools_page.nml:45
            lambda _o: _tr('seconds (0: on Ctrl+R alone)'),
            yielding=True,
        )
        self.processes_unit.x = 37    # tools_page.nml:43
        self.processes_unit.width = _bind(    # tools_page.nml:44
            lambda _o: max(0, _o.parent.width - 39)
        )

        self.services_manager.x = 2    # tools_page.nml:49
        self.services_manager.y = 5    # tools_page.nml:50
        self.services_manager.width = 50    # tools_page.nml:51
        self.services_manager.height = 1    # tools_page.nml:52
        self.services_manager.label_text = _bind(    # tools_page.nml:53
            lambda _o: _tr('Service ~m~anager'),
            yielding=True,
        )
        self.services_manager.label_width = 30    # tools_page.nml:54

        self.services_refresh.x = 2    # tools_page.nml:58
        self.services_refresh.y = 6    # tools_page.nml:59
        self.services_refresh.width = 34    # tools_page.nml:60
        self.services_refresh.height = 1    # tools_page.nml:61
        self.services_refresh.label_text = _bind(    # tools_page.nml:62
            lambda _o: _tr('S~e~rvices read every'),
            yielding=True,
        )
        self.services_refresh.label_width = 30    # tools_page.nml:63
        self.services_refresh.mask = '99'    # tools_page.nml:64
        self.services_refresh.page_keys = False    # tools_page.nml:65

        self.services_unit.y = 6    # tools_page.nml:69
        self.services_unit.height = 1    # tools_page.nml:70
        self.services_unit.text = _bind(    # tools_page.nml:74
            lambda _o: _tr('seconds (0: on Ctrl+R alone)'),
            yielding=True,
        )
        self.services_unit.x = 37    # tools_page.nml:72
        self.services_unit.width = _bind(    # tools_page.nml:73
            lambda _o: max(0, _o.parent.width - 39)
        )

        self.journal_lines.x = 2    # tools_page.nml:78
        self.journal_lines.y = 7    # tools_page.nml:79
        self.journal_lines.width = 36    # tools_page.nml:80
        self.journal_lines.height = 1    # tools_page.nml:81
        self.journal_lines.label_text = _bind(    # tools_page.nml:82
            lambda _o: _tr('~J~ournal lines F3 shows first'),
            yielding=True,
        )
        self.journal_lines.label_width = 30    # tools_page.nml:83
        self.journal_lines.mask = '9999'    # tools_page.nml:84
        self.journal_lines.page_keys = False    # tools_page.nml:85

        self.monitor_refresh.x = 2    # tools_page.nml:89
        self.monitor_refresh.y = 9    # tools_page.nml:90
        self.monitor_refresh.width = 34    # tools_page.nml:91
        self.monitor_refresh.height = 1    # tools_page.nml:92
        self.monitor_refresh.label_text = _bind(    # tools_page.nml:93
            lambda _o: _tr('S~y~stem monitor reads every'),
            yielding=True,
        )
        self.monitor_refresh.label_width = 30    # tools_page.nml:94
        self.monitor_refresh.mask = '99'    # tools_page.nml:95
        self.monitor_refresh.page_keys = False    # tools_page.nml:96

        self.monitor_unit.y = 9    # tools_page.nml:100
        self.monitor_unit.height = 1    # tools_page.nml:101
        self.monitor_unit.text = _bind(    # tools_page.nml:105
            lambda _o: _tr('seconds (0: on Ctrl+R alone)'),
            yielding=True,
        )
        self.monitor_unit.x = 37    # tools_page.nml:103
        self.monitor_unit.width = _bind(    # tools_page.nml:104
            lambda _o: max(0, _o.parent.width - 39)
        )
