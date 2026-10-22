# navml: generated
"""Generated from ``game_window.nml``.

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
from navigator.widgets.game.commands import GameSetup, LevelUp, NewGame, PauseGame, ShowTopTen, TogglePreview    # game_window.nml:1
from navigator.widgets.game.game_window.glass import Glass    # game_window.nml:2
from navigator.widgets.game.game_window.info import GameInfo    # game_window.nml:3
from navml.commands import CloseWindow    # game_window.nml:4
from navml.widgets.dialog.button import Button    # game_window.nml:5
from navml.widgets.menu.menu_item import MenuItem    # game_window.nml:6
from navml.widgets.menu.menu_line import MenuLine    # game_window.nml:7
from navml.widgets.menu.sub_menu import SubMenu    # game_window.nml:8
from navml.widgets.window import Window    # game_window.nml:9

__navml_component__ = "GameWindow"

__all__ = ["GameWindow"]


class GameWindow(Window, _Component):
    """≡ > Game: DOS Navigator's ``TGameWindow``, *Navigator's game*.

    A dialog DN put on the desktop as a window, one at a time: the glass down
    the left, *Info* with *Next* and *Best* beside it, and *New*, *Setup*,
    *Top 10* and *Pause* under them, where ``TGameWindow.Init`` put them --
    the glass's frame on the window's bottom edge, as its rectangles put it
    there in DN.  Its keys are ``StatusDef hcTetris``'s.
    """

    #: The document this class was generated from.
    __navml_source__ = "game_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # game_window.nml:23
        'escape': CloseWindow,    # game_window.nml:24
        'f2': NewGame,    # game_window.nml:25
        'f3': PauseGame,    # game_window.nml:26
        'f4': ShowTopTen,    # game_window.nml:27
        'f5': GameSetup,    # game_window.nml:28
        'kp_plus': LevelUp,    # game_window.nml:29
        'kp_multiply': TogglePreview,    # game_window.nml:30
        'alt+n': NewGame,    # game_window.nml:31
        'alt+p': PauseGame,    # game_window.nml:32
        'alt+t': ShowTopTen,    # game_window.nml:33
        'alt+s': GameSetup,    # game_window.nml:34
    }

    #: Ids, annotated so the hand-written half completes them.
    glass: Glass    # game_window.nml:37
    info: GameInfo    # game_window.nml:44
    new_button: Button    # game_window.nml:51
    setup_button: Button    # game_window.nml:59
    top_button: Button    # game_window.nml:67
    pause_button: Button    # game_window.nml:75
    game_menu: SubMenu    # game_window.nml:87

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_new_button_click(self, event: _Event) -> bool:    # game_window.nml:51
        """``new_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_setup_button_click(self, event: _Event) -> bool:    # game_window.nml:59
        """``setup_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_top_button_click(self, event: _Event) -> bool:    # game_window.nml:67
        """``top_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pause_button_click(self, event: _Event) -> bool:    # game_window.nml:75
        """``pause_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.glass = Glass(parent=self)    # game_window.nml:36
        self.info = GameInfo(parent=self)    # game_window.nml:43
        self.new_button = Button(parent=self)    # game_window.nml:50
        self.setup_button = Button(parent=self)    # game_window.nml:58
        self.top_button = Button(parent=self)    # game_window.nml:66
        self.pause_button = Button(parent=self)    # game_window.nml:74
        self.game_menu = SubMenu(parent=self)    # game_window.nml:86
        _w1 = MenuItem(parent=self.game_menu)    # game_window.nml:90
        _w2 = MenuItem(parent=self.game_menu)    # game_window.nml:93
        _w3 = MenuItem(parent=self.game_menu)    # game_window.nml:96
        _w4 = MenuItem(parent=self.game_menu)    # game_window.nml:99
        _w5 = MenuLine(parent=self.game_menu)    # game_window.nml:102
        _w6 = MenuItem(parent=self.game_menu)    # game_window.nml:103
        _w7 = MenuItem(parent=self.game_menu)    # game_window.nml:106
        _w8 = MenuLine(parent=self.game_menu)    # game_window.nml:109
        _w9 = MenuItem(parent=self.game_menu)    # game_window.nml:110

        self.title = _bind(lambda _o: _tr("Navigator's game"), yielding=True)    # game_window.nml:19
        self.zoomable = False    # game_window.nml:20
        self.resizable = False    # game_window.nml:21

        self.glass.x = 1    # game_window.nml:38
        self.glass.y = 1    # game_window.nml:39
        self.glass.width = 26    # game_window.nml:40
        self.glass.height = 21    # game_window.nml:41

        self.info.x = 28    # game_window.nml:45
        self.info.y = 1    # game_window.nml:46
        self.info.width = 23    # game_window.nml:47
        self.info.height = 15    # game_window.nml:48

        self.new_button.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:52
        self.new_button.x = 28    # game_window.nml:53
        self.new_button.y = 17    # game_window.nml:54
        self.new_button.width = 11    # game_window.nml:55
        self.new_button.height = 2    # game_window.nml:56
        self.new_button.on_click = self.on_new_button_click    # game_window.nml:51

        self.setup_button.text = _bind(    # game_window.nml:60
            lambda _o: _tr('~S~etup'),
            yielding=True,
        )
        self.setup_button.x = 39    # game_window.nml:61
        self.setup_button.y = 17    # game_window.nml:62
        self.setup_button.width = 11    # game_window.nml:63
        self.setup_button.height = 2    # game_window.nml:64
        self.setup_button.on_click = self.on_setup_button_click    # game_window.nml:59

        self.top_button.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:68
        self.top_button.x = 28    # game_window.nml:69
        self.top_button.y = 19    # game_window.nml:70
        self.top_button.width = 11    # game_window.nml:71
        self.top_button.height = 2    # game_window.nml:72
        self.top_button.on_click = self.on_top_button_click    # game_window.nml:67

        self.pause_button.text = _bind(    # game_window.nml:76
            lambda _o: _tr('~P~ause'),
            yielding=True,
        )
        self.pause_button.x = 39    # game_window.nml:77
        self.pause_button.y = 19    # game_window.nml:78
        self.pause_button.width = 11    # game_window.nml:79
        self.pause_button.height = 2    # game_window.nml:80
        self.pause_button.on_click = self.on_pause_button_click    # game_window.nml:75

        self.game_menu.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # game_window.nml:88
        self.game_menu.after = 'File'    # game_window.nml:89

        _w1.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:91
        _w1.command = NewGame    # game_window.nml:92

        _w2.text = _bind(lambda _o: _tr('~P~ause'), yielding=True)    # game_window.nml:94
        _w2.command = PauseGame    # game_window.nml:95

        _w3.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:97
        _w3.command = ShowTopTen    # game_window.nml:98

        _w4.text = _bind(lambda _o: _tr('~S~etup'), yielding=True)    # game_window.nml:100
        _w4.command = GameSetup    # game_window.nml:101

        _w6.text = _bind(lambda _o: _tr('~L~evel up'), yielding=True)    # game_window.nml:104
        _w6.command = LevelUp    # game_window.nml:105

        _w7.text = _bind(lambda _o: _tr('Pre~v~iew'), yielding=True)    # game_window.nml:107
        _w7.command = TogglePreview    # game_window.nml:108

        _w9.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # game_window.nml:111
        _w9.command = CloseWindow    # game_window.nml:112
