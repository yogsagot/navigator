# navml: generated
"""Generated from ``startup_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # startup_page.nml:1
from navml.widgets.dialog.label import Label    # startup_page.nml:2

__navml_component__ = "StartupPage"

__all__ = ["StartupPage"]


class StartupPage(_Component):
    """Options > Configuration > Startup: DOS Navigator's ``dlgStartupSetup``.

    The resource's groups, less what only meant something on DOS --
    *Restore screen mode*, the two overlay boxes, *Force* and *Restore VGA
    palette*, *Enable blinking* (VGA attribute bit 7), and the whole
    *Timeslicing* group (*Sleep when inactive*, *DOS Idle (Int28)*): an event
    loop already sleeps while nothing happens.
    """

    #: The document this class was generated from.
    __navml_source__ = "startup_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # startup_page.nml:13

    #: Ids, annotated so the hand-written half completes them.
    startup_caption: Label    # startup_page.nml:16
    startup: CheckBoxes    # startup_page.nml:25
    shutdown_caption: Label    # startup_page.nml:33
    shutdown: CheckBoxes    # startup_page.nml:42

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.startup_caption = Label(parent=self)    # startup_page.nml:15
        self.startup = CheckBoxes(parent=self)    # startup_page.nml:24
        self.shutdown_caption = Label(parent=self)    # startup_page.nml:32
        self.shutdown = CheckBoxes(parent=self)    # startup_page.nml:41

        self.startup_caption.x = 2    # startup_page.nml:17
        self.startup_caption.y = 1    # startup_page.nml:18
        self.startup_caption.width = 20    # startup_page.nml:19
        self.startup_caption.height = 1    # startup_page.nml:20
        self.startup_caption.text = _bind(    # startup_page.nml:21
            lambda _o: _tr('Startup options'),
            yielding=True,
        )
        self.startup_caption.link = _bind(lambda _o: self.startup)    # startup_page.nml:22

        self.startup.x = 2    # startup_page.nml:26
        self.startup.y = 2    # startup_page.nml:27
        self.startup.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_page.nml:28
        self.startup.height = 1    # startup_page.nml:29
        self.startup.items = _bind(    # startup_page.nml:30
            lambda _o: [_tr('Auto run ~U~ser Menu'), _tr('Clear ~H~istory')],
            yielding=True,
        )

        self.shutdown_caption.x = 2    # startup_page.nml:34
        self.shutdown_caption.y = 4    # startup_page.nml:35
        self.shutdown_caption.width = 20    # startup_page.nml:36
        self.shutdown_caption.height = 1    # startup_page.nml:37
        self.shutdown_caption.text = _bind(    # startup_page.nml:38
            lambda _o: _tr('Shutdown options'),
            yielding=True,
        )
        self.shutdown_caption.link = _bind(lambda _o: self.shutdown)    # startup_page.nml:39

        self.shutdown.x = 2    # startup_page.nml:43
        self.shutdown.y = 5    # startup_page.nml:44
        self.shutdown.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_page.nml:45
        self.shutdown.height = 2    # startup_page.nml:46
        self.shutdown.items = _bind(    # startup_page.nml:47
            lambda _o: [_tr('~I~nactivity hour exit'), _tr('Autosave ~D~esktop'), _tr('~P~reserve directory')],
            yielding=True,
        )
