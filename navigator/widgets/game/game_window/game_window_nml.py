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
from navml.widgets.dialog.button_row import ButtonRow    # game_window.nml:6
from navml.widgets.menu.menu_item import MenuItem    # game_window.nml:7
from navml.widgets.menu.menu_line import MenuLine    # game_window.nml:8
from navml.widgets.menu.sub_menu import SubMenu    # game_window.nml:9
from navml.widgets.window import Window    # game_window.nml:10

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
    keys = {    # game_window.nml:24
        'escape': CloseWindow,    # game_window.nml:25
        'f2': NewGame,    # game_window.nml:26
        'f3': PauseGame,    # game_window.nml:27
        'f4': ShowTopTen,    # game_window.nml:28
        'f5': GameSetup,    # game_window.nml:29
        'kp_plus': LevelUp,    # game_window.nml:30
        'kp_multiply': TogglePreview,    # game_window.nml:31
        'alt+n': NewGame,    # game_window.nml:32
        'alt+p': PauseGame,    # game_window.nml:33
        'alt+t': ShowTopTen,    # game_window.nml:34
        'alt+s': GameSetup,    # game_window.nml:35
    }

    #: Ids, annotated so the hand-written half completes them.
    glass: Glass    # game_window.nml:38
    info: GameInfo    # game_window.nml:45
    new_button: Button    # game_window.nml:60
    setup_button: Button    # game_window.nml:65
    top_button: Button    # game_window.nml:78
    pause_button: Button    # game_window.nml:83
    game_menu: SubMenu    # game_window.nml:92

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_new_button_click(self, event: _Event) -> bool:    # game_window.nml:60
        """``new_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_setup_button_click(self, event: _Event) -> bool:    # game_window.nml:65
        """``setup_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_top_button_click(self, event: _Event) -> bool:    # game_window.nml:78
        """``top_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pause_button_click(self, event: _Event) -> bool:    # game_window.nml:83
        """``pause_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.glass = Glass(parent=self)    # game_window.nml:37
        self.info = GameInfo(parent=self)    # game_window.nml:44
        _w1 = ButtonRow(parent=self)    # game_window.nml:51
        self.new_button = Button(parent=_w1)    # game_window.nml:59
        self.setup_button = Button(parent=_w1)    # game_window.nml:64
        _w2 = ButtonRow(parent=self)    # game_window.nml:69
        self.top_button = Button(parent=_w2)    # game_window.nml:77
        self.pause_button = Button(parent=_w2)    # game_window.nml:82
        self.game_menu = SubMenu(parent=self)    # game_window.nml:91
        _w3 = MenuItem(parent=self.game_menu)    # game_window.nml:94
        _w4 = MenuItem(parent=self.game_menu)    # game_window.nml:95
        _w5 = MenuItem(parent=self.game_menu)    # game_window.nml:96
        _w6 = MenuItem(parent=self.game_menu)    # game_window.nml:97
        _w7 = MenuLine(parent=self.game_menu)    # game_window.nml:98
        _w8 = MenuItem(parent=self.game_menu)    # game_window.nml:99
        _w9 = MenuItem(parent=self.game_menu)    # game_window.nml:101
        _w10 = MenuLine(parent=self.game_menu)    # game_window.nml:103
        _w11 = MenuItem(parent=self.game_menu)    # game_window.nml:104

        self.title = _bind(lambda _o: _tr("Navigator's game"), yielding=True)    # game_window.nml:20
        self.zoomable = False    # game_window.nml:21
        self.resizable = False    # game_window.nml:22

        self.glass.x = 1    # game_window.nml:39
        self.glass.y = 1    # game_window.nml:40
        self.glass.width = 26    # game_window.nml:41
        self.glass.height = 21    # game_window.nml:42

        self.info.x = 28    # game_window.nml:46
        self.info.y = 1    # game_window.nml:47
        self.info.width = 23    # game_window.nml:48
        self.info.height = 15    # game_window.nml:49

        _w1.justify = 'start'    # game_window.nml:52
        _w1.spacing = 0    # game_window.nml:53
        _w1.y = 17# game_window.nml:54
        _w1.x = 28# game_window.nml:56
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # game_window.nml:57

        self.new_button.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:61
        self.new_button.command = NewGame    # game_window.nml:62
        self.new_button.on_click = self.on_new_button_click    # game_window.nml:60

        self.setup_button.text = _bind(    # game_window.nml:66
            lambda _o: _tr('~S~etup'),
            yielding=True,
        )
        self.setup_button.command = GameSetup    # game_window.nml:67
        self.setup_button.on_click = self.on_setup_button_click    # game_window.nml:65

        _w2.justify = 'start'    # game_window.nml:70
        _w2.spacing = 0    # game_window.nml:71
        _w2.y = 19# game_window.nml:72
        _w2.x = 28# game_window.nml:74
        _w2.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # game_window.nml:75

        self.top_button.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:79
        self.top_button.command = ShowTopTen    # game_window.nml:80
        self.top_button.on_click = self.on_top_button_click    # game_window.nml:78

        self.pause_button.text = _bind(    # game_window.nml:84
            lambda _o: _tr('~P~ause'),
            yielding=True,
        )
        self.pause_button.command = PauseGame    # game_window.nml:85
        self.pause_button.on_click = self.on_pause_button_click    # game_window.nml:83

        self.game_menu.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # game_window.nml:91
        self.game_menu.after = 'File'    # game_window.nml:91
        self.game_menu.tooltip = _bind(    # game_window.nml:93
            lambda _o: _tr('A new game, pause, the Top Ten and setup'),
            yielding=True,
        )

        _w3.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:94
        _w3.command = NewGame    # game_window.nml:94

        _w4.text = _bind(lambda _o: _tr('~P~ause'), yielding=True)    # game_window.nml:95
        _w4.command = PauseGame    # game_window.nml:95

        _w5.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:96
        _w5.command = ShowTopTen    # game_window.nml:96

        _w6.text = _bind(lambda _o: _tr('~S~etup'), yielding=True)    # game_window.nml:97
        _w6.command = GameSetup    # game_window.nml:97

        _w8.text = _bind(lambda _o: _tr('~L~evel up'), yielding=True)    # game_window.nml:99
        _w8.command = LevelUp    # game_window.nml:99
        _w8.tooltip = _bind(    # game_window.nml:100
            lambda _o: _tr('Play at the next level, faster'),
            yielding=True,
        )

        _w9.text = _bind(lambda _o: _tr('Pre~v~iew'), yielding=True)    # game_window.nml:101
        _w9.command = TogglePreview    # game_window.nml:101
        _w9.tooltip = _bind(    # game_window.nml:102
            lambda _o: _tr('Show the next figure'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # game_window.nml:104
        _w11.command = CloseWindow    # game_window.nml:104
