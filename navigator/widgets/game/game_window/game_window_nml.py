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
from navigator.lib.utilities.tetris import TICK    # game_window.nml:11
from navml.widgets.timer import Timer    # game_window.nml:12

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
    keys = {    # game_window.nml:26
        'escape': CloseWindow,    # game_window.nml:27
        'f2': NewGame,    # game_window.nml:28
        'f3': PauseGame,    # game_window.nml:29
        'f4': ShowTopTen,    # game_window.nml:30
        'f5': GameSetup,    # game_window.nml:31
        'kp_plus': LevelUp,    # game_window.nml:32
        'kp_multiply': TogglePreview,    # game_window.nml:33
        'alt+n': NewGame,    # game_window.nml:34
        'alt+p': PauseGame,    # game_window.nml:35
        'alt+t': ShowTopTen,    # game_window.nml:36
        'alt+s': GameSetup,    # game_window.nml:37
    }

    #: Ids, annotated so the hand-written half completes them.
    glass: Glass    # game_window.nml:47
    info: GameInfo    # game_window.nml:54
    new_button: Button    # game_window.nml:69
    setup_button: Button    # game_window.nml:74
    top_button: Button    # game_window.nml:87
    pause_button: Button    # game_window.nml:92
    game_menu: SubMenu    # game_window.nml:101
    clock: Timer    # game_window.nml:117

    #: The commands this component handles itself.
    async def on_show_top_ten(self, event: _Any) -> bool:    # game_window.nml:41
        """``ShowTopTen``."""
        self.spawn(self.show_scores())
        return True

    async def on_game_setup(self, event: _Any) -> bool:    # game_window.nml:42
        """``GameSetup``."""
        self.spawn(self.setup())
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_new_button_click(self, event: _Event) -> bool:    # game_window.nml:69
        """``new_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_setup_button_click(self, event: _Event) -> bool:    # game_window.nml:74
        """``setup_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_top_button_click(self, event: _Event) -> bool:    # game_window.nml:87
        """``top_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pause_button_click(self, event: _Event) -> bool:    # game_window.nml:92
        """``pause_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.glass = Glass(parent=self)    # game_window.nml:46
        self.info = GameInfo(parent=self)    # game_window.nml:53
        _w1 = ButtonRow(parent=self)    # game_window.nml:60
        self.new_button = Button(parent=_w1)    # game_window.nml:68
        self.setup_button = Button(parent=_w1)    # game_window.nml:73
        _w2 = ButtonRow(parent=self)    # game_window.nml:78
        self.top_button = Button(parent=_w2)    # game_window.nml:86
        self.pause_button = Button(parent=_w2)    # game_window.nml:91
        self.game_menu = SubMenu(parent=self)    # game_window.nml:100
        _w3 = MenuItem(parent=self.game_menu)    # game_window.nml:103
        _w4 = MenuItem(parent=self.game_menu)    # game_window.nml:104
        _w5 = MenuItem(parent=self.game_menu)    # game_window.nml:105
        _w6 = MenuItem(parent=self.game_menu)    # game_window.nml:106
        _w7 = MenuLine(parent=self.game_menu)    # game_window.nml:107
        _w8 = MenuItem(parent=self.game_menu)    # game_window.nml:108
        _w9 = MenuItem(parent=self.game_menu)    # game_window.nml:110
        _w10 = MenuLine(parent=self.game_menu)    # game_window.nml:112
        _w11 = MenuItem(parent=self.game_menu)    # game_window.nml:113
        self.clock = Timer(parent=self)    # game_window.nml:116

        self.title = _bind(lambda _o: _tr("Navigator's game"), yielding=True)    # game_window.nml:22
        self.zoomable = False    # game_window.nml:23
        self.resizable = False    # game_window.nml:24
        self.local_menu = _bind(lambda _o: self.game_menu)    # game_window.nml:44

        self.glass.x = 1    # game_window.nml:48
        self.glass.y = 1    # game_window.nml:49
        self.glass.width = 26    # game_window.nml:50
        self.glass.height = 21    # game_window.nml:51

        self.info.x = 28    # game_window.nml:55
        self.info.y = 1    # game_window.nml:56
        self.info.width = 23    # game_window.nml:57
        self.info.height = 15    # game_window.nml:58

        _w1.justify = 'start'    # game_window.nml:61
        _w1.spacing = 0    # game_window.nml:62
        _w1.y = 17# game_window.nml:63
        _w1.x = 28# game_window.nml:65
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # game_window.nml:66

        self.new_button.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:70
        self.new_button.command = NewGame    # game_window.nml:71
        self.new_button.on_click = self.on_new_button_click    # game_window.nml:69

        self.setup_button.text = _bind(    # game_window.nml:75
            lambda _o: _tr('~S~etup'),
            yielding=True,
        )
        self.setup_button.command = GameSetup    # game_window.nml:76
        self.setup_button.on_click = self.on_setup_button_click    # game_window.nml:74

        _w2.justify = 'start'    # game_window.nml:79
        _w2.spacing = 0    # game_window.nml:80
        _w2.y = 19# game_window.nml:81
        _w2.x = 28# game_window.nml:83
        _w2.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # game_window.nml:84

        self.top_button.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:88
        self.top_button.command = ShowTopTen    # game_window.nml:89
        self.top_button.on_click = self.on_top_button_click    # game_window.nml:87

        self.pause_button.text = _bind(    # game_window.nml:93
            lambda _o: _tr('~P~ause'),
            yielding=True,
        )
        self.pause_button.command = PauseGame    # game_window.nml:94
        self.pause_button.on_click = self.on_pause_button_click    # game_window.nml:92

        self.game_menu.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # game_window.nml:100
        self.game_menu.after = 'File'    # game_window.nml:100
        self.game_menu.tooltip = _bind(    # game_window.nml:102
            lambda _o: _tr('A new game, pause, the Top Ten and setup'),
            yielding=True,
        )

        _w3.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # game_window.nml:103
        _w3.command = NewGame    # game_window.nml:103

        _w4.text = _bind(lambda _o: _tr('~P~ause'), yielding=True)    # game_window.nml:104
        _w4.command = PauseGame    # game_window.nml:104

        _w5.text = _bind(lambda _o: _tr('~T~op 10'), yielding=True)    # game_window.nml:105
        _w5.command = ShowTopTen    # game_window.nml:105

        _w6.text = _bind(lambda _o: _tr('~S~etup'), yielding=True)    # game_window.nml:106
        _w6.command = GameSetup    # game_window.nml:106

        _w8.text = _bind(lambda _o: _tr('~L~evel up'), yielding=True)    # game_window.nml:108
        _w8.command = LevelUp    # game_window.nml:108
        _w8.tooltip = _bind(    # game_window.nml:109
            lambda _o: _tr('Play at the next level, faster'),
            yielding=True,
        )

        _w9.text = _bind(lambda _o: _tr('Pre~v~iew'), yielding=True)    # game_window.nml:110
        _w9.command = TogglePreview    # game_window.nml:110
        _w9.tooltip = _bind(    # game_window.nml:111
            lambda _o: _tr('Show the next figure'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # game_window.nml:113
        _w11.command = CloseWindow    # game_window.nml:113

        self.clock.interval = round(TICK * 1000)    # game_window.nml:118

        async def _on_timer(event):    # game_window.nml:119
            await self._tick()
            return True
        self.clock.on_timer = _on_timer

        self._navml_built(__class__)
