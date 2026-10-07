"""The game's behaviour: the clock it falls by, its buttons and keys, the end
of a game, and the Top Ten (:mod:`navigator.tetris` has the rules)."""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator import tetris
from navigator.settings import SETTINGS
from navigator.widgets.game.commands import GameSetup, LevelUp, NewGame, PauseGame, ShowTopTen, TogglePreview

#: The window's size: ``TGameWindow``'s, which fits an 80 by 25 screen's
#: desktop exactly.
WIDTH, HEIGHT = 53, 22
#: How often the clock looks: a hundredth of DN's ``Update`` is too fine to matter.
TICK = 0.05


class GameWindow(Window):
    """*Navigator's game*: Tetris or Pentix, as *Setup game* says."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        setup = SETTINGS.tetris
        self.game = tetris.Game(start_level=max(1, min(10, setup.level)), pentix=setup.style == "pentix",
                                preview=setup.preview)
        self.glass.game = self.info.game = self.game
        self._clock: Any = None
        self._asking = False
        #: Whether the keyboard has been here: the pause is for losing it.
        self._held = False
        self._show_best()

    @property
    def style_name(self) -> str:
        return "pentix" if self.game.pentix else "tetris"

    def mounted(self) -> None:
        super().mounted()
        effect(self, GameWindow._pause_when_left)
        app = self.application
        if app is not None and self._clock is None:
            self._clock = app.call_every(TICK, self._tick)

    def unmounting(self) -> None:
        if self._clock is not None:
            self._clock.cancel()
            self._clock = None
        super().unmounting()

    def _pause_when_left(self) -> None:
        """``SetState``: the game stops whenever the window loses the keyboard
        -- having had it: it is mounted before it is given it."""
        held = self.focus_within
        if held:
            self._held = True
        elif self._held and not self.game.stopped:
            self.game.stopped = True
            self.invalidate()

    async def _tick(self) -> None:
        game = self.game
        if game.tick(round(TICK * 100)):
            self.glass.invalidate()
            self.info.invalidate()
            if game.over and not self._asking:
                self.spawn(self._game_over())

    def _show_best(self) -> None:
        best = tetris.top_ten(self.style_name)
        self.info.best = (best[0].name, best[0].score) if best else (tetris.ANONYMOUS, 0)
        self.info.invalidate()

    def _redraw(self) -> None:
        self.glass.invalidate()
        self.info.invalidate()

    # -- the end of a game ------------------------------------------------------------

    async def _game_over(self) -> None:
        """*Game over*, the final score, and -- one good enough -- a name for
        the Top Ten (``dlgTetrisWinner``) and the Top Ten with it bright."""
        from navigator.widgets.game.winner_dialog import WinnerDialog

        app = self.application
        game = self.game
        self._asking = True
        try:
            await Dialog(title="Information", prompt=f"Game over\n\nFinal score - {game.score}",
                         buttons="ok").execute(app)
            place = tetris.place_for(self.style_name, game.score)
            if place is None:
                return
            name = await WinnerDialog().execute(app)
            tetris.enter(self.style_name, name if name is not None else tetris.ANONYMOUS,
                         game.start_level, game.level, game.score)
            self._show_best()
            await self.show_scores(place)
        finally:
            self._asking = False

    async def show_scores(self, highlight: int | None = None) -> None:
        """F4, *Top 10*: ``ShowScores``, the game held while it is up."""
        from navigator.widgets.game.top_ten_dialog import TopTenDialog

        game = self.game
        was = game.stopped
        game.stopped = True
        try:
            await TopTenDialog(game_style=self.style_name, highlight=highlight).execute(self.application)
        finally:
            game.stopped = was or game.over
            self.glass.focus()

    async def setup(self) -> None:
        """F5, *Setup*: ``dlgGameSetup``, a new game in what it says, and the
        answer kept (``cmUpdateConfig``)."""
        import contextlib

        from navigator.widgets.game.game_setup_dialog import GameSetupDialog

        game = self.game
        game.stopped = True
        answer = await GameSetupDialog(level=game.level).execute(self.application)
        self.glass.focus()
        if answer is None:
            return
        SETTINGS.tetris.update(answer)
        with contextlib.suppress(OSError):
            SETTINGS.save(section="tetris")
        game.start_level, game.pentix, game.preview = answer["level"], answer["style"] == "pentix", answer["preview"]
        game.new_game()
        self._show_best()
        self._redraw()

    # -- the buttons and the keys -----------------------------------------------------

    async def on_new_game(self, event: NewGame) -> bool:
        self.game.new_game()
        self.glass.focus()
        self._redraw()
        return True

    async def on_pause_game(self, event: PauseGame) -> bool:
        self.game.pause()
        self.glass.focus()
        self._redraw()
        return True

    async def on_show_top_ten(self, event: ShowTopTen) -> bool:
        self.spawn(self.show_scores())
        return True

    async def on_game_setup(self, event: GameSetup) -> bool:
        self.spawn(self.setup())
        return True

    async def on_level_up(self, event: LevelUp) -> bool:
        self.game.level_up()
        self._redraw()
        return True

    async def on_toggle_preview(self, event: TogglePreview) -> bool:
        self.game.preview = not self.game.preview
        self._redraw()
        return True

    async def on_new_button_click(self, event: Event) -> bool:
        return await self.on_new_game(NewGame())

    async def on_setup_button_click(self, event: Event) -> bool:
        return await self.on_game_setup(GameSetup())

    async def on_top_button_click(self, event: Event) -> bool:
        return await self.on_show_top_ten(ShowTopTen())

    async def on_pause_button_click(self, event: Event) -> bool:
        return await self.on_pause_game(PauseGame())
