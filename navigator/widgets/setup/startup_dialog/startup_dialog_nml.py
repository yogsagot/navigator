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

    The resource's three groups, less what only meant something on DOS --
    *Restore screen mode*, the two overlay boxes, *Force* and *Restore VGA
    palette*, *DOS Idle (Int28)* and the overlay buffer's size.
    """

    #: The document this class was generated from.
    __navml_source__ = "startup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    startup_caption: Label    # startup_dialog.nml:16
    startup: CheckBoxes    # startup_dialog.nml:25
    shutdown_caption: Label    # startup_dialog.nml:33
    shutdown: CheckBoxes    # startup_dialog.nml:42
    timeslicing_caption: Label    # startup_dialog.nml:50
    timeslicing: CheckBoxes    # startup_dialog.nml:59

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.startup_caption = Label(parent=self)    # startup_dialog.nml:15
        self.startup = CheckBoxes(parent=self)    # startup_dialog.nml:24
        self.shutdown_caption = Label(parent=self)    # startup_dialog.nml:32
        self.shutdown = CheckBoxes(parent=self)    # startup_dialog.nml:41
        self.timeslicing_caption = Label(parent=self)    # startup_dialog.nml:49
        self.timeslicing = CheckBoxes(parent=self)    # startup_dialog.nml:58

        self.modal_width = 60    # startup_dialog.nml:11
        self.modal_height = 15    # startup_dialog.nml:12
        self.title = 'Startup'    # startup_dialog.nml:13

        self.startup_caption.x = 2    # startup_dialog.nml:17
        self.startup_caption.y = 1    # startup_dialog.nml:18
        self.startup_caption.width = 20    # startup_dialog.nml:19
        self.startup_caption.height = 1    # startup_dialog.nml:20
        self.startup_caption.text = 'Startup options'    # startup_dialog.nml:21
        self.startup_caption.link = _bind(lambda _o: self.startup)    # startup_dialog.nml:22

        self.startup.x = 2    # startup_dialog.nml:26
        self.startup.y = 2    # startup_dialog.nml:27
        self.startup.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_dialog.nml:28
        self.startup.height = 1    # startup_dialog.nml:29
        self.startup.items = ['Auto run ~U~ser Menu', 'Clear ~H~istory']    # startup_dialog.nml:30

        self.shutdown_caption.x = 2    # startup_dialog.nml:34
        self.shutdown_caption.y = 4    # startup_dialog.nml:35
        self.shutdown_caption.width = 20    # startup_dialog.nml:36
        self.shutdown_caption.height = 1    # startup_dialog.nml:37
        self.shutdown_caption.text = 'Shutdown options'    # startup_dialog.nml:38
        self.shutdown_caption.link = _bind(lambda _o: self.shutdown)    # startup_dialog.nml:39

        self.shutdown.x = 2    # startup_dialog.nml:43
        self.shutdown.y = 5    # startup_dialog.nml:44
        self.shutdown.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_dialog.nml:45
        self.shutdown.height = 2    # startup_dialog.nml:46
        self.shutdown.items = ['~I~nactivity hour exit', 'Autosave ~D~esktop', 'Enable ~b~linking', '~P~reserve directory']    # startup_dialog.nml:47

        self.timeslicing_caption.x = 2    # startup_dialog.nml:51
        self.timeslicing_caption.y = 8    # startup_dialog.nml:52
        self.timeslicing_caption.width = 20    # startup_dialog.nml:53
        self.timeslicing_caption.height = 1    # startup_dialog.nml:54
        self.timeslicing_caption.text = 'Timeslicing options'    # startup_dialog.nml:55
        self.timeslicing_caption.link = _bind(lambda _o: self.timeslicing)    # startup_dialog.nml:56

        self.timeslicing.x = 2    # startup_dialog.nml:60
        self.timeslicing.y = 9    # startup_dialog.nml:61
        self.timeslicing.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # startup_dialog.nml:62
        self.timeslicing.height = 1    # startup_dialog.nml:63
        self.timeslicing.items = ['~S~leep when inactive']    # startup_dialog.nml:64
