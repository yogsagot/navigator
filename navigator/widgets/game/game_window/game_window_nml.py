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

from navml.component import Component as _Component
from navigator.widgets.game.commands import GameSetup, LevelUp, NewGame, PauseGame, ShowTopTen, TogglePreview    # game_window.nml:1
from navigator.widgets.game.game_window.glass import Glass    # game_window.nml:2
from navigator.widgets.game.game_window.info import GameInfo    # game_window.nml:3
from navml.commands import CloseWindow    # game_window.nml:4
from navml.widgets.dialog.button import Button    # game_window.nml:5
from navml.widgets.window import Window    # game_window.nml:6

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
    keys = {    # game_window.nml:20
        'escape': CloseWindow,    # game_window.nml:21
        'f2': NewGame,    # game_window.nml:22
        'f3': PauseGame,    # game_window.nml:23
        'f4': ShowTopTen,    # game_window.nml:24
        'f5': GameSetup,    # game_window.nml:25
        'kp_plus': LevelUp,    # game_window.nml:26
        'kp_multiply': TogglePreview,    # game_window.nml:27
        'alt+n': NewGame,    # game_window.nml:28
        'alt+p': PauseGame,    # game_window.nml:29
        'alt+t': ShowTopTen,    # game_window.nml:30
        'alt+s': GameSetup,    # game_window.nml:31
    }

    #: Ids, annotated so the hand-written half completes them.
    glass: Glass    # game_window.nml:34
    info: GameInfo    # game_window.nml:41
    new_button: Button    # game_window.nml:48
    setup_button: Button    # game_window.nml:56
    top_button: Button    # game_window.nml:64
    pause_button: Button    # game_window.nml:72

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_new_button_click(self, event: _Event) -> bool:    # game_window.nml:48
        """``new_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_setup_button_click(self, event: _Event) -> bool:    # game_window.nml:56
        """``setup_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_top_button_click(self, event: _Event) -> bool:    # game_window.nml:64
        """``top_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pause_button_click(self, event: _Event) -> bool:    # game_window.nml:72
        """``pause_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.glass = Glass(parent=self)    # game_window.nml:33
        self.info = GameInfo(parent=self)    # game_window.nml:40
        self.new_button = Button(parent=self)    # game_window.nml:47
        self.setup_button = Button(parent=self)    # game_window.nml:55
        self.top_button = Button(parent=self)    # game_window.nml:63
        self.pause_button = Button(parent=self)    # game_window.nml:71

        self.title = "Navigator's game"    # game_window.nml:16
        self.zoomable = False    # game_window.nml:17
        self.resizable = False    # game_window.nml:18

        self.glass.x = 1    # game_window.nml:35
        self.glass.y = 1    # game_window.nml:36
        self.glass.width = 26    # game_window.nml:37
        self.glass.height = 21    # game_window.nml:38

        self.info.x = 28    # game_window.nml:42
        self.info.y = 1    # game_window.nml:43
        self.info.width = 23    # game_window.nml:44
        self.info.height = 15    # game_window.nml:45

        self.new_button.text = '~N~ew'    # game_window.nml:49
        self.new_button.x = 28    # game_window.nml:50
        self.new_button.y = 17    # game_window.nml:51
        self.new_button.width = 11    # game_window.nml:52
        self.new_button.height = 2    # game_window.nml:53
        self.new_button.on_click = self.on_new_button_click    # game_window.nml:48

        self.setup_button.text = '~S~etup'    # game_window.nml:57
        self.setup_button.x = 39    # game_window.nml:58
        self.setup_button.y = 17    # game_window.nml:59
        self.setup_button.width = 11    # game_window.nml:60
        self.setup_button.height = 2    # game_window.nml:61
        self.setup_button.on_click = self.on_setup_button_click    # game_window.nml:56

        self.top_button.text = '~T~op 10'    # game_window.nml:65
        self.top_button.x = 28    # game_window.nml:66
        self.top_button.y = 19    # game_window.nml:67
        self.top_button.width = 11    # game_window.nml:68
        self.top_button.height = 2    # game_window.nml:69
        self.top_button.on_click = self.on_top_button_click    # game_window.nml:64

        self.pause_button.text = '~P~ause'    # game_window.nml:73
        self.pause_button.x = 39    # game_window.nml:74
        self.pause_button.y = 19    # game_window.nml:75
        self.pause_button.width = 11    # game_window.nml:76
        self.pause_button.height = 2    # game_window.nml:77
        self.pause_button.on_click = self.on_pause_button_click    # game_window.nml:72
