# navml: generated
"""Generated from ``game_setup_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # game_setup_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # game_setup_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # game_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # game_setup_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # game_setup_dialog.nml:5

__navml_component__ = "GameSetupDialog"

__all__ = ["GameSetupDialog"]


class GameSetupDialog(Dialog, _Component):
    """DOS Navigator's ``dlgGameSetup``: the ten levels down the left, the game

    style and the preview on the right, OK and Cancel under them -- the
    resource's places, its 53 by 15.
    """

    #: The document this class was generated from.
    __navml_source__ = "game_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    level_caption: Label    # game_setup_dialog.nml:16
    level: RadioButtons    # game_setup_dialog.nml:25
    style_caption: Label    # game_setup_dialog.nml:33
    game_style: RadioButtons    # game_setup_dialog.nml:42
    options_caption: Label    # game_setup_dialog.nml:50
    options: CheckBoxes    # game_setup_dialog.nml:59
    pick: Button    # game_setup_dialog.nml:67
    abandon: Button    # game_setup_dialog.nml:76

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # game_setup_dialog.nml:67
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # game_setup_dialog.nml:76
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.level_caption = Label(parent=self)    # game_setup_dialog.nml:15
        self.level = RadioButtons(parent=self)    # game_setup_dialog.nml:24
        self.style_caption = Label(parent=self)    # game_setup_dialog.nml:32
        self.game_style = RadioButtons(parent=self)    # game_setup_dialog.nml:41
        self.options_caption = Label(parent=self)    # game_setup_dialog.nml:49
        self.options = CheckBoxes(parent=self)    # game_setup_dialog.nml:58
        self.pick = Button(parent=self)    # game_setup_dialog.nml:66
        self.abandon = Button(parent=self)    # game_setup_dialog.nml:75

        self.modal_width = 53    # game_setup_dialog.nml:11
        self.modal_height = 15    # game_setup_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Setup game'), yielding=True)    # game_setup_dialog.nml:13

        self.level_caption.x = 3    # game_setup_dialog.nml:17
        self.level_caption.y = 2    # game_setup_dialog.nml:18
        self.level_caption.width = 8    # game_setup_dialog.nml:19
        self.level_caption.height = 1    # game_setup_dialog.nml:20
        self.level_caption.text = _bind(lambda _o: _tr('Level'), yielding=True)    # game_setup_dialog.nml:21
        self.level_caption.link = _bind(lambda _o: self.level)    # game_setup_dialog.nml:22

        self.level.x = 3    # game_setup_dialog.nml:26
        self.level.y = 3    # game_setup_dialog.nml:27
        self.level.width = 25    # game_setup_dialog.nml:28
        self.level.height = 10    # game_setup_dialog.nml:29
        self.level.items = _bind(    # game_setup_dialog.nml:30
            lambda _o: [_tr('~1~ - Baby'), _tr('~2~ - Little fella'), _tr('~3~ - Big child'), _tr("~4~ - It's easy"), _tr('~5~ - Never mind'), _tr("~6~ - I'm powerful !"), _tr('~7~ - Insanity coming'), _tr('~8~ - So what ?..'), _tr('~9~ - Madness'), _tr('1~0~ - Sanitarium')],
            yielding=True,
        )

        self.style_caption.x = 30    # game_setup_dialog.nml:34
        self.style_caption.y = 2    # game_setup_dialog.nml:35
        self.style_caption.width = 12    # game_setup_dialog.nml:36
        self.style_caption.height = 1    # game_setup_dialog.nml:37
        self.style_caption.text = _bind(    # game_setup_dialog.nml:38
            lambda _o: _tr('~G~ame style'),
            yielding=True,
        )
        self.style_caption.link = _bind(lambda _o: self.game_style)    # game_setup_dialog.nml:39

        self.game_style.x = 30    # game_setup_dialog.nml:43
        self.game_style.y = 3    # game_setup_dialog.nml:44
        self.game_style.width = 20    # game_setup_dialog.nml:45
        self.game_style.height = 2    # game_setup_dialog.nml:46
        self.game_style.items = _bind(    # game_setup_dialog.nml:47
            lambda _o: [_tr('Classic ~t~etris'), _tr('Penti~x~')],
            yielding=True,
        )

        self.options_caption.x = 30    # game_setup_dialog.nml:51
        self.options_caption.y = 6    # game_setup_dialog.nml:52
        self.options_caption.width = 10    # game_setup_dialog.nml:53
        self.options_caption.height = 1    # game_setup_dialog.nml:54
        self.options_caption.text = _bind(    # game_setup_dialog.nml:55
            lambda _o: _tr('~O~ptions'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # game_setup_dialog.nml:56

        self.options.x = 30    # game_setup_dialog.nml:60
        self.options.y = 7    # game_setup_dialog.nml:61
        self.options.width = 19    # game_setup_dialog.nml:62
        self.options.height = 1    # game_setup_dialog.nml:63
        self.options.items = _bind(    # game_setup_dialog.nml:64
            lambda _o: [_tr('~P~iece preview')],
            yielding=True,
        )

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # game_setup_dialog.nml:68
        self.pick.default = True    # game_setup_dialog.nml:69
        self.pick.x = 40    # game_setup_dialog.nml:70
        self.pick.y = 9    # game_setup_dialog.nml:71
        self.pick.width = 11    # game_setup_dialog.nml:72
        self.pick.height = 2    # game_setup_dialog.nml:73
        self.pick.on_click = self.on_pick_click    # game_setup_dialog.nml:67

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # game_setup_dialog.nml:77
        self.abandon.x = 40    # game_setup_dialog.nml:78
        self.abandon.y = 11    # game_setup_dialog.nml:79
        self.abandon.width = 11    # game_setup_dialog.nml:80
        self.abandon.height = 2    # game_setup_dialog.nml:81
        self.abandon.on_click = self.on_abandon_click    # game_setup_dialog.nml:76
