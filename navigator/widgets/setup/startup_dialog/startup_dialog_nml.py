# navml: generated
"""Generated from ``startup_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # startup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # startup_dialog.nml:2
from navml.widgets.dialog.label import Label    # startup_dialog.nml:3

__navml_component__ = "StartupDialog"

__all__ = ["StartupDialog"]


class StartupDialog(Dialog, _Component):
    """Options > Configuration > Startup: DOS Navigator's ``dlgStartupSetup``.

    The resource's groups, less what only meant something on DOS --
    *Restore screen mode*, the two overlay boxes, *Force* and *Restore VGA
    palette*, *Enable blinking* (VGA attribute bit 7), and the whole
    *Timeslicing* group (*Sleep when inactive*, *DOS Idle (Int28)*): an event
    loop already sleeps while nothing happens.
    """

    #: The document this class was generated from.
    __navml_source__ = "startup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    startup_caption: Label    # startup_dialog.nml:18
    startup: CheckBoxes    # startup_dialog.nml:27
    shutdown_caption: Label    # startup_dialog.nml:35
    shutdown: CheckBoxes    # startup_dialog.nml:44

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.startup_caption = Label(parent=self)    # startup_dialog.nml:17
        self.startup = CheckBoxes(parent=self)    # startup_dialog.nml:26
        self.shutdown_caption = Label(parent=self)    # startup_dialog.nml:34
        self.shutdown = CheckBoxes(parent=self)    # startup_dialog.nml:43

        self.modal_width = 60    # startup_dialog.nml:13
        self.modal_height = 12    # startup_dialog.nml:14
        self.title = 'Startup'    # startup_dialog.nml:15

        self.startup_caption.x = 2    # startup_dialog.nml:19
        self.startup_caption.y = 1    # startup_dialog.nml:20
        self.startup_caption.width = 20    # startup_dialog.nml:21
        self.startup_caption.height = 1    # startup_dialog.nml:22
        self.startup_caption.text = 'Startup options'    # startup_dialog.nml:23
        self.startup_caption.link = _bind(lambda _o: self.startup)    # startup_dialog.nml:24

        self.startup.x = 2    # startup_dialog.nml:28
        self.startup.y = 2    # startup_dialog.nml:29
        self.startup.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_dialog.nml:30
        self.startup.height = 1    # startup_dialog.nml:31
        self.startup.items = ['Auto run ~U~ser Menu', 'Clear ~H~istory']    # startup_dialog.nml:32

        self.shutdown_caption.x = 2    # startup_dialog.nml:36
        self.shutdown_caption.y = 4    # startup_dialog.nml:37
        self.shutdown_caption.width = 20    # startup_dialog.nml:38
        self.shutdown_caption.height = 1    # startup_dialog.nml:39
        self.shutdown_caption.text = 'Shutdown options'    # startup_dialog.nml:40
        self.shutdown_caption.link = _bind(lambda _o: self.shutdown)    # startup_dialog.nml:41

        self.shutdown.x = 2    # startup_dialog.nml:45
        self.shutdown.y = 5    # startup_dialog.nml:46
        self.shutdown.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_dialog.nml:47
        self.shutdown.height = 2    # startup_dialog.nml:48
        self.shutdown.items = ['~I~nactivity hour exit', 'Autosave ~D~esktop', '~P~reserve directory']    # startup_dialog.nml:49
